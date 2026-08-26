#!/usr/bin/env python3
"""Freeze the v9 LFM2 prospective development plan before its first model call."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import urllib.request


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
ENDPOINT = "http://127.0.0.1:11434"
SOURCE_MODEL = "lfm2:24b"


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


def main() -> None:
    runtime = get("/api/version").get("version")
    if runtime != "0.32.7":
        raise SystemExit(f"REFUSING: Ollama version drift {runtime}")
    tags = {row["name"]: row for row in get("/api/tags").get("models", [])}
    tag = tags.get(SOURCE_MODEL)
    if tag is None:
        raise SystemExit(f"REFUSING: missing installed candidate {SOURCE_MODEL}")
    shown = post("/api/show", {"model": SOURCE_MODEL})
    capabilities = shown.get("capabilities") or []
    if "thinking" in capabilities:
        raise SystemExit(f"REFUSING: thinking capability on {SOURCE_MODEL}")
    details = shown.get("details") or {}
    format_plan = checked(REPO / "reader-format-structured-v1-2026-08-26" / "plan.json")
    packet = checked(REPO / "reader-qualification-calibration-v1-2026-08-26" / "development-packet.json")
    schema = {
        "type": "object",
        "properties": {"answer": {"type": "string", "enum": ["A", "B", "C"]}},
        "required": ["answer"],
        "additionalProperties": False,
    }
    plan = {
        "kind": "ainglish.panel.reader-v9-development-plan.v1",
        "result_kind": "ainglish.panel.reader-v9-development-result.v1",
        "evidentiary_status": "reader development only; never qualification or proposal evidence",
        "phase": "development-lfm2",
        "freeze_rule": "Commit and push this exact plan before the first candidate call; never tune or retry after observation.",
        "candidate": {
            "lineage": "LFM2 24B-A2B",
            "producer": "Liquid AI",
            "source_model": SOURCE_MODEL,
            "source_manifest_sha256": tag["digest"],
            "capabilities": capabilities,
            "details": {
                "family": details.get("family"),
                "families": details.get("families"),
                "parameter_size": details.get("parameter_size"),
                "quantization_level": details.get("quantization_level"),
                "format": details.get("format"),
            },
            "official_reference": "https://ollama.com/library/lfm2",
            "independence_caveat": "Distinct Liquid hybrid family from Qwen; local Ollama serving and the qualification harness remain shared infrastructure.",
        },
        "runtime": {
            "ollama_version": runtime,
            "structured_output_reference": "https://docs.ollama.com/capabilities/structured-outputs",
        },
        "format_stage": {
            "source_plan": {
                "file": "reader-format-structured-v1-2026-08-26/plan.json",
                "content_sha256": format_plan["content_sha256"],
            },
            "controls": format_plan["controls"],
            "gate": format_plan["compatibility_gate"],
            "failure_action": "Publish the format result and expose zero semantic development items.",
        },
        "semantic_stage": {
            "packet": {
                "file": "reader-qualification-calibration-v1-2026-08-26/development-packet.json",
                "content_sha256": packet["content_sha256"],
            },
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
            "pass_meaning": "Eligible only for a later fresh disjoint holdout; never qualified by this exposed packet.",
        },
        "transport": {
            "adapter": "ollama-native-chat-json-schema-v1",
            "think": False,
            "temperature": 0,
            "seed": 2026082641,
            "num_ctx": 4096,
            "max_tokens": 16,
            "timeout_s": 600,
            "format": schema,
        },
        "gpu_gate": {
            "ollama_base_url": ENDPOINT,
            "minimum_total_free_mib": 36000,
            "maximum_utilization_percent": 35,
        },
        "result_file": "development-lfm2-result.json",
        "journal_file": "development-lfm2-attempt-journal.jsonl",
    }
    plan["content_sha256"] = hashlib.sha256(canonical(plan)).hexdigest()
    target = ROOT / "development-lfm2-plan.json"
    if target.exists():
        if checked(target) != plan:
            raise SystemExit("REFUSING: frozen plan drift")
    else:
        target.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    index = {
        "kind": "ainglish.panel.reader-v9-development-index.v1",
        "runner": "reader-qualification-v9-2026-08-26/run_candidate_once.py",
        "auditor": "reader-qualification-v9-2026-08-26/audit_candidate.py",
        "plans": [{
            "file": target.name,
            "lineage": plan["candidate"]["lineage"],
            "content_sha256": plan["content_sha256"],
        }],
        "fresh_holdout_authoring_gate": "LFM2 passes every development gate; later LFM2 and Qwen holdout plans are both frozen before either call",
        "model_calls": 0,
    }
    index["content_sha256"] = hashlib.sha256(canonical(index)).hexdigest()
    index_path = ROOT / "index.json"
    if index_path.exists():
        if checked(index_path) != index:
            raise SystemExit("REFUSING: frozen index drift")
    else:
        index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(index, indent=2))


if __name__ == "__main__":
    main()
