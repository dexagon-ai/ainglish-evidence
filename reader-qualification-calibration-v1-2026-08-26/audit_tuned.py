#!/usr/bin/env python3
"""Offline audit of the frozen tuned-development plan and optional result."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from analyze import canonical, checked
from analyze_tuned import build as build_tuned_analysis
from build_tuned_plan import build


ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    plan = checked(ROOT / "tuned-run-plan.json")
    packet = checked(ROOT / plan["packet"]["file"])
    if plan != build():
        raise SystemExit("REFUSING: tuned run-plan drift")
    report = {
        "kind": "ainglish.panel.reader-qualification-development-tuned-audit.v1",
        "model_calls": 0,
        "network_calls": 0,
        "tuned_run_plan_sha256": plan["content_sha256"],
        "development_result": None,
        "development_passes": [],
        "v8_authoring_ready": False,
        "status": "passed-static",
    }
    result_path = ROOT / "development-tuned-result.json"
    if result_path.exists():
        result = checked(result_path)
        if result["plan_sha256"] != plan["content_sha256"] or result["packet_sha256"] != packet["content_sha256"]:
            raise SystemExit("REFUSING: tuned result binding drift")
        expected_cells = len(plan["panel"]) * len(packet["items"])
        identities = {(row["reader"], row["item_id"]) for row in result["rows"]}
        if len(result["rows"]) != expected_cells or len(identities) != expected_cells:
            raise SystemExit("REFUSING: tuned result cell population drift")
        journal = ROOT / result["attempt_journal"]["file"]
        if hashlib.sha256(journal.read_bytes()).hexdigest() != result["attempt_journal"]["sha256"]:
            raise SystemExit("REFUSING: tuned attempt-journal drift")
        gate = plan["development_gate"]
        passed = []
        for reader in plan["panel"]:
            own = [row for row in result["rows"] if row["reader"] == reader["name"]]
            observed = {
                "exact_code_cells": sum(row["exact_code"] for row in own),
                "correct_cells": sum(row["correct"] for row in own),
                "correct_by_axis": {
                    axis: sum(row["correct"] for row in own if row["axis"] == axis)
                    for axis in packet["axes"]
                },
                "correct_by_label": {
                    label: sum(row["correct"] for row in own if row["expected"] == label)
                    for label in packet["labels"]
                },
                "thinking_bytes": sum(row["thinking_bytes"] for row in own),
                "fault_cells": sum(row["fault"] is not None for row in own),
            }
            if result["summaries"][reader["name"]] != observed:
                raise SystemExit(f"REFUSING: tuned summary drift for {reader['name']}")
            decision = (
                observed["exact_code_cells"] == gate["exact_code_cells_required"]
                and observed["correct_cells"] >= gate["correct_cells_required"]
                and all(value >= gate["correct_per_axis_required"] for value in observed["correct_by_axis"].values())
                and all(value >= gate["correct_per_label_required"] for value in observed["correct_by_label"].values())
                and observed["thinking_bytes"] == gate["thinking_bytes_required"]
                and observed["fault_cells"] == gate["fault_cells_required"]
            )
            if decision:
                passed.append({"name": reader["name"], "lineage": reader["lineage"]})
        report["development_result"] = {"file": result_path.name, "content_sha256": result["content_sha256"], "response_cells": len(result["rows"])}
        report["development_passes"] = passed
        report["v8_authoring_ready"] = len({row["lineage"] for row in passed}) >= 2
        tuned_analysis = checked(ROOT / "development-tuned-analysis.json")
        if tuned_analysis != build_tuned_analysis():
            raise SystemExit("REFUSING: tuned development analysis drift")
        if tuned_analysis["development_passes"] != passed or tuned_analysis["v8_authoring_ready"] != report["v8_authoring_ready"]:
            raise SystemExit("REFUSING: tuned development decision drift")
        report["development_tuned_analysis_sha256"] = tuned_analysis["content_sha256"]
        report["status"] = "passed-with-tuned-result"
    report["content_sha256"] = hashlib.sha256(canonical(report)).hexdigest()
    if args.write:
        target = ROOT / "tuned-audit-report.json"
        if target.exists():
            raise SystemExit("REFUSING: tuned-audit-report.json already exists")
        target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
