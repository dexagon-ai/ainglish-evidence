#!/usr/bin/env python3
"""Offline audit for one staged fresh-lineage candidate result."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from build_candidate_plan import canonical, checked
from run_candidate_once import format_passed, observed_format, observed_semantic, semantic_passed


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True)
    parser.add_argument("--write")
    args = parser.parse_args()
    plan = checked(ROOT / args.plan)
    packet = checked(REPO / plan["semantic_stage"]["packet"]["file"])
    report = {
        "kind": "ainglish.panel.reader-fresh-lineage-development-audit.v1",
        "model_calls": 0, "network_calls": 0,
        "plan_sha256": plan["content_sha256"], "result": None,
        "format_passed": False, "semantic_exposed": False,
        "development_passed": False, "status": "passed-static",
    }
    result_path = ROOT / plan["result_file"]
    if result_path.exists():
        result = checked(result_path)
        if result["plan_sha256"] != plan["content_sha256"] or result["candidate"] != plan["candidate"]:
            raise SystemExit("REFUSING: candidate result binding drift")
        journal = ROOT / result["attempt_journal"]["file"]
        if hashlib.sha256(journal.read_bytes()).hexdigest() != result["attempt_journal"]["sha256"]:
            raise SystemExit("REFUSING: candidate journal drift")
        format_rows = result["format"]["rows"]
        if len(format_rows) != 12 or len({row["control_id"] for row in format_rows}) != 12:
            raise SystemExit("REFUSING: format cell population drift")
        controls = {row["id"]: row for row in plan["format_stage"]["controls"]}
        for row in format_rows:
            parsed = row["parsed"]
            valid_json = row["parse_error"] is None
            schema_exact = isinstance(parsed, dict) and set(parsed) == {"answer"} and isinstance(parsed["answer"], str) and parsed["answer"] in "ABC"
            target = controls[row["control_id"]]["target"]
            if (
                row["target"] != target or row["valid_json"] != valid_json
                or row["schema_exact"] != schema_exact
                or row["target_correct"] != (schema_exact and parsed["answer"] == target)
            ):
                raise SystemExit("REFUSING: format cell projection drift")
        format_observed = observed_format(format_rows)
        format_ok = format_passed(plan, format_observed)
        if result["format"]["observed"] != format_observed or result["format"]["passed"] != format_ok:
            raise SystemExit("REFUSING: format projection drift")
        semantic_rows = result["semantic"]["rows"]
        if format_ok:
            if len(semantic_rows) != 24 or len({row["item_id"] for row in semantic_rows}) != 24:
                raise SystemExit("REFUSING: semantic cell population drift")
            items = {row["id"]: row for row in packet["items"]}
            for row in semantic_rows:
                item = items[row["item_id"]]
                mapping = {chr(65 + index): label for index, label in enumerate(item["options"])}
                expected_code = next(code for code, label in mapping.items() if label == item["answer"])
                parsed = row["parsed"]
                valid_json = row["parse_error"] is None
                schema_exact = isinstance(parsed, dict) and set(parsed) == {"answer"} and isinstance(parsed["answer"], str) and parsed["answer"] in "ABC"
                parsed_code = parsed["answer"] if schema_exact else None
                parsed_label = mapping.get(parsed_code)
                if (
                    row["axis"] != item["axis"] or row["expected_label"] != item["answer"]
                    or row["expected_code"] != expected_code or row["valid_json"] != valid_json
                    or row["schema_exact"] != schema_exact or row["parsed_code"] != parsed_code
                    or row["parsed_label"] != parsed_label or row["correct"] != (parsed_label == item["answer"])
                ):
                    raise SystemExit("REFUSING: semantic cell projection drift")
            semantic_observed = observed_semantic(packet, semantic_rows)
            semantic_ok = semantic_passed(plan, semantic_observed)
        else:
            if semantic_rows or result["semantic"]["exposed"]:
                raise SystemExit("REFUSING: semantic exposure after format failure")
            semantic_observed = None
            semantic_ok = False
        if (
            result["semantic"]["observed"] != semantic_observed
            or result["semantic"]["passed"] != semantic_ok
            or result["v8_holdout_eligible"] != semantic_ok
        ):
            raise SystemExit("REFUSING: semantic projection drift")
        report.update({
            "result": {"file": result_path.name, "content_sha256": result["content_sha256"]},
            "format_passed": format_ok, "semantic_exposed": result["semantic"]["exposed"],
            "development_passed": semantic_ok, "status": "passed-with-result",
        })
    report["content_sha256"] = hashlib.sha256(canonical(report)).hexdigest()
    if args.write:
        target = ROOT / args.write
        if target.exists():
            raise SystemExit(f"REFUSING: {target.name} already exists")
        target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
