#!/usr/bin/env python3
"""Recompute transparent strata from a future SDK real-cell receipt."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys


def canonical_sha(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--items", type=Path, required=True)
    parser.add_argument("--cells", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        item_doc = json.loads(args.items.read_text(encoding="utf-8"))
        cell_doc = json.loads(args.cells.read_text(encoding="utf-8"))
        items = {item["id"]: item for item in item_doc["items"] if not item.get("calibration")}
        rows = cell_doc["rows"]
        if len(rows) != cell_doc.get("real_cells_recorded"):
            raise ValueError("cell receipt count does not match its rows")
        if any(row.get("item_id") not in items for row in rows):
            raise ValueError("cell receipt names an unknown or calibration item")

        counts: dict[tuple[str, ...], list[int]] = defaultdict(lambda: [0, 0])
        for row in rows:
            item = items[row["item_id"]]
            dimensions = {
                "pooled": "all",
                "marker": item["marker"],
                "carrier": item["carrier"],
                "channel": item["channel"],
                "position": item["position"],
                "frame": item["frame"],
                "case": item["case"],
                "reader": row["reader"],
            }
            for dimension, value in dimensions.items():
                key = (dimension, str(value), row["arm"])
                counts[key][1] += 1
                counts[key][0] += int(bool(row.get("correct")))

        def record(key: tuple[str, ...]) -> dict:
            correct, total = counts[key]
            return {
                "correct": correct,
                "total": total,
                "accuracy": round(correct / total, 6) if total else None,
            }

        def groups(dimension: str) -> dict:
            values = sorted({key[1] for key in counts if key[0] == dimension})
            result = {}
            for value in values:
                english = record((dimension, value, "english"))
                ainglish = record((dimension, value, "ainglish"))
                delta = None
                if english["accuracy"] is not None and ainglish["accuracy"] is not None:
                    delta = round(100 * (ainglish["accuracy"] - english["accuracy"]), 4)
                result[value] = {
                    "english": english,
                    "ainglish": ainglish,
                    "delta_pp": delta,
                }
            return result

        summary = {
            "kind": "ainglish.you-number.strata-summary.v1",
            "attempt_id": cell_doc.get("attempt_id"),
            "source": {
                "items_canonical_sha256": item_doc.get("sha256"),
                "cells_canonical_sha256": canonical_sha(cell_doc),
            },
            "strata": {
                dimension: groups(dimension)
                for dimension in ("pooled", "marker", "carrier", "channel", "position", "frame", "case", "reader")
            },
            "interpretation": (
                "The registered -5pp non-inferiority margin is applied to each marker separately. "
                "The pooled value cannot rescue a failing or unresolved marker. These descriptive "
                "strata do not replace an eligible interval from the filed measurement receipt."
            ),
        }
        args.output.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"REFUSING: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
