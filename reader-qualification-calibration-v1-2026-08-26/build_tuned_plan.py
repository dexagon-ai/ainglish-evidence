#!/usr/bin/env python3
"""Freeze the one allowed generic prompt clarification over exposed controls."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from analyze import canonical, checked


ROOT = Path(__file__).resolve().parent


def build() -> dict:
    base = checked(ROOT / "run-plan.json")
    packet = checked(ROOT / "development-packet.json")
    result = checked(ROOT / "development-result.json")
    analysis = checked(ROOT / "development-analysis.json")
    if result["plan_sha256"] != base["content_sha256"] or analysis["source_receipts"]["development_result_sha256"] != result["content_sha256"]:
        raise SystemExit("REFUSING: initial development chain drift")
    document = {
        "kind": "ainglish.panel.reader-qualification-development-tuned-run-plan.v1",
        "result_kind": "ainglish.panel.reader-qualification-development-tuned-result.v1",
        "evidentiary_status": "development-only deliberate reuse; never qualification or proposal evidence",
        "freeze_rule": "Commit and push this plan before the first tuned model call. Attempt every reader-item cell at most once and retain every outcome.",
        "base_receipts": {
            "run_plan_sha256": base["content_sha256"],
            "development_result_sha256": result["content_sha256"],
            "development_analysis_sha256": analysis["content_sha256"],
        },
        "reuse_statement": "The exact exposed 24-item packet is deliberately reused to test one generic instruction revision. These cells can never qualify a reader.",
        "change_control": "The user-prompt instruction is the only intentional execution change. Reader wrappers, model digests, item order, options, temperature, seed, context, output bound, and GPU gate are unchanged.",
        "packet": {"file": "development-packet.json", "content_sha256": packet["content_sha256"]},
        "source_directory": base["source_directory"],
        "source_reader_specs": base["source_reader_specs"],
        "transport": base["transport"],
        "gpu_gate": base["gpu_gate"],
        "panel": base["panel"],
        "prompt_contract": (
            "Classify only what logically follows from the premise. ENTAILED means the hypothesis "
            "must be true in every situation consistent with the premise. CONTRADICTED means the "
            "hypothesis must be false in every situation consistent with the premise. NOT DETERMINED "
            "means the premise permits at least one situation where the hypothesis is true and at "
            "least one where it is false. Do not add likely background assumptions or choose the most "
            "plausible completion. If a reference or inference admits multiple premise-consistent "
            "possibilities, choose NOT DETERMINED."
        ),
        "development_gate": {
            "exact_code_cells_required": 24,
            "correct_cells_required": 22,
            "correct_per_axis_required": 2,
            "correct_per_label_required": 7,
            "thinking_bytes_required": 0,
            "fault_cells_required": 0,
        },
        "v8_authoring_gate": "At least two distinct reader lineages must pass the frozen development gate before authoring a fresh, disjoint v8 holdout.",
    }
    document["content_sha256"] = hashlib.sha256(canonical(document)).hexdigest()
    return document


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    document = build()
    target = ROOT / "tuned-run-plan.json"
    if args.write:
        if target.exists():
            raise SystemExit("REFUSING: tuned-run-plan.json already exists")
        target.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"readers": len(document["panel"]), "sha256": document["content_sha256"], "gate": document["development_gate"]}, indent=2))


if __name__ == "__main__":
    main()
