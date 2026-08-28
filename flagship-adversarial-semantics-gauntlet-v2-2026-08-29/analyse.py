#!/usr/bin/env python3
"""Expand frozen batches and report adversarial semantic failures."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    correct = sum(row["correct"] for row in rows)
    invalid = sum(row["invalid_batch"] for row in rows)
    return {
        "correct": correct,
        "total": len(rows),
        "accuracy": round(correct / len(rows), 6) if rows else None,
        "invalid_batch_cells": invalid,
        "valid_cell_accuracy": round(correct / (len(rows) - invalid), 6) if len(rows) > invalid else None,
    }


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: analyse.py results/responses.jsonl")
    response_path = Path(sys.argv[1])
    calls = jsonl(response_path)
    plan = json.loads((ROOT / "RUN_PLAN.json").read_text(encoding="utf-8"))
    if len(calls) != plan["planned_calls"]:
        raise SystemExit(f"REFUSING: expected {plan['planned_calls']} calls, got {len(calls)}")
    keys = [(row["reader_id"], row["rank"]) for row in calls]
    if len(keys) != len(set(keys)):
        raise SystemExit("REFUSING: duplicate reader/rank call")
    items = json.loads((ROOT / "items.json").read_text(encoding="utf-8"))["items"]
    by_rank = defaultdict(list)
    for item in items:
        by_rank[item["rank"]].append(item)

    cells = []
    for call in calls:
        answers = call["answers"] if call["valid"] else {}
        for item in by_rank[call["rank"]]:
            observed = answers.get(item["id"])
            cells.append({
                "reader_id": call["reader_id"], "model": call["model"], "rank": item["rank"],
                "slug": item["slug"], "id": item["id"], "pole": item["pole"], "family": item["family"],
                "expected": item["expected"], "observed": observed, "correct": observed == item["expected"],
                "invalid_batch": not call["valid"], "batch_error": call["error"],
            })
    if len(cells) != plan["planned_cells"]:
        raise RuntimeError("expanded cell count drift")

    models = sorted({row["model"] for row in cells})
    model_summary = {model: summary([row for row in cells if row["model"] == model]) for model in models}
    family_summary = {
        model: {family: summary([row for row in cells if row["model"] == model and row["family"] == family]) for family in sorted({row["family"] for row in cells})}
        for model in models
    }
    label_summary = {
        model: {label: summary([row for row in cells if row["model"] == model and row["expected"] == label]) for label in ("entailed", "contradicted", "underdetermined")}
        for model in models
    }
    construct_summary = {
        model: [
            {"rank": rank, "slug": by_rank[rank][0]["slug"], **summary([row for row in cells if row["model"] == model and row["rank"] == rank])}
            for rank in range(1, 19)
        ] for model in models
    }
    channel_failures = {}
    for model in models:
        model_calls = [row for row in calls if row["model"] == model]
        empty = [row for row in model_calls if not row["content"]]
        if empty:
            channel_failures[model] = {
                "calls": len(model_calls), "empty_content_calls": len(empty),
                "nonempty_thinking_calls": sum(bool(row["thinking"]) for row in empty),
                "classification": "output-channel or structured-response failure; do not interpret invalid cells as semantic choices",
            }
    failures = [row for row in cells if not row["correct"]]
    output = {
        "schema": "ainglish.flagship-adversarial-analysis.v2",
        "responses_sha256": hashlib.sha256(response_path.read_bytes()).hexdigest(),
        "calls": len(calls), "cells": len(cells),
        "model_summary": model_summary,
        "family_summary": family_summary,
        "expected_label_summary": label_summary,
        "construct_summary": construct_summary,
        "output_channel_failures": channel_failures,
        "semantic_or_invalid_failures": failures,
        "failure_counts": {
            "total": len(failures),
            "by_family": dict(Counter(row["family"] for row in failures)),
            "by_expected": dict(Counter(row["expected"] for row in failures)),
            "by_observed": dict(Counter(str(row["observed"]) for row in failures)),
        },
        "interpretation_boundary": [
            "Only content-channel, reference-grounded judgements are scored.",
            "Malformed batches remain in the denominator but are separated from parseable semantic errors.",
            "High accuracy cannot establish cold comprehension, human intuitiveness, external adoption, or governance evidence.",
            "The gauntlet is designed to reveal complement assumptions and overreading; it is not a one-number flagship ranking.",
        ],
        "governance_evidence": False,
        "model_downloads": 0,
    }
    output["content_sha256"] = hashlib.sha256(canonical(output)).hexdigest()
    target = ROOT / "analysis.json"
    if target.exists():
        raise SystemExit("REFUSING: analysis.json already exists")
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "models": model_summary, "channel_failures": channel_failures, "failure_counts": output["failure_counts"], "content_sha256": output["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
