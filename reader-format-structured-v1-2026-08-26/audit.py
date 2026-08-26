#!/usr/bin/env python3
"""Offline audit of the structured-output format screen."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from build_plan import build, canonical, checked
from run_once import project


ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    plan = checked(ROOT / "plan.json")
    if plan != build():
        raise SystemExit("REFUSING: format plan drift")
    report = {
        "kind": "ainglish.panel.reader-format-structured-audit.v1",
        "model_calls": 0,
        "network_calls": 0,
        "plan_sha256": plan["content_sha256"],
        "result": None,
        "compatible_readers": [],
        "status": "passed-static",
    }
    result_path = ROOT / "result.json"
    if result_path.exists():
        result = checked(result_path)
        if result["plan_sha256"] != plan["content_sha256"]:
            raise SystemExit("REFUSING: format result binding drift")
        identities = {(row["reader"], row["control_id"]) for row in result["rows"]}
        if len(result["rows"]) != 72 or len(identities) != 72:
            raise SystemExit("REFUSING: format result cell population drift")
        journal = ROOT / result["attempt_journal"]["file"]
        if hashlib.sha256(journal.read_bytes()).hexdigest() != result["attempt_journal"]["sha256"]:
            raise SystemExit("REFUSING: format attempt-journal drift")
        compatible = []
        for reader in plan["panel"]:
            own = [row for row in result["rows"] if row["reader"] == reader["name"]]
            for row in own:
                schema_exact = isinstance(row["parsed"], dict) and set(row["parsed"]) == {"answer"} and row["parsed"]["answer"] in "ABC"
                if row["schema_exact"] != schema_exact or row["target_correct"] != (schema_exact and row["parsed"]["answer"] == row["target"]):
                    raise SystemExit("REFUSING: format cell projection drift")
        expected_summaries, compatible = project(plan, result["rows"])
        if result["summaries"] != expected_summaries:
            raise SystemExit("REFUSING: format summary drift")
        if result["compatible_readers"] != compatible:
            raise SystemExit("REFUSING: compatible-reader projection drift")
        report["result"] = {"file": result_path.name, "content_sha256": result["content_sha256"], "response_cells": len(result["rows"])}
        report["compatible_readers"] = compatible
        report["status"] = "passed-with-result"
    report["content_sha256"] = hashlib.sha256(canonical(report)).hexdigest()
    if args.write:
        target = ROOT / "audit-report.json"
        if target.exists():
            raise SystemExit("REFUSING: audit-report.json already exists")
        target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
