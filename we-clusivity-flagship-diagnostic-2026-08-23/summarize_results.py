#!/usr/bin/env python3
"""Summarize preregistered clusivity strata from the two saved form receipts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FORMS = ("we-including-you", "we-excluding-you")
WARM_DISTRACTOR = (
    "the wording only adds a warmer team tone; whether the reader is included remains unresolved"
)


def aggregate(rows: list[dict]) -> dict:
    arms = {}
    for arm in ("english", "ainglish"):
        selected = [row for row in rows if row["arm"] == arm]
        correct = sum(bool(row["correct"]) for row in selected)
        arms[arm] = {
            "correct": correct,
            "cells": len(selected),
            "accuracy": round(correct / len(selected), 4) if selected else None,
        }
    delta = None
    if arms["english"]["cells"] and arms["ainglish"]["cells"]:
        delta = 100 * (arms["ainglish"]["accuracy"] - arms["english"]["accuracy"])
    return {"arms": arms, "delta_pp": round(delta, 2) if delta is not None else None}


def grouped(rows: list[dict], key: str) -> dict:
    return {
        value: aggregate([row for row in rows if row[key] == value])
        for value in sorted({row[key] for row in rows})
    }


def load_form(form: str) -> dict:
    measurements = list(ROOT.glob(f"runspec-{form}.json.attempt-*.measurement.json"))
    cells = list(ROOT.glob(f"runspec-{form}.json.attempt-*.cells.json"))
    if len(measurements) != 1 or len(cells) != 1:
        raise RuntimeError(
            f"expected one completed receipt pair for {form}; got "
            f"{len(measurements)} measurement and {len(cells)} cell files"
        )
    measurement = json.loads(measurements[0].read_text(encoding="utf-8"))
    cell_document = json.loads(cells[0].read_text(encoding="utf-8"))
    item_rows = json.loads((ROOT / f"{form}-items.json").read_text(encoding="utf-8"))["items"]
    items = {row["id"]: row for row in item_rows if not row.get("calibration")}
    if measurement["attempt_id"] != cell_document["attempt_id"]:
        raise RuntimeError(f"attempt mismatch for {form}")
    if len(cell_document["rows"]) != 300:
        raise RuntimeError(f"expected 300 real cells for {form}")
    rows = []
    for cell in cell_document["rows"]:
        item = items[cell["item_id"]]
        rows.append({**cell, "form": form, "probe": item["probe"], "scenario_id": item["scenario_id"]})
    wrong = [row for row in rows if not row["correct"]]
    primary = {
        key: measurement.get(key)
        for key in (
            "attempt_id", "value", "value_lo", "value_hi", "arms", "calibration",
            "panel_agreement", "panel_neff", "panel_neff_basis", "per_member",
            "resample_down", "yield_report", "transport_faults",
        )
    }
    primary["noninferiority_margin_pp"] = -5
    primary["noninferiority_passed"] = measurement["value_lo"] >= -5
    return {
        "primary": primary,
        "recomputed_overall": aggregate(rows),
        "by_probe": grouped(rows, "probe"),
        "by_reader": grouped(rows, "reader"),
        "wrong_answer_counts": dict(Counter(str(row["answer"]) for row in wrong)),
        "semantic_bleaching_wrong_cells": sum(row["answer"] == WARM_DISTRACTOR for row in wrong),
    }


def main() -> None:
    output = {
        "kind": "ainglish.clusivity-flagship-diagnostic-summary.v1",
        "construct": "we-including-you / we-excluding-you",
        "interpretation": (
            "Two separately preregistered form-specific primaries. Probe and reader aggregates are "
            "descriptive and do not acquire separate confidence intervals or settlement claims."
        ),
        "forms": {form: load_form(form) for form in FORMS},
    }
    path = ROOT / "result-summary.json"
    path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
