#!/usr/bin/env python3
"""Recompute the one-shot Command R holdout result and journal binding."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
GENERIC = REPO / "reader-fresh-lineage-v1-2026-08-26"
sys.path.insert(0, str(GENERIC))
spec = importlib.util.spec_from_file_location("generic_command_r_holdout_audit", GENERIC / "run_candidate_once.py")
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def canonical(value: dict) -> bytes:
    material = copy.deepcopy(value)
    material.pop("content_sha256", None)
    return json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if hashlib.sha256(canonical(value)).hexdigest() != value.get("content_sha256"):
        raise SystemExit(f"REFUSING: digest drift: {path.name}")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    plan = checked(ROOT / "holdout-command-r-plan.json")
    packet = checked(REPO / plan["semantic_stage"]["packet"]["file"])
    result = checked(ROOT / plan["result_file"])
    if result["plan_sha256"] != plan["content_sha256"] or result["candidate"] != plan["candidate"]:
        raise SystemExit("REFUSING: plan/result binding drift")
    format_rows = result["format"]["rows"]
    semantic_rows = result["semantic"]["rows"]
    if len(format_rows) != 12 or len(semantic_rows) != 64:
        raise SystemExit("REFUSING: result population drift")
    controls = {row["id"]: row for row in plan["format_stage"]["controls"]}
    for row in format_rows:
        parsed, parse_error, exact = module.decode(row["raw_output"])
        target = controls[row["control_id"]]["target"]
        if (
            row["raw_output_sha256"] != hashlib.sha256(row["raw_output"].encode()).hexdigest()
            or row["parsed"] != parsed
            or row["parse_error"] != parse_error
            or row["valid_json"] != (parse_error is None)
            or row["schema_exact"] != exact
            or row["target"] != target
            or row["target_correct"] != (exact and parsed["answer"] == target)
        ):
            raise SystemExit("REFUSING: format projection drift")
    items = {row["id"]: row for row in packet["items"]}
    errors = []
    for row in semantic_rows:
        item = items[row["item_id"]]
        mapping = {chr(65 + index): label for index, label in enumerate(item["options"])}
        parsed, parse_error, exact = module.decode(row["raw_output"])
        code = parsed["answer"] if exact else None
        label = mapping.get(code)
        expected_code = next(key for key, value in mapping.items() if value == item["answer"])
        if (
            row["raw_output_sha256"] != hashlib.sha256(row["raw_output"].encode()).hexdigest()
            or row["parsed"] != parsed
            or row["parse_error"] != parse_error
            or row["valid_json"] != (parse_error is None)
            or row["schema_exact"] != exact
            or row["axis"] != item["axis"]
            or row["expected_label"] != item["answer"]
            or row["expected_code"] != expected_code
            or row["parsed_code"] != code
            or row["parsed_label"] != label
            or row["correct"] != (label == item["answer"])
        ):
            raise SystemExit("REFUSING: semantic projection drift")
        if not row["correct"]:
            errors.append({
                "item_id": row["item_id"],
                "axis": row["axis"],
                "expected_label": item["answer"],
                "observed_label": label,
            })
    format_observed = module.observed_format(format_rows)
    semantic_observed = module.observed_semantic(packet, semantic_rows)
    format_ok = module.format_passed(plan, format_observed)
    semantic_ok = module.semantic_passed(plan, semantic_observed)
    if (
        result["format"]["observed"] != format_observed
        or result["format"]["passed"] != format_ok
        or result["semantic"]["observed"] != semantic_observed
        or result["semantic"]["passed"] != semantic_ok
        or result["v8_holdout_eligible"] != semantic_ok
    ):
        raise SystemExit("REFUSING: aggregate projection drift")
    journal = ROOT / result["attempt_journal"]["file"]
    journal_sha = hashlib.sha256(journal.read_bytes()).hexdigest()
    if journal_sha != result["attempt_journal"]["sha256"]:
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
    report = {
        "kind": "ainglish.panel.reader-qualification-result-audit.v8",
        "instance": plan["instance"],
        "seat": "command-r",
        "lineage": plan["candidate"]["lineage"],
        "holdout_sha256": packet["content_sha256"],
        "plan_sha256": plan["content_sha256"],
        "result_sha256": result["content_sha256"],
        "journal_sha256": journal_sha,
        "format_observed": format_observed,
        "semantic_observed": semantic_observed,
        "error_items": errors,
        "qualified": semantic_ok,
        "scope_boundary": plan["scope"],
        "adverse_prior_disclosed": True,
        "model_calls": 0,
        "network_calls": 0,
        "status": "passed-with-qualified-result" if semantic_ok else "passed-with-adverse-result",
    }
    report["content_sha256"] = hashlib.sha256(canonical(report)).hexdigest()
    if args.write:
        target = ROOT / "holdout-command-r-result-audit.json"
        if target.exists():
            raise SystemExit("REFUSING: frozen holdout audit already exists")
        target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
