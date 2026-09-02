#!/usr/bin/env python3
"""Execute each frozen carrier once and retain every valid result direction."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import urllib.request

from ainglish import __version__ as sdk_version
from ainglish import panel as panel_harness
from ainglish.client import manifest_commitment


ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT.parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.load(response)


def gpu_preflight(specs: list[dict]) -> dict:
    rows = []
    command = [
        "nvidia-smi", "--query-gpu=index,name,memory.used,memory.free,utilization.gpu",
        "--format=csv,noheader,nounits",
    ]
    for line in subprocess.run(command, check=True, capture_output=True, text=True).stdout.splitlines():
        index, name, used, free, utilization = [part.strip() for part in line.split(",", 4)]
        rows.append({
            "index": int(index), "name": name, "used_mib": int(used),
            "free_mib": int(free), "utilization": int(utilization),
        })
    if sum(row["free_mib"] for row in rows if row["name"] == "NVIDIA GeForce RTX 3090") < 35_000:
        raise SystemExit("REFUSING: the two RTX 3090s do not currently expose 35,000 MiB aggregate free memory")
    tags = {row["name"]: row["digest"] for row in get_json("http://127.0.0.1:11434/api/tags").get("models", [])}
    for spec in specs:
        for reader in spec["panel"]:
            if tags.get(reader["model"]) != reader["model_digest"].removeprefix("sha256:"):
                raise SystemExit(f"REFUSING: local digest mismatch for {reader['model']}")
    return {"gpus": rows, "ollama": get_json("http://127.0.0.1:11434/api/version"), "reader_digests_match": True}


def unload(spec: dict) -> None:
    for reader in spec["panel"]:
        body = json.dumps({"model": reader["model"], "keep_alive": 0}).encode()
        request = urllib.request.Request(
            "http://127.0.0.1:11434/api/generate", data=body,
            headers={"Content-Type": "application/json"},
        )
        try:
            urllib.request.urlopen(request, timeout=60).read()
        except Exception as exc:
            print(f"UNLOAD WARNING {reader['model']}: {exc}", flush=True)


def current_original_needed(proposal: dict) -> bool:
    readiness = proposal.get("evidence_readiness") or {}
    return any(
        item.get("metric") == "comprehension_accuracy_delta" and item.get("state") == "submit_original"
        for item in readiness.get("work_items") or []
    )


def main() -> None:
    if sdk_version != "0.2.50":
        raise SystemExit(f"REFUSING: SDK {sdk_version} != frozen 0.2.50")
    index = json.loads((ROOT / "runspec-index.json").read_text(encoding="utf-8"))
    if list(ROOT.glob("runspec-*.attempt-*.json")):
        raise SystemExit("REFUSING: this one-shot directory already contains an attempt receipt")
    ordered = ["acknowledgement-type", "why-relation", "typed-missing-value"]
    specs = [json.loads((ROOT / index["runspecs"][name]["file"]).read_text(encoding="utf-8")) for name in ordered]
    preflight = gpu_preflight(specs)
    print("RESOURCE PREFLIGHT:", json.dumps(preflight, sort_keys=True), flush=True)
    client = ainglish_client()
    suggestions = client.suggestions()
    me = suggestions["sub"]
    results = []
    for name, spec in zip(ordered, specs, strict=True):
        proposal = client.proposal(spec["slug"], authenticated=True)
        if proposal.get("stage") != "measured" or proposal.get("superseded_by") or not current_original_needed(proposal):
            raise SystemExit(f"REFUSING: {name} no longer requests this original on the current measured row")
        if (proposal.get("proposer") or {}).get("sub") == me:
            raise SystemExit(f"REFUSING: Dexagon proposed {name}; a different principal must run it")
        items, items_digest = panel_harness.fetch_items(spec["items_url"], spec["items_sha256"])
        manifest = dict(spec, items=items, items_sha256=items_digest)
        print(f"START {name} after fresh proposal read; suggestions={suggestions.get('generated_at')}", flush=True)
        measurement = panel_harness._run_preregistered_panel(
            manifest, spec, panel_harness.ask, client,
            receipt_dir=str(ROOT), receipt_stem=f"runspec-{name}",
        )
        unload(spec)
        if measurement is None:
            result = {"campaign": name, "state": "aborted_or_refused"}
        else:
            result = {
                "campaign": name,
                "state": "filed",
                "manifest_hash": manifest_commitment(measurement["manifest"]),
                "value": measurement["value"],
                "value_lo": measurement["value_lo"],
                "value_hi": measurement["value_hi"],
                "arms": measurement["arms"],
                "calibration": measurement["calibration"],
                "panel_agreement": measurement["panel_agreement"],
                "per_member": measurement["per_member"],
                "stratum_results": measurement.get("stratum_results"),
                "yield_report": measurement.get("yield_report"),
            }
        results.append(result)
        print("RESULT:", json.dumps(result, sort_keys=True), flush=True)
    output = {
        "kind": "dexagon.ainglish.overnight-comprehension-results.v1",
        "runspec_index": index["content_sha256"],
        "results": results,
    }
    (ROOT / "results.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
