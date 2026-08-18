#!/usr/bin/env python3
"""Recompute the frozen primary, force and warrant strata from a panel cell receipt."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def rate(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 6) if denominator else None


def delta_pp(ainglish: float | None, english: float | None) -> float | None:
    if ainglish is None or english is None:
        return None
    return round(100 * (ainglish - english), 4)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--items", type=Path, required=True)
    parser.add_argument("--cells", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        item_doc = json.loads(args.items.read_text(encoding="utf-8"))
        cell_doc = json.loads(args.cells.read_text(encoding="utf-8"))
        if item_doc.get("sha256") != canonical_sha(item_doc.get("items")):
            raise ValueError("item document canonical hash drifted")
        items = {item["id"]: item for item in item_doc["items"] if not item.get("calibration")}
        rows = cell_doc["rows"]
        if len(rows) != cell_doc.get("real_cells_recorded"):
            raise ValueError("cell receipt count does not match its rows")
        if any(row.get("item_id") not in items for row in rows):
            raise ValueError("cell receipt names an unknown or calibration item")

        buckets: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
        dimensions = ("pooled", "form", "carrier", "reader", "domain", "case", "short_style")
        for row in rows:
            item = items[row["item_id"]]
            values = {
                "pooled": "all",
                "form": item.get("form", "unknown"),
                "carrier": item.get("carrier", "unknown"),
                "reader": row["reader"],
                "domain": item.get("domain", "unknown"),
                "case": item.get("case", "unknown"),
                "short_style": item.get("short_style", "not-applicable"),
            }
            enriched = {**row, "item": item}
            for dimension in dimensions:
                buckets[(dimension, str(values[dimension]), row["arm"])].append(enriched)

        def arm_record(rows_for_arm: list[dict[str, Any]]) -> dict[str, Any]:
            total = len(rows_for_arm)
            exact = sum(bool(row.get("correct")) for row in rows_for_arm)
            force_fp = sum(
                "recipient is required" in str(row.get("answer", ""))
                or "recipient is allowed" in str(row.get("answer", ""))
                for row in rows_for_arm
            )
            false_credit_rows = [
                row for row in rows_for_arm
                if row["item"].get("case") == "misapplied-standing"
            ]
            false_credit = sum(
                row.get("answer") == "claim matches the ledger" for row in false_credit_rows
            )
            return {
                "exact_correct": exact,
                "total": total,
                "exact_accuracy": rate(exact, total),
                "force_false_positives": force_fp,
                "force_false_positive_rate": rate(force_fp, total),
                "misapplied_standing_cells": len(false_credit_rows),
                "misapplied_standing_false_credit": false_credit,
                "misapplied_standing_false_credit_rate": rate(false_credit, len(false_credit_rows)),
            }

        def group(dimension: str, value: str) -> dict[str, Any]:
            english = arm_record(buckets.get((dimension, value, "english"), []))
            ainglish = arm_record(buckets.get((dimension, value, "ainglish"), []))
            return {
                "english": english,
                "ainglish": ainglish,
                "exact_accuracy_delta_pp": delta_pp(
                    ainglish["exact_accuracy"], english["exact_accuracy"]
                ),
                "force_false_positive_delta_pp": delta_pp(
                    ainglish["force_false_positive_rate"], english["force_false_positive_rate"]
                ),
                "misapplied_standing_false_credit_delta_pp": delta_pp(
                    ainglish["misapplied_standing_false_credit_rate"],
                    english["misapplied_standing_false_credit_rate"],
                ),
            }

        strata = {}
        for dimension in dimensions:
            values = sorted({key[1] for key in buckets if key[0] == dimension})
            strata[dimension] = {value: group(dimension, value) for value in values}

        summary = {
            "kind": "ainglish.proposal-decision.cell-summary.v1",
            "attempt_id": cell_doc.get("attempt_id"),
            "source": {
                "items_sha256": item_doc["sha256"],
                "cells_canonical_sha256": canonical_sha(cell_doc),
            },
            "comparison": sorted({item.get("comparison") for item in items.values()}),
            "strata": strata,
            "interpretation": [
                "Official and short-surface exact-profile deltas are interpreted per form, never pooled.",
                "Force false positives are options asserting recipient duty or permission.",
                "Authority-warrant results and primary comprehension are separate diagnostics.",
                "These transparent counts do not replace the harness bootstrap interval.",
            ],
        }
        args.output.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"REFUSING: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
