#!/usr/bin/env python3
"""Summarize claim and diagnostic cell receipts without changing the filed scalar."""

from __future__ import annotations

from collections import defaultdict
import argparse
import json
from pathlib import Path

from build_packet import QUESTION_BLOCKS


ROOT = Path(__file__).resolve().parent


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def item_map(filename: str) -> dict[str, dict]:
    return {row["id"]: row for row in read_json(ROOT / filename)["items"] if not row.get("calibration")}


def summarize(filename: str, items: dict[str, dict]) -> dict:
    rows = read_json(ROOT / filename)["rows"]
    groups: dict[str, list[bool]] = defaultdict(list)
    cross = defaultdict(lambda: {"cells": 0, "false_cross_inferences": 0})
    for row in rows:
        item = items[row["item_id"]]
        correct = row.get("correct") is True
        force = item["force"]
        strata = item.get("strata") or {}
        dimensions = {
            "overall": "all",
            "force": force,
            "arm": row["arm"],
            "reader": row["reader"],
            "question_kind": strata.get("question_kind", "unknown"),
            "voice": strata.get("voice", "unknown"),
            "cross_cell": strata.get("load_bearing_cross_cell", "unknown"),
            "domain": strata.get("domain", "unknown"),
            "severity": strata.get("severity", "unknown"),
        }
        for dimension, value in dimensions.items():
            groups[f"{dimension}:{value}"].append(correct)
        q = QUESTION_BLOCKS[strata["question_kind"]]
        other_answer = q["possibility" if force == "permission" else "permission"]
        key = f"{force}:{row['arm']}"
        cross[key]["cells"] += 1
        if row.get("answer") == other_answer:
            cross[key]["false_cross_inferences"] += 1
    summaries = {
        key: {"cells": len(values), "accuracy": round(sum(values) / len(values), 6)}
        for key, values in sorted(groups.items())
    }
    for value in cross.values():
        value["rate"] = round(value["false_cross_inferences"] / value["cells"], 6)
    return {"cells": len(rows), "groups": summaries, "false_cross_inference": dict(sorted(cross.items()))}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("attempt_id")
    args = parser.parse_args()
    files = {
        "claim": (f"may-modal-claim.attempt-{args.attempt_id}.cells.json", "claim-items.json"),
        "bare": (f"may-modal-bare.attempt-{args.attempt_id}.cells.json", "bare-items.json"),
        "allowed_to": (f"may-modal-allowed-to.attempt-{args.attempt_id}.cells.json", "allowed-to-items.json"),
    }
    result = {
        "kind": "ainglish.may-modal.strata-summary.v1",
        "attempt_id": args.attempt_id,
        "comparisons": {
            name: summarize(cell_file, item_map(item_file))
            for name, (cell_file, item_file) in files.items()
        },
    }
    output = ROOT / f"strata-summary.attempt-{args.attempt_id}.json"
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
