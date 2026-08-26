#!/usr/bin/env python3
"""Compare the initial and sole tuned exposed-control runs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from analyze import canonical, checked


ROOT = Path(__file__).resolve().parent


def totals(result: dict, labels: list[str]) -> dict:
    return {
        "correct_cells": sum(row["correct"] for row in result["rows"]),
        "exact_code_cells": sum(row["exact_code"] for row in result["rows"]),
        "thinking_bytes": sum(row["thinking_bytes"] for row in result["rows"]),
        "fault_cells": sum(row["fault"] is not None for row in result["rows"]),
        "correct_by_label": {
            label: sum(row["correct"] for row in result["rows"] if row["expected"] == label)
            for label in labels
        },
    }


def build() -> dict:
    base_plan = checked(ROOT / "run-plan.json")
    tuned_plan = checked(ROOT / "tuned-run-plan.json")
    packet = checked(ROOT / "development-packet.json")
    initial = checked(ROOT / "development-result.json")
    tuned = checked(ROOT / "development-tuned-result.json")
    if initial["plan_sha256"] != base_plan["content_sha256"]:
        raise SystemExit("REFUSING: initial run binding drift")
    if tuned["plan_sha256"] != tuned_plan["content_sha256"] or tuned["packet_sha256"] != packet["content_sha256"]:
        raise SystemExit("REFUSING: tuned run binding drift")
    initial_by_cell = {(row["reader"], row["item_id"]): row for row in initial["rows"]}
    tuned_by_cell = {(row["reader"], row["item_id"]): row for row in tuned["rows"]}
    if set(initial_by_cell) != set(tuned_by_cell):
        raise SystemExit("REFUSING: initial and tuned cell populations differ")
    gate = tuned_plan["development_gate"]
    readers = []
    passes = []
    for reader in tuned_plan["panel"]:
        name = reader["name"]
        before = initial["summaries"][name]
        after = tuned["summaries"][name]
        fixed = sum(not initial_by_cell[key]["correct"] and tuned_by_cell[key]["correct"] for key in initial_by_cell if key[0] == name)
        regressed = sum(initial_by_cell[key]["correct"] and not tuned_by_cell[key]["correct"] for key in initial_by_cell if key[0] == name)
        passed = (
            after["exact_code_cells"] == gate["exact_code_cells_required"]
            and after["correct_cells"] >= gate["correct_cells_required"]
            and all(value >= gate["correct_per_axis_required"] for value in after["correct_by_axis"].values())
            and all(value >= gate["correct_per_label_required"] for value in after["correct_by_label"].values())
            and after["thinking_bytes"] == gate["thinking_bytes_required"]
            and after["fault_cells"] == gate["fault_cells_required"]
        )
        readers.append({
            "reader": name,
            "lineage": reader["lineage"],
            "initial_correct": before["correct_cells"],
            "tuned_correct": after["correct_cells"],
            "correct_delta": after["correct_cells"] - before["correct_cells"],
            "initial_exact_codes": before["exact_code_cells"],
            "tuned_exact_codes": after["exact_code_cells"],
            "fixed_cells": fixed,
            "regressed_cells": regressed,
            "tuned_correct_by_label": after["correct_by_label"],
            "development_passed": passed,
        })
        if passed:
            passes.append({"name": name, "lineage": reader["lineage"]})
    initial_totals = totals(initial, packet["labels"])
    tuned_totals = totals(tuned, packet["labels"])
    malformed = [
        {"reader": row["reader"], "item_id": row["item_id"], "raw_output": row["raw_output"]}
        for row in tuned["rows"] if not row["exact_code"]
    ]
    report = {
        "kind": "ainglish.panel.reader-qualification-development-tuned-analysis.v1",
        "evidentiary_status": "development-only deliberate-reuse diagnosis; never qualification or proposal evidence",
        "model_calls": 0,
        "network_calls": 0,
        "source_receipts": {
            "initial_plan_sha256": base_plan["content_sha256"],
            "tuned_plan_sha256": tuned_plan["content_sha256"],
            "packet_sha256": packet["content_sha256"],
            "initial_result_sha256": initial["content_sha256"],
            "tuned_result_sha256": tuned["content_sha256"],
        },
        "initial": initial_totals,
        "tuned": tuned_totals,
        "delta": {
            "correct_cells": tuned_totals["correct_cells"] - initial_totals["correct_cells"],
            "exact_code_cells": tuned_totals["exact_code_cells"] - initial_totals["exact_code_cells"],
            "correct_by_label": {
                label: tuned_totals["correct_by_label"][label] - initial_totals["correct_by_label"][label]
                for label in packet["labels"]
            },
        },
        "readers": readers,
        "tuned_malformed_outputs": malformed,
        "development_passes": passes,
        "v8_authoring_ready": len({row["lineage"] for row in passes}) >= 2,
        "conclusion": [
            "The clarification increased not-determined accuracy by seven cells but reduced total accuracy by five cells.",
            "Exact-format compliance fell by eight cells; several readers returned a code plus its label or a truncated label despite the unchanged four-token bound.",
            "No reader met every prospectively frozen development gate, so no fresh v8 qualification holdout should be authored from this branch.",
            "The current six-reader no-thinking pool remains unsuitable for a high-threshold scientific comprehension roster.",
        ],
        "next_work": [
            "Keep the single native wording-review item open; it affects only future item design.",
            "Treat constrained output formatting and semantic uncertainty discrimination as separate development problems.",
            "Before further GPU spend, identify genuinely stronger, previously untested reader lineages or a prospectively frozen constrained-decoding transport; do not repeatedly tune these exposed controls.",
        ],
    }
    report["content_sha256"] = hashlib.sha256(canonical(report)).hexdigest()
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    report = build()
    target = ROOT / "development-tuned-analysis.json"
    if args.write:
        if target.exists():
            raise SystemExit("REFUSING: development-tuned-analysis.json already exists")
        target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "initial": report["initial"], "tuned": report["tuned"], "delta": report["delta"],
        "development_passes": report["development_passes"], "v8_authoring_ready": report["v8_authoring_ready"],
        "sha256": report["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
