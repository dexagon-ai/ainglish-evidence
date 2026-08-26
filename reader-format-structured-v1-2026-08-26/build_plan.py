#!/usr/bin/env python3
"""Freeze a format-only structured-output compatibility screen."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "reader-qualification-v7-2026-08-25"
SOURCE_SPECS = ("phase-a-holdout.json", "reserve-b-holdout.json", "final-reserve-holdout.json")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    sealed = dict(value)
    expected = sealed.pop("content_sha256")
    if hashlib.sha256(canonical(sealed)).hexdigest() != expected:
        raise SystemExit(f"REFUSING: digest drift in {path}")
    return value


def build() -> dict:
    panel = []
    receipts = []
    keys = ("name", "lineage", "producer", "source_model", "source_manifest_sha256", "source_capabilities")
    for name in SOURCE_SPECS:
        spec = checked(SOURCE / name)
        receipts.append({"file": name, "content_sha256": spec["content_sha256"]})
        panel.extend({key: reader[key] for key in keys} for reader in spec["panel"])
    if len(panel) != 6 or len({row["lineage"] for row in panel}) != 6:
        raise SystemExit("REFUSING: expected six distinct v7 source readers")
    phrasings = (
        "Store target code {target} in the answer field.",
        "The required answer value is {target}.",
        "Copy {target} into the answer property.",
        "Return the supplied target, which is {target}.",
    )
    controls = []
    ordinal = 0
    for round_index, phrase in enumerate(phrasings, 1):
        for target in "ABC":
            ordinal += 1
            controls.append({
                "id": f"format-{ordinal:02d}",
                "round": round_index,
                "target": target,
                "instruction": phrase.format(target=target),
            })
    schema = {
        "type": "object",
        "properties": {"answer": {"type": "string", "enum": ["A", "B", "C"]}},
        "required": ["answer"],
        "additionalProperties": False,
    }
    document = {
        "kind": "ainglish.panel.reader-format-structured-plan.v1",
        "result_kind": "ainglish.panel.reader-format-structured-result.v1",
        "evidentiary_status": "format-only development diagnostic; never reader qualification or proposal evidence",
        "freeze_rule": "Commit and push this exact plan before the first model call; attempt each reader-control cell once and retain every outcome.",
        "separation_rule": "Every target code is explicitly supplied. No semantic premise, hypothesis, answer key, or proposal construct appears in this screen.",
        "source_directory": SOURCE.name,
        "source_reader_specs": receipts,
        "runtime": {
            "ollama_version": "0.32.7",
            "official_structured_output_reference": "https://docs.ollama.com/capabilities/structured-outputs",
        },
        "transport": {
            "adapter": "ollama-native-chat-json-schema-v1",
            "think": False,
            "temperature": 0,
            "seed": 2026082623,
            "num_ctx": 4096,
            "max_tokens": 16,
            "timeout_s": 300,
            "format": schema,
        },
        "gpu_gate": {
            "ollama_base_url": "http://127.0.0.1:11434",
            "minimum_total_free_mib": 36000,
            "maximum_utilization_percent": 35,
        },
        "compatibility_gate": {
            "valid_json_cells_required": 12,
            "schema_exact_cells_required": 12,
            "target_correct_cells_required": 12,
            "thinking_bytes_required": 0,
            "fault_cells_required": 0,
        },
        "panel": panel,
        "controls": controls,
    }
    document["content_sha256"] = hashlib.sha256(canonical(document)).hexdigest()
    return document


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    document = build()
    target = ROOT / "plan.json"
    if args.write:
        if target.exists():
            raise SystemExit("REFUSING: plan.json already exists")
        target.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"readers": len(document["panel"]), "controls": len(document["controls"]), "sha256": document["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
