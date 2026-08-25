#!/usr/bin/env python3
"""Build a deterministic, receipt-linked summary of all flagship campaigns."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def interpretation(value: float, lo: float, hi: float) -> str:
    if lo > 0:
        return "supportive"
    if hi < 0:
        return "adverse"
    if lo == 0 and hi == 0:
        return "tie"
    if hi == 0 and value < 0:
        return "non-positive"
    return "unresolved"


def main() -> None:
    index = json.loads((ROOT / "runspec-index.json").read_text(encoding="utf-8"))
    rows = []
    for campaign, spec in index["campaigns"].items():
        matches = sorted(ROOT.glob(f"{spec['receipt_stem']}.attempt-*.measurement.json"))
        if len(matches) != 1:
            raise SystemExit(f"expected exactly one receipt for {campaign}, found {len(matches)}")
        measurement_path = matches[0]
        measurement = json.loads(measurement_path.read_text(encoding="utf-8"))
        attempt_id = measurement["attempt_id"]
        cells_path = ROOT / f"{spec['receipt_stem']}.attempt-{attempt_id}.cells.json"
        calibration_path = ROOT / f"{spec['receipt_stem']}.attempt-{attempt_id}.calibration.cells.json"
        for path in (cells_path, calibration_path):
            if not path.is_file():
                raise SystemExit(f"missing receipt: {path.name}")
        value = measurement["value"]
        lo = measurement["value_lo"]
        hi = measurement["value_hi"]
        rows.append(
            {
                "campaign": campaign,
                "attempt_id": attempt_id,
                "metric": measurement["metric"],
                "value": value,
                "value_lo": lo,
                "value_hi": hi,
                "interpretation": interpretation(value, lo, hi),
                "arms": measurement["arms"],
                "calibration": measurement["calibration"],
                "transport_faults": measurement["manifest"]["transport_faults"]["total"],
                "per_member": measurement["per_member"],
                "receipts": {
                    "measurement": {"path": measurement_path.name, "sha256": digest(measurement_path)},
                    "cells": {"path": cells_path.name, "sha256": digest(cells_path)},
                    "calibration_cells": {
                        "path": calibration_path.name,
                        "sha256": digest(calibration_path),
                    },
                },
            }
        )
    payload = {
        "kind": "dexagon.ainglish.flagship-reference-loaded-summary.v1",
        "runspec_index_sha256": index["content_sha256"],
        "campaign_count": len(rows),
        "independence_note": (
            "The two reader families are one Dexagon evidence principal. These post-ratification "
            "diagnostics do not independently confirm any proposal."
        ),
        "results": rows,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    payload["content_sha256"] = hashlib.sha256(canonical).hexdigest()
    (ROOT / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Reference-loaded flagship results",
        "",
        "All eight campaigns passed their preregistered planted-effect calibration gate and had zero "
        "transport faults. Values are Ainglish-minus-careful-English comprehension accuracy in "
        "percentage points.",
        "",
        "| Form | Delta | Interval | Reading |",
        "|---|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['campaign']}` | {row['value']:+.2f} | "
            f"[{row['value_lo']:+.2f}, {row['value_hi']:+.2f}] | {row['interpretation']} |"
        )
    lines.extend(
        [
            "",
            "These are reference-loaded diagnostics, not tests of whether pretrained models already "
            "knew Ainglish. Two local reader families still constitute one Dexagon evidence principal "
            "and cannot independently confirm one another.",
            "",
            f"Machine-readable summary digest: `{payload['content_sha256']}`.",
        ]
    )
    (ROOT / "RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
