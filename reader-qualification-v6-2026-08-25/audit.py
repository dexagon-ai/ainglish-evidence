#!/usr/bin/env python3
"""Audit v6 frozen inputs, phase receipts, and terminal roster without model calls."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PHASES = (
    ("phase-a-holdout.json", "phase-a-result.json"),
    ("reserve-b-holdout.json", "reserve-b-result.json"),
    ("final-reserve-holdout.json", "final-reserve-result.json"),
)


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    sealed = dict(value)
    expected = sealed.pop("content_sha256")
    actual = hashlib.sha256(canonical(sealed)).hexdigest()
    if actual != expected:
        raise SystemExit(f"REFUSING: digest drift in {path.name}: {actual} != {expected}")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    plan = checked(ROOT / "plan.json")
    if len(plan["items"]) != 64 or len({row["id"] for row in plan["items"]}) != 64:
        raise SystemExit("REFUSING: plan item population drift")
    report = {
        "kind": "ainglish.panel.reader-qualification-integrity-report.v6",
        "model_calls": 0,
        "network_calls": 0,
        "plan_sha256": plan["content_sha256"],
        "plan_items": 64,
        "phases": [],
        "selected": None,
        "status": "passed",
    }
    prior_accumulated = []
    for spec_name, result_name in PHASES:
        spec_path = ROOT / spec_name
        result_path = ROOT / result_name
        if not spec_path.exists() and result_path.exists():
            raise SystemExit(f"REFUSING: {result_name} exists without {spec_name}")
        if not spec_path.exists():
            break
        spec = checked(spec_path)
        if spec["plan_sha256"] != plan["content_sha256"] or spec["items"] != plan["items"]:
            raise SystemExit(f"REFUSING: {spec_name} does not bind the frozen plan")
        row = {"spec": spec_name, "spec_sha256": spec["content_sha256"], "result": None}
        if result_path.exists():
            result = checked(result_path)
            if result["spec_sha256"] != spec["content_sha256"] or result["plan_sha256"] != plan["content_sha256"]:
                raise SystemExit(f"REFUSING: {result_name} binding drift")
            expected_cells = len(spec["panel"]) * len(spec["items"])
            identities = {(cell["reader"], cell["item_id"]) for cell in result["rows"]}
            if len(result["rows"]) != expected_cells or len(identities) != expected_cells:
                raise SystemExit(f"REFUSING: {result_name} cell population drift")
            journal = ROOT / result["attempt_journal"]["file"]
            if not journal.exists() or hashlib.sha256(journal.read_bytes()).hexdigest() != result["attempt_journal"]["sha256"]:
                raise SystemExit(f"REFUSING: {result_name} attempt-journal drift")
            fixed = []
            for reader in spec["panel"]:
                own = [cell for cell in result["rows"] if cell["reader"] == reader["name"]]
                by_axis = {axis: sum(cell["correct"] for cell in own if cell["axis"] == axis) for axis in spec["axes"]}
                observed = {
                    "exact_code_cells": sum(cell["exact_code"] for cell in own),
                    "correct_cells": sum(cell["correct"] for cell in own),
                    "correct_by_axis": by_axis,
                    "thinking_bytes": sum(cell["thinking_bytes"] for cell in own),
                    "fault_cells": sum(cell["fault"] is not None for cell in own),
                }
                if result["qualification"][reader["name"]]["observed"] != observed:
                    raise SystemExit(f"REFUSING: {result_name} qualification projection drift for {reader['name']}")
                rule = spec["selection_rule"]
                qualified = (
                    observed["exact_code_cells"] == rule["exact_code_cells_required"]
                    and observed["correct_cells"] >= rule["correct_cells_required"]
                    and all(value >= rule["correct_per_axis_required"] for value in by_axis.values())
                    and observed["thinking_bytes"] == rule["thinking_bytes_required"]
                    and observed["fault_cells"] == 0
                )
                if result["qualification"][reader["name"]]["qualified"] != qualified:
                    raise SystemExit(f"REFUSING: {result_name} qualification decision drift for {reader['name']}")
                if qualified:
                    fixed.append(reader)
            if result["fixed_roster"] != fixed:
                raise SystemExit(f"REFUSING: {result_name} fixed-roster drift")
            expected_accumulated = [*prior_accumulated, *result["fixed_roster"]]
            if result["accumulated_fixed_roster"] != expected_accumulated:
                raise SystemExit(f"REFUSING: {result_name} accumulated roster drift")
            ready = len({reader["lineage"] for reader in expected_accumulated}) >= spec["selection_rule"]["minimum_distinct_qualified_lineages"]
            if result["roster_ready"] != ready:
                raise SystemExit(f"REFUSING: {result_name} roster-ready drift")
            prior_accumulated = expected_accumulated
            row["result"] = result_name
            row["result_sha256"] = result["content_sha256"]
            row["qualification"] = result["qualification"]
            row["roster_ready"] = result["roster_ready"]
        report["phases"].append(row)
    selected_path = ROOT / "selected-result.json"
    if selected_path.exists():
        selected = checked(selected_path)
        if selected["plan_sha256"] != plan["content_sha256"] or selected["fixed_roster"] != prior_accumulated:
            raise SystemExit("REFUSING: selected roster drift")
        report["selected"] = {
            "file": selected_path.name,
            "content_sha256": selected["content_sha256"],
            "roster_ready": selected["roster_ready"],
            "fixed_roster": [row["name"] for row in selected["fixed_roster"]],
        }
    report["content_sha256"] = hashlib.sha256(canonical(report)).hexdigest()
    if args.write:
        target = ROOT / "audit-report.json"
        if target.exists():
            raise SystemExit("REFUSING: audit-report.json already exists")
        with target.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
