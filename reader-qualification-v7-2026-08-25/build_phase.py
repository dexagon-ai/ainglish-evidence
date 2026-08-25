#!/usr/bin/env python3
"""Freeze one v7 tranche after its source and wrapper digests exist locally."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import urllib.request


ROOT = Path(__file__).resolve().parent
PHASES = ("phase-a", "reserve-b", "final-reserve")
SPEC_FILES = {
    "phase-a": "phase-a-holdout.json",
    "reserve-b": "reserve-b-holdout.json",
    "final-reserve": "final-reserve-holdout.json",
}
RESULT_FILES = {
    "phase-a": "phase-a-result.json",
    "reserve-b": "reserve-b-result.json",
    "final-reserve": "final-reserve-result.json",
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    sealed = dict(value)
    expected = sealed.pop("content_sha256")
    if hashlib.sha256(canonical(sealed)).hexdigest() != expected:
        raise SystemExit(f"REFUSING: digest drift in {path.name}")
    return value


def get_json(path: str) -> dict:
    with urllib.request.urlopen("http://127.0.0.1:11434" + path, timeout=30) as response:
        return json.load(response)


def post_json(path: str, payload: dict) -> dict:
    request = urllib.request.Request(
        "http://127.0.0.1:11434" + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def prior_results(phase: str) -> list[tuple[Path, dict]]:
    index = PHASES.index(phase)
    out = []
    for earlier in PHASES[:index]:
        path = ROOT / RESULT_FILES[earlier]
        if not path.exists():
            raise SystemExit(f"REFUSING: {path.name} is required before {phase}")
        out.append((path, checked(path)))
    return out


def accumulated_qualified(results: list[tuple[Path, dict]]) -> list[dict]:
    out = []
    seen = set()
    for _path, result in results:
        for reader in result.get("fixed_roster", []):
            if reader["name"] in seen:
                raise SystemExit("REFUSING: a reader appears in more than one prior tranche")
            seen.add(reader["name"])
            out.append(reader)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", required=True, choices=PHASES)
    args = parser.parse_args()
    if (ROOT / "preflight-abort.json").exists():
        raise SystemExit("REFUSING: v7 was permanently aborted before inference")
    plan = checked(ROOT / "plan.json")
    target = ROOT / SPEC_FILES[args.phase]
    if target.exists():
        raise SystemExit(f"REFUSING: {target.name} already exists")
    sources = prior_results(args.phase)
    prior_roster = accumulated_qualified(sources)
    if len({row["lineage"] for row in prior_roster}) >= plan["selection_rule"]["minimum_distinct_qualified_lineages"]:
        raise SystemExit("REFUSING: the accumulated roster is already ready; later-tranche spend is unnecessary")
    if get_json("/api/ps").get("models"):
        raise SystemExit("REFUSING: Ollama has a resident model before phase freeze")
    tags = {row["name"]: row["digest"] for row in get_json("/api/tags").get("models", [])}
    panel = []
    for candidate in plan["candidate_tranches"][args.phase]:
        if tags.get(candidate["source_model"]) != candidate["source_manifest_sha256"]:
            raise SystemExit(f"REFUSING: source tag absent or drifted for {candidate['source_model']}")
        source_shown = post_json("/api/show", {"model": candidate["source_model"]})
        source_capabilities = source_shown.get("capabilities")
        if not isinstance(source_capabilities, list) or "completion" not in source_capabilities or "thinking" in source_capabilities:
            raise SystemExit(f"REFUSING: incompatible source capabilities for {candidate['source_model']}: {source_capabilities}")
        wrapper_digest = tags.get(candidate["wrapper_model"])
        if not wrapper_digest:
            raise SystemExit(f"REFUSING: wrapper {candidate['wrapper_model']} is not installed")
        shown = post_json("/api/show", {"model": candidate["wrapper_model"]})
        wrapper_capabilities = shown.get("capabilities")
        if not isinstance(wrapper_capabilities, list) or "completion" not in wrapper_capabilities or "thinking" in wrapper_capabilities:
            raise SystemExit(f"REFUSING: incompatible wrapper capabilities for {candidate['wrapper_model']}: {wrapper_capabilities}")
        modelfile = str(shown.get("modelfile", ""))
        if candidate["model_blob_sha256"] not in modelfile.replace("sha256-", ""):
            raise SystemExit(f"REFUSING: wrapper base blob drift for {candidate['wrapper_model']}")
        if "Return only the requested opaque choice code" not in modelfile:
            raise SystemExit(f"REFUSING: wrapper system instruction drift for {candidate['wrapper_model']}")
        transport = plan["transport"]
        panel.append({
            **candidate,
            "provider": "ollama",
            "model": candidate["wrapper_model"],
            "model_digest": f"sha256:{wrapper_digest}",
            "source_capabilities": source_capabilities,
            "wrapper_capabilities": wrapper_capabilities,
            "max_tokens": transport["max_tokens"],
            "timeout_s": transport["timeout_s"],
            "temperature": transport["temperature"],
            "seed": transport["seed"],
            "num_ctx": transport["num_ctx"],
        })
    source_receipts = [
        {"file": path.name, "content_sha256": result["content_sha256"]}
        for path, result in sources
    ]
    spec = {
        "kind": f"ainglish.panel.reader-qualification-holdout.v7-{args.phase}",
        "result_kind": f"ainglish.panel.reader-qualification-holdout-result.v7-{args.phase}",
        "evidentiary_status": plan["evidentiary_status"],
        "plan_sha256": plan["content_sha256"],
        "phase": args.phase,
        "trigger": "initial tranche" if args.phase == "phase-a" else "accumulated published results contain fewer than two qualified lineages",
        "source_results": source_receipts,
        "prior_qualified_readers": prior_roster,
        "answer_protocol": plan["answer_protocol"],
        "transport": plan["transport"],
        "axes": plan["axes"],
        "items_per_axis": plan["items_per_axis"],
        "forbidden_construct_terms": plan["forbidden_construct_terms"],
        "disjoint_from_specs": plan["disjoint_from_specs"],
        "gpu_gate": plan["gpu_gate"],
        "selection_rule": plan["selection_rule"],
        "panel": panel,
        "items": plan["items"],
    }
    spec["content_sha256"] = hashlib.sha256(canonical(spec)).hexdigest()
    with target.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(spec, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({
        "phase": args.phase,
        "items": len(spec["items"]),
        "models": len(panel),
        "reader_calls": 0,
        "source_results": source_receipts,
        "sha256": spec["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
