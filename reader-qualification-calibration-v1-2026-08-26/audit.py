#!/usr/bin/env python3
"""Offline audit for the v7 diagnosis and development calibration."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from analyze import build_outputs, canonical, checked
from build_development import build as build_development
from build_run_plan import build as build_run_plan


ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    expected_analysis, expected_native = build_outputs()
    analysis = checked(ROOT / "analysis.json")
    native = checked(ROOT / "native-review-packet.json")
    development = checked(ROOT / "development-packet.json")
    run_plan = checked(ROOT / "run-plan.json")
    if analysis != expected_analysis or native != expected_native:
        raise SystemExit("REFUSING: derived diagnosis drift")
    if development != build_development(development["disjointness_receipts"]):
        raise SystemExit("REFUSING: development packet drift")
    if run_plan != build_run_plan():
        raise SystemExit("REFUSING: development run plan drift")
    report = {
        "kind": "ainglish.panel.reader-qualification-calibration-audit.v1",
        "model_calls": 0,
        "network_calls": 0,
        "analysis_sha256": analysis["content_sha256"],
        "native_review_packet_sha256": native["content_sha256"],
        "development_packet_sha256": development["content_sha256"],
        "run_plan_sha256": run_plan["content_sha256"],
        "development_result": None,
        "status": "passed-static",
    }
    result_path = ROOT / "development-result.json"
    if result_path.exists():
        result = checked(result_path)
        if result["plan_sha256"] != run_plan["content_sha256"] or result["packet_sha256"] != development["content_sha256"]:
            raise SystemExit("REFUSING: development result binding drift")
        expected_cells = len(run_plan["panel"]) * len(development["items"])
        identities = {(row["reader"], row["item_id"]) for row in result["rows"]}
        if len(result["rows"]) != expected_cells or len(identities) != expected_cells:
            raise SystemExit("REFUSING: development result cell population drift")
        journal = ROOT / result["attempt_journal"]["file"]
        if hashlib.sha256(journal.read_bytes()).hexdigest() != result["attempt_journal"]["sha256"]:
            raise SystemExit("REFUSING: development attempt-journal drift")
        item_by_id = {row["id"]: row for row in development["items"]}
        for reader in run_plan["panel"]:
            own = [row for row in result["rows"] if row["reader"] == reader["name"]]
            for row in own:
                item = item_by_id[row["item_id"]]
                if row["expected"] != item["answer"] or row["axis"] != item["axis"]:
                    raise SystemExit("REFUSING: development result answer binding drift")
                if row["correct"] != (row["parsed_answer"] == row["expected"]):
                    raise SystemExit("REFUSING: development result correctness drift")
            observed = {
                "exact_code_cells": sum(row["exact_code"] for row in own),
                "correct_cells": sum(row["correct"] for row in own),
                "correct_by_axis": {
                    axis: sum(row["correct"] for row in own if row["axis"] == axis)
                    for axis in development["axes"]
                },
                "correct_by_label": {
                    label: sum(row["correct"] for row in own if row["expected"] == label)
                    for label in development["labels"]
                },
                "thinking_bytes": sum(row["thinking_bytes"] for row in own),
                "fault_cells": sum(row["fault"] is not None for row in own),
            }
            if observed != result["summaries"][reader["name"]]:
                raise SystemExit(f"REFUSING: development summary drift for {reader['name']}")
        report["development_result"] = {
            "file": result_path.name,
            "content_sha256": result["content_sha256"],
            "response_cells": len(result["rows"]),
        }
        report["status"] = "passed-with-development-result"
    report["content_sha256"] = hashlib.sha256(canonical(report)).hexdigest()
    if args.write:
        target = ROOT / "audit-report.json"
        if target.exists():
            raise SystemExit("REFUSING: audit-report.json already exists")
        target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
