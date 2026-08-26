#!/usr/bin/env python3
"""Recover the complete result after the post-run summary projection fault."""

from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path

from build_plan import canonical, checked
from run_once import project


ROOT = Path(__file__).resolve().parent


def main() -> None:
    target = ROOT / "result.json"
    journal_path = ROOT / "attempt-journal.jsonl"
    if target.exists():
        raise SystemExit("REFUSING: result.json already exists")
    plan = checked(ROOT / "plan.json")
    events = [json.loads(line) for line in journal_path.read_text(encoding="utf-8").splitlines()]
    if not events or events[0].get("event") != "run_started" or events[-1] != {"cells": 72, "event": "run_completed"}:
        raise SystemExit("REFUSING: journal does not show a complete run")
    if events[0].get("plan_sha256") != plan["content_sha256"]:
        raise SystemExit("REFUSING: journal belongs to another plan")
    attempts = [row for row in events if row.get("event") == "cell_attempted"]
    records = [row for row in events if row.get("event") == "cell_recorded"]
    if len(attempts) != 72 or len(records) != 72:
        raise SystemExit("REFUSING: journal cell population is incomplete")
    for attempt, record in zip(attempts, records):
        if (
            attempt["ordinal"] != record["ordinal"]
            or attempt["reader"] != record["row"]["reader"]
            or attempt["control_id"] != record["row"]["control_id"]
        ):
            raise SystemExit("REFUSING: attempted and recorded cell sequence drift")
    rows = [record["row"] for record in records]
    if len({(row["reader"], row["control_id"]) for row in rows}) != 72:
        raise SystemExit("REFUSING: duplicate recovered cell")
    summaries, compatible = project(plan, rows)
    result = {
        "kind": plan["result_kind"],
        "evidentiary_status": plan["evidentiary_status"],
        "plan_sha256": plan["content_sha256"],
        "started_at": events[0]["started_at"],
        "completed_at": None,
        "recovered_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "preflight": {
            "status": "passed-before-run",
            "details_retained": False,
            "note": "The original runner retained preflight details only for its post-journal result projection; the projection fault occurred before that result was written.",
        },
        "recovery": {
            "reason": "Post-run KeyError while projecting compatibility_gate keys after the run_completed journal event.",
            "model_calls_repeated": 0,
            "source": {"file": journal_path.name, "sha256": hashlib.sha256(journal_path.read_bytes()).hexdigest()},
        },
        "attempt_journal": {"file": journal_path.name, "sha256": hashlib.sha256(journal_path.read_bytes()).hexdigest()},
        "summaries": summaries,
        "compatible_readers": compatible,
        "rows": rows,
    }
    result["content_sha256"] = hashlib.sha256(canonical(result)).hexdigest()
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"summaries": summaries, "compatible_readers": compatible, "sha256": result["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
