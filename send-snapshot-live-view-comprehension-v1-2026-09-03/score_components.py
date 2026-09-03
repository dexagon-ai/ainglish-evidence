#!/usr/bin/env python3
"""Recover the two independently scored questions from a panel cell journal."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("cells", type=Path, help="ainglish.panel.cell-results.v1 JSON")
    args = parser.parse_args()
    carrier = json.loads((ROOT / "items.json").read_text(encoding="utf-8"))
    by_id = {item["id"]: item for item in carrier["items"] if "option_components" in item}
    receipt = json.loads(args.cells.read_text(encoding="utf-8"))
    rows = receipt.get("rows")
    if not isinstance(rows, list):
        raise SystemExit("REFUSING: cell receipt has no rows list")

    totals: dict[tuple[str, ...], dict[str, list[int]]] = defaultdict(
        lambda: {"implementation": [0, 0], "consequence": [0, 0], "exact_pair": [0, 0]}
    )
    unrecognized = []
    for row in rows:
        item = by_id.get(row.get("item_id"))
        if item is None:
            continue  # target-independent calibration row
        answer = row.get("answer")
        components = item["option_components"].get(answer)
        if components is None:
            unrecognized.append({
                "item_id": row.get("item_id"), "reader": row.get("reader"),
                "arm": row.get("arm"), "answer": answer,
            })
            continue
        strata = item["strata"]
        keys = [
            ("all",),
            ("form", strata["form"]),
            ("form_domain_event", strata["form"], strata["domain"], strata["event"]),
            ("probe", strata["probe"]),
        ]
        scores = {
            "implementation": bool(components["implementation_correct"]),
            "consequence": bool(components["consequence_correct"]),
            "exact_pair": bool(components["implementation_correct"] and components["consequence_correct"]),
        }
        for key in keys:
            for component, correct in scores.items():
                totals[key][component][0] += int(correct)
                totals[key][component][1] += 1

    result_rows = []
    for key in sorted(totals):
        result_rows.append({
            "slice": list(key),
            "scores": {
                component: {
                    "correct": correct,
                    "n": n,
                    "accuracy": round(correct / n, 4) if n else None,
                }
                for component, (correct, n) in totals[key].items()
            },
        })
    result = {
        "kind": "dexagon.ainglish.snapshot-live-component-scores.v1",
        "carrier_sha256": carrier["sha256"],
        "source_attempt_id": receipt.get("attempt_id"),
        "recognized_scientific_cells": totals[("all",)]["exact_pair"][1],
        "unrecognized_scientific_cells": unrecognized,
        "results": result_rows,
    }
    if unrecognized:
        raise SystemExit(json.dumps(result, indent=2, ensure_ascii=False))
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
