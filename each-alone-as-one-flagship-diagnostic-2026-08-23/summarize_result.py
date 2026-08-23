#!/usr/bin/env python3
"""Compute the preregistered descriptive strata from the saved real-cell receipt."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ATTEMPT_ID = "ee0493da-2bac-42af-9ccc-d07cd7c965c2"
MANIFEST_HASH = "30670e65701887ea943d82daba213db87827eb9a1b975e683705a3e9cbbd2490"
CELLS = ROOT / f"runspec.json.attempt-{ATTEMPT_ID}.cells.json"
MEASUREMENT = ROOT / f"runspec.json.attempt-{ATTEMPT_ID}.measurement.json"
ITEMS = ROOT / "careful-items.json"


def aggregate(rows: list[dict]) -> dict:
    cells = {}
    for arm in ("english", "ainglish"):
        selected = [row for row in rows if row["arm"] == arm]
        correct = sum(bool(row["correct"]) for row in selected)
        cells[arm] = {
            "correct": correct,
            "cells": len(selected),
            "accuracy": round(correct / len(selected), 4) if selected else None,
        }
    if cells["english"]["cells"] and cells["ainglish"]["cells"]:
        delta = 100 * (cells["ainglish"]["accuracy"] - cells["english"]["accuracy"])
    else:
        delta = None
    return {"arms": cells, "delta_pp": round(delta, 2) if delta is not None else None}


def grouped(rows: list[dict], keys: tuple[str, ...]) -> dict:
    values = sorted({tuple(row[key] for key in keys) for row in rows})
    output = {}
    for value in values:
        selected = [row for row in rows if tuple(row[key] for key in keys) == value]
        output["/".join(value)] = aggregate(selected)
    return output


def wrong_answers(rows: list[dict]) -> dict:
    output = {}
    values = sorted({(row["probe"], row["form"], row["arm"]) for row in rows})
    for probe, form, arm in values:
        selected = [
            row for row in rows
            if row["probe"] == probe and row["form"] == form and row["arm"] == arm
            and not row["correct"]
        ]
        output[f"{probe}/{form}/{arm}"] = {
            "wrong_cells": len(selected),
            "answers": dict(Counter(str(row["answer"]) for row in selected)),
        }
    return output


def main() -> None:
    item_rows = json.loads(ITEMS.read_text(encoding="utf-8"))["items"]
    items = {row["id"]: row for row in item_rows if not row.get("calibration")}
    cell_document = json.loads(CELLS.read_text(encoding="utf-8"))
    measurement = json.loads(MEASUREMENT.read_text(encoding="utf-8"))
    assert cell_document["attempt_id"] == ATTEMPT_ID
    assert measurement["attempt_id"] == ATTEMPT_ID
    assert len(cell_document["rows"]) == 300

    rows = []
    for cell in cell_document["rows"]:
        item = items[cell["item_id"]]
        rows.append({
            **cell,
            "form": item["form"],
            "probe": item["probe"],
            "scenario_id": item["scenario_id"],
        })

    summary = {
        "kind": "ainglish.flagship-diagnostic-strata.v1",
        "construct": "each-alone / as-one",
        "attempt_id": ATTEMPT_ID,
        "manifest_hash": MANIFEST_HASH,
        "interpretation": (
            "Descriptive preregistered strata from the single frozen run. No stratum-specific "
            "confidence interval or settlement claim is inferred from these aggregates."
        ),
        "primary": {
            "value": measurement["value"],
            "value_lo": measurement["value_lo"],
            "value_hi": measurement["value_hi"],
            "arms": measurement["arms"],
            "noninferiority_margin_pp": -5,
            "noninferiority_passed": measurement["value_lo"] >= -5,
            "calibration": measurement["calibration"],
            "panel_agreement": measurement["panel_agreement"],
            "per_member": measurement["per_member"],
            "resample_down": measurement["resample_down"],
        },
        "recomputed_overall": aggregate(rows),
        "by_form": grouped(rows, ("form",)),
        "by_probe": grouped(rows, ("probe",)),
        "by_form_probe": grouped(rows, ("form", "probe")),
        "by_reader": grouped(rows, ("reader",)),
        "by_reader_probe": grouped(rows, ("reader", "probe")),
        "wrong_answer_diagnostics": wrong_answers(rows),
    }
    (ROOT / "strata-summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "primary": summary["primary"],
        "by_form": summary["by_form"],
        "by_probe": summary["by_probe"],
        "by_form_probe": summary["by_form_probe"],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
