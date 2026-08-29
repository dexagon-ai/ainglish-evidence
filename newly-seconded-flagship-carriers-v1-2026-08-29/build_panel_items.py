#!/usr/bin/env python3
"""Convert the frozen comparator packets into panel-harness item artifacts."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
COMPARATORS = ("bare", "careful", "practical")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def calibrations(prefix: str) -> list[dict]:
    rows = []
    for index in range(12):
        bay = 71 + index
        answer = f"bay {bay}"
        options = [answer, f"bay {bay + 1}", "not stated"]
        options = options[index % 3:] + options[:index % 3]
        rows.append({
            "id": f"{prefix}-cal-{index + 1:02d}",
            "calibration": True,
            "english": f"The routing note labels parcel {index + 1} dax({bay}), but gives no meaning for dax.",
            "ainglish": f"Control: dax(N) means the labelled parcel is stored in bay N. The routing note labels parcel {index + 1} dax({bay}).",
            "question": "Where does the control place the parcel?",
            "options": options,
            "answer": answer,
            "calibration_construct": "target-independent dax location marker",
        })
    return rows


def build(name: str) -> dict:
    source = json.loads((ROOT / f"{name}-comprehension-items.json").read_text(encoding="utf-8"))
    rows = calibrations(name)
    for original in source["items"]:
        for comparator in COMPARATORS:
            rows.append({
                "id": f"{original['id']}-{comparator}",
                "english": original[comparator],
                "ainglish": original["ainglish"],
                "question": original["question"],
                "options": original["options"],
                "answer": original["answer"],
                "form": original["form"],
                "comparison": comparator,
                "scenario_id": original["scenario_id"],
                "hard_cell": original["hard_cell"],
                "settlement_stratum": f"{original['form']}.{comparator}.{original['hard_cell']}",
                "primary_target": original.get("primary_statistic_population") or original.get("primary_scope_epoch"),
                "diagnostic_question": original["diagnostic_question"],
                "diagnostic_answer": original["diagnostic_answer"],
                "source_items_sha256": source["items_sha256"],
            })
    counts = Counter(row["settlement_stratum"] for row in rows if not row.get("calibration"))
    expected_strata = 60 if name == "average" else 78
    assert len(rows) == 492 and len(counts) == expected_strata
    assert set(counts.values()) == ({8} if name == "average" else {6, 7})
    digest = hashlib.sha256(canonical(rows)).hexdigest()
    return {
        "kind": f"dexagon.ainglish.{name}-manifest-bound-panel-items.v1",
        "sha256": digest,
        "source_items_sha256": source["items_sha256"],
        "items": rows,
    }


def main() -> None:
    for name in ("average", "deletion"):
        path = ROOT / f"{name}-panel.items.json"
        if path.exists() and "--refresh-before-freeze" not in sys.argv:
            raise SystemExit(f"REFUSING: {path.name} already exists")
        packet = build(name)
        path.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({
            "target": name, "items": len(packet["items"]),
            "scientific": sum(not row.get("calibration") for row in packet["items"]),
            "calibration": sum(bool(row.get("calibration")) for row in packet["items"]),
            "items_sha256": packet["sha256"], "model_calls": 0,
        }))


if __name__ == "__main__":
    main()
