#!/usr/bin/env python3
"""Offline audit for one staged fresh-lineage candidate result."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from build_candidate_plan import canonical, checked
from run_candidate_once import decode, format_passed, observed_format, observed_semantic, semantic_passed


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent


def validate_raw_projection(row: dict) -> tuple[object, str | None, bool]:
    raw = row["raw_output"]
    if not isinstance(raw, str):
        raise SystemExit("REFUSING: raw output is not text")
    parsed, parse_error, schema_exact = decode(raw)
    if (
        row["raw_output_sha256"] != hashlib.sha256(raw.encode()).hexdigest()
        or row["parsed"] != parsed
        or row["parse_error"] != parse_error
        or row["valid_json"] != (parse_error is None)
        or row["schema_exact"] != schema_exact
    ):
        raise SystemExit("REFUSING: raw-output projection drift")
    if not isinstance(row["thinking_bytes"], int) or row["thinking_bytes"] < 0:
        raise SystemExit("REFUSING: invalid thinking byte count")
    if row["fault"] is not None and not isinstance(row["fault"], str):
        raise SystemExit("REFUSING: invalid fault label")
    return parsed, parse_error, schema_exact


def validate_journal(plan: dict, result: dict, format_rows: list[dict], semantic_rows: list[dict]) -> None:
    journal = ROOT / result["attempt_journal"]["file"]
    if hashlib.sha256(journal.read_bytes()).hexdigest() != result["attempt_journal"]["sha256"]:
        raise SystemExit("REFUSING: candidate journal drift")
    try:
        events = [json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines()]
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise SystemExit(f"REFUSING: invalid candidate journal: {exc}") from exc
    if not events or events[0] != {
        "event": "run_started",
        "plan_sha256": plan["content_sha256"],
        "started_at": result["started_at"],
    }:
        raise SystemExit("REFUSING: candidate journal start drift")
    attempts = [event for event in events if event.get("event") == "cell_attempted"]
    recordings = [event for event in events if event.get("event") == "cell_recorded"]
    expected_rows = format_rows + semantic_rows
    if len(attempts) != len(expected_rows) or len(recordings) != len(expected_rows):
        raise SystemExit("REFUSING: candidate journal cell population drift")
    for ordinal, (attempt, recording, row) in enumerate(zip(attempts, recordings, expected_rows), 1):
        stage = row["stage"]
        identifier_key = "control_id" if stage == "format" else "item_id"
        identifier = row[identifier_key]
        if (
            attempt != {"event": "cell_attempted", "stage": stage, "ordinal": ordinal, identifier_key: identifier}
            or recording != {"event": "cell_recorded", "stage": stage, "ordinal": ordinal, "row": row}
        ):
            raise SystemExit("REFUSING: candidate journal cell sequence drift")
    format_events = [event for event in events if event.get("event") == "format_completed"]
    run_events = [event for event in events if event.get("event") == "run_completed"]
    if len(format_events) != 1 or format_events[0] != {
        "event": "format_completed",
        "observed": result["format"]["observed"],
        "passed": result["format"]["passed"],
    }:
        raise SystemExit("REFUSING: candidate journal format completion drift")
    if len(run_events) != 1 or run_events[0] != {
        "event": "run_completed",
        "format_passed": result["format"]["passed"],
        "semantic_cells": len(semantic_rows),
        "development_passed": result["semantic"]["passed"],
    }:
        raise SystemExit("REFUSING: candidate journal run completion drift")
    expected_event_count = 1 + 2 * len(expected_rows) + 2
    if len(events) != expected_event_count:
        raise SystemExit("REFUSING: unexpected candidate journal events")


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
        format_rows = result["format"]["rows"]
        if len(format_rows) != 12 or len({row["control_id"] for row in format_rows}) != 12:
            raise SystemExit("REFUSING: format cell population drift")
        controls = {row["id"]: row for row in plan["format_stage"]["controls"]}
        for row in format_rows:
            parsed, _, schema_exact = validate_raw_projection(row)
            target = controls[row["control_id"]]["target"]
            if (
                row["target"] != target
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
                parsed, _, schema_exact = validate_raw_projection(row)
                parsed_code = parsed["answer"] if schema_exact else None
                parsed_label = mapping.get(parsed_code)
                if (
                    row["axis"] != item["axis"] or row["expected_label"] != item["answer"]
                    or row["expected_code"] != expected_code or row["parsed_code"] != parsed_code
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
        validate_journal(plan, result, format_rows, semantic_rows)
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
