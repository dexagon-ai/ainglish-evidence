#!/usr/bin/env python3
"""Recompute the preregistered scientific strata from the saved real-cell receipt."""

from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ATTEMPT_ID = "4d11c748-2ac0-484c-8a9c-3524180d5dc1"
CELLS = ROOT / f"runspec-dedicated-gpu0.json.attempt-{ATTEMPT_ID}.cells.json"
MEASUREMENT = ROOT / f"runspec-dedicated-gpu0.json.attempt-{ATTEMPT_ID}.measurement.json"


def canonical_sha(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def group(item: dict) -> str:
    if "each-alone" in item["ainglish"]:
        return "each_alone"
    if "as-one" in item["ainglish"]:
        return "as_one"
    return "bare"


def main() -> None:
    item_doc = json.loads((ROOT / "items.json").read_text(encoding="utf-8"))
    items = {item["id"]: item for item in item_doc["items"] if not item.get("calibration")}
    cell_doc = json.loads(CELLS.read_text(encoding="utf-8"))
    measurement = json.loads(MEASUREMENT.read_text(encoding="utf-8"))
    rows = cell_doc["rows"]
    if cell_doc["attempt_id"] != ATTEMPT_ID or len(rows) != 38:
        raise SystemExit("REFUSING: real-cell receipt identity or yield drifted")

    counts: dict[tuple[str, ...], list[int]] = defaultdict(lambda: [0, 0])
    for row in rows:
        item_group = group(items[row["item_id"]])
        for key in (("pooled", row["arm"]), (item_group, row["arm"]),
                    ("reader", row["reader"], row["arm"]),
                    ("reader_group", row["reader"], item_group, row["arm"])):
            counts[key][1] += 1
            counts[key][0] += int(row["correct"])

    def record(key: tuple[str, ...]) -> dict:
        correct, total = counts[key]
        return {"correct": correct, "total": total, "accuracy": round(correct / total, 4)}

    readers = sorted({row["reader"] for row in rows})
    document = {
        "kind": "ainglish.panel.strata-summary.v1",
        "attempt_id": ATTEMPT_ID,
        "measurement_ref": "2aaf9a29d4a155074ce7536954c964adf5ae5bc9f69d94e563efb82eafc09c4a",
        "source_receipts": {
            "cells_canonical_sha256": canonical_sha(cell_doc),
            "measurement_request_canonical_sha256": canonical_sha(measurement),
        },
        "headline": {
            "metric": measurement["metric"],
            "value_pp": measurement["value"],
            "value_lo_pp": measurement["value_lo"],
            "value_hi_pp": measurement["value_hi"],
            "english": record(("pooled", "english")),
            "ainglish": record(("pooled", "ainglish")),
        },
        "scientific_strata": {
            item_group: {
                "english": record((item_group, "english")),
                "ainglish": record((item_group, "ainglish")),
                "delta_pp": round(
                    100 * (record((item_group, "ainglish"))["accuracy"]
                           - record((item_group, "english"))["accuracy"]), 2
                ),
            }
            for item_group in ("each_alone", "as_one", "bare")
        },
        "per_reader": {
            reader: {
                "english": record(("reader", reader, "english")),
                "ainglish": record(("reader", reader, "ainglish")),
            }
            for reader in readers
        },
        "interpretation": (
            "Supports ambiguity resolution versus bare plural in this original manifest. "
            "Does not test non-inferiority to careful explicit English and is not a replication."
        ),
    }
    (ROOT / "strata-summary.json").write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(document, indent=2, ensure_ascii=False))
    print("summary canonical sha256:", canonical_sha(document))


if __name__ == "__main__":
    main()
