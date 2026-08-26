#!/usr/bin/env python3
"""Recompute both 64-cell result projections and their durable journal bindings."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

from build_development_plans import canonical, checked


ROOT = Path(__file__).resolve().parent
GENERIC = ROOT.parent / "reader-fresh-lineage-v1-2026-08-26"
sys.path.insert(0, str(GENERIC))
from run_candidate_once import decode, format_passed, observed_format, observed_semantic, semantic_passed  # noqa: E402


def audit(short: str, packet: dict) -> dict:
    plan = checked(ROOT / f"holdout-{short}-plan.json")
    result = checked(ROOT / f"holdout-{short}-result.json")
    if result["plan_sha256"] != plan["content_sha256"] or result["candidate"] != plan["candidate"]:
        raise SystemExit("REFUSING: plan/result binding drift")
    format_rows = result["format"]["rows"]
    semantic_rows = result["semantic"]["rows"]
    if len(format_rows) != 12 or len(semantic_rows) != 64:
        raise SystemExit("REFUSING: result cell population drift")
    controls = {row["id"]: row for row in plan["format_stage"]["controls"]}
    for row in format_rows:
        parsed, parse_error, exact = decode(row["raw_output"])
        target = controls[row["control_id"]]["target"]
        if (
            row["raw_output_sha256"] != hashlib.sha256(row["raw_output"].encode()).hexdigest()
            or row["parsed"] != parsed or row["parse_error"] != parse_error
            or row["valid_json"] != (parse_error is None) or row["schema_exact"] != exact
            or row["target"] != target or row["target_correct"] != (exact and parsed["answer"] == target)
        ):
            raise SystemExit("REFUSING: format raw projection drift")
    items = {row["id"]: row for row in packet["items"]}
    for row in semantic_rows:
        item = items[row["item_id"]]
        mapping = {chr(65 + index): label for index, label in enumerate(item["options"])}
        parsed, parse_error, exact = decode(row["raw_output"])
        code = parsed["answer"] if exact else None
        label = mapping.get(code)
        expected_code = next(code for code, value in mapping.items() if value == item["answer"])
        if (
            row["raw_output_sha256"] != hashlib.sha256(row["raw_output"].encode()).hexdigest()
            or row["parsed"] != parsed or row["parse_error"] != parse_error
            or row["valid_json"] != (parse_error is None) or row["schema_exact"] != exact
            or row["axis"] != item["axis"] or row["expected_label"] != item["answer"]
            or row["expected_code"] != expected_code or row["parsed_code"] != code
            or row["parsed_label"] != label or row["correct"] != (label == item["answer"])
        ):
            raise SystemExit("REFUSING: semantic raw projection drift")
    format_observed = observed_format(format_rows)
    semantic_observed = observed_semantic(packet, semantic_rows)
    format_ok = format_passed(plan, format_observed)
    semantic_ok = semantic_passed(plan, semantic_observed)
    if (
        result["format"]["observed"] != format_observed or result["format"]["passed"] != format_ok
        or result["semantic"]["observed"] != semantic_observed or result["semantic"]["passed"] != semantic_ok
        or result["v8_holdout_eligible"] != semantic_ok
    ):
        raise SystemExit("REFUSING: aggregate projection drift")
    journal = ROOT / result["attempt_journal"]["file"]
    if hashlib.sha256(journal.read_bytes()).hexdigest() != result["attempt_journal"]["sha256"]:
        raise SystemExit("REFUSING: journal digest drift")
    events = [json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines()]
    rows = format_rows + semantic_rows
    attempts = [event for event in events if event.get("event") == "cell_attempted"]
    records = [event for event in events if event.get("event") == "cell_recorded"]
    if len(attempts) != 76 or len(records) != 76 or len(events) != 155:
        raise SystemExit("REFUSING: journal population drift")
    for ordinal, (attempt, record, row) in enumerate(zip(attempts, records, rows), 1):
        key = "control_id" if row["stage"] == "format" else "item_id"
        if attempt != {"event": "cell_attempted", "stage": row["stage"], "ordinal": ordinal, key: row[key]}:
            raise SystemExit("REFUSING: journal attempt sequence drift")
        if record != {"event": "cell_recorded", "stage": row["stage"], "ordinal": ordinal, "row": row}:
            raise SystemExit("REFUSING: journal record sequence drift")
    return {
        "lineage": plan["candidate"]["lineage"],
        "plan_sha256": plan["content_sha256"],
        "result_sha256": result["content_sha256"],
        "journal_sha256": result["attempt_journal"]["sha256"],
        "observed": semantic_observed,
        "qualified": semantic_ok,
    }


def main() -> None:
    packet = checked(ROOT / "holdout.json")
    document = {
        "kind": "ainglish.panel.reader-qualification-result-audit.v8",
        "holdout_sha256": packet["content_sha256"],
        "readers": [audit("phi", packet), audit("qwen", packet)],
        "model_calls": 0,
        "network_calls": 0,
        "status": "passed",
    }
    document["content_sha256"] = hashlib.sha256(canonical(document)).hexdigest()
    target = ROOT / "holdout-results-audit.json"
    if target.exists():
        if checked(target) != document:
            raise SystemExit("REFUSING: result audit drift")
    else:
        target.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(document, indent=2))


if __name__ == "__main__":
    main()
