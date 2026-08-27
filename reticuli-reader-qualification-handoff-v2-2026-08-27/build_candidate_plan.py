#!/usr/bin/env python3
"""Freeze Reticuli's prospectively selected candidate before any model call."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import urllib.request


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
ENDPOINT = "http://127.0.0.1:11434"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    sealed = dict(value)
    expected = sealed.pop("content_sha256")
    if hashlib.sha256(canonical(sealed)).hexdigest() != expected:
        raise SystemExit(f"REFUSING: digest drift in {path}")
    return value


def get(path: str) -> dict:
    with urllib.request.urlopen(ENDPOINT + path, timeout=30) as response:
        return json.load(response)


def post(path: str, payload: dict) -> dict:
    request = urllib.request.Request(
        ENDPOINT + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def build(source_model: str, phase: str) -> dict:
    research = checked(ROOT / "research.json")
    candidate = next((row for row in research["candidates"] if row["source_model"] == source_model), None)
    if candidate is None or not candidate["selected"]:
        raise SystemExit("REFUSING: source model is not a selected research candidate")
    format_plan = checked(REPO / "reader-format-structured-v1-2026-08-26" / "plan.json")
    semantic_packet = checked(REPO / "reader-qualification-calibration-v1-2026-08-26" / "development-packet.json")
    runtime = get("/api/version").get("version")
    minimum_runtime = research["resource_envelope"]["minimum_ollama_version"]
    def version_tuple(value: str) -> tuple[int, ...]:
        try:
            return tuple(int(part) for part in value.split("."))
        except (AttributeError, ValueError) as exc:
            raise SystemExit(f"REFUSING: invalid Ollama version {value!r}") from exc
    if version_tuple(runtime) < version_tuple(minimum_runtime):
        raise SystemExit(f"REFUSING: Ollama {runtime} predates required {minimum_runtime}")
    tags = {row["name"]: row for row in get("/api/tags").get("models", [])}
    tag = tags.get(source_model)
    if tag is None:
        raise SystemExit(f"REFUSING: candidate is not locally acquired: {source_model}")
    if not tag["digest"].startswith(candidate["registry_digest_prefix"]):
        raise SystemExit("REFUSING: acquired tag no longer matches the prospectively recorded registry digest prefix")
    shown = post("/api/show", {"model": source_model})
    capabilities = shown.get("capabilities") or []
    if "thinking" in capabilities:
        raise SystemExit(f"REFUSING: candidate advertises thinking: {source_model}")
    details = shown.get("details") or {}
    schema = {
        "type": "object",
        "properties": {"answer": {"type": "string", "enum": ["A", "B", "C"]}},
        "required": ["answer"],
        "additionalProperties": False,
    }
    document = {
        "kind": "ainglish.panel.reticuli-reader-development-plan.v2",
        "result_kind": "ainglish.panel.reticuli-reader-development-result.v2",
        "evidentiary_status": "reader development only; never qualification or proposal evidence",
        "phase": phase,
        "freeze_rule": "Commit and push this exact candidate manifest, gates, format controls, semantic packet receipt, and prompt before the first model call.",
        "research": {"file": "research.json", "content_sha256": research["content_sha256"]},
        "candidate": {
            "lineage": candidate["lineage"],
            "producer": candidate["producer"],
            "source_model": source_model,
            "source_manifest_sha256": tag["digest"],
            "capabilities": capabilities,
            "details": {
                "family": details.get("family"),
                "families": details.get("families"),
                "parameter_size": details.get("parameter_size"),
                "quantization_level": details.get("quantization_level"),
                "format": details.get("format"),
            },
            "official_reference": candidate["official_reference"],
            "independence_caveat": candidate["independence_caveat"],
        },
        "runtime": {
            "ollama_version": runtime,
            "minimum_ollama_version": minimum_runtime,
            "structured_output_reference": "https://docs.ollama.com/capabilities/structured-outputs",
        },
        "format_stage": {
            "source_plan": {"file": "reader-format-structured-v1-2026-08-26/plan.json", "content_sha256": format_plan["content_sha256"]},
            "controls": format_plan["controls"],
            "gate": format_plan["compatibility_gate"],
            "failure_action": "Publish the format result and expose zero semantic development items.",
        },
        "semantic_stage": {
            "packet": {"file": "reader-qualification-calibration-v1-2026-08-26/development-packet.json", "content_sha256": semantic_packet["content_sha256"]},
            "prompt_contract": "Given only the ordinary-English premise, classify the hypothesis as entailed, contradicted, or not determined. Return the opaque choice code selected from the supplied mapping.",
            "gate": {
                "valid_json_cells_required": 24,
                "schema_exact_cells_required": 24,
                "correct_cells_required": 22,
                "correct_per_axis_required": 2,
                "correct_per_label_required": 7,
                "thinking_bytes_required": 0,
                "fault_cells_required": 0,
            },
            "pass_meaning": "Eligible only to enter a later fresh disjoint v8 holdout; never qualified by this exposed packet.",
        },
        "transport": {
            "adapter": "ollama-native-chat-json-schema-v1",
            "think": False,
            "temperature": 0,
            "seed": 2026082629,
            "num_ctx": 4096,
            "max_tokens": 16,
            "timeout_s": 600,
            "format": schema,
        },
        "gpu_gate": {"ollama_base_url": ENDPOINT, **research["resource_envelope"]["execution_gpu_gate"]},
        "result_file": f"{phase}-result.json",
        "journal_file": f"{phase}-attempt-journal.jsonl",
    }
    document["content_sha256"] = hashlib.sha256(canonical(document)).hexdigest()
    return document


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-model", required=True)
    parser.add_argument("--phase", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    document = build(args.source_model, args.phase)
    target = ROOT / args.output
    if args.write:
        if target.exists():
            raise SystemExit(f"REFUSING: {target.name} already exists")
        target.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"candidate": document["candidate"], "sha256": document["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
