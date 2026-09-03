#!/usr/bin/env python3
"""Refuse malformed or overlapping whole/part scientific inputs before reader spend."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

from ainglish import panel

ROOT = Path(__file__).resolve().parent
TARGET_URL = "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/3ccd0bcfa65a89097cb20a4635a2e32eb5136dd2/whole_part_true_contrasts_v2_items.json"
TARGET_SHA256 = "c54b00fb1221adfce7389b753b165f61c68f2510c084f8591aca97b3511653a9"


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def pair(row: dict) -> tuple[str, str]:
    return row["english"], row["ainglish"]


def main() -> None:
    rows = json.loads((ROOT / "items.json").read_text(encoding="utf-8"))
    target, target_digest = panel.fetch_items(TARGET_URL, TARGET_SHA256)
    real = [row for row in rows if not row.get("calibration")]
    calibration = [row for row in rows if row.get("calibration")]
    target_pairs = {pair(row) for row in target}
    overlaps = sorted({pair(row) for row in rows} & target_pairs)
    problems = []
    if len(real) != 48 or len(calibration) != 8:
        problems.append("carrier is not 48 scientific plus 8 calibration items")
    if len({row["id"] for row in rows}) != len(rows):
        problems.append("item ids are not unique")
    if len({pair(row) for row in rows}) != len(rows):
        problems.append("complete item pairs are not unique")
    if overlaps:
        problems.append(f"{len(overlaps)} complete pairs overlap the target")
    if Counter(row.get("form") for row in real) != {"part": 24, "whole": 24}:
        problems.append("scientific forms are not balanced")
    for row in real:
        form = row.get("form")
        if not row["ainglish"].startswith(form + "("):
            problems.append(f"{row['id']} does not carry its declared marker")
        expected = "a subset of" if form == "part" else "the entire population"
        if expected not in row["english"]:
            problems.append(f"{row['id']} lacks its full careful-English population mapping")
        if row.get("answer") not in row.get("options", []):
            problems.append(f"{row['id']} answer is absent from its options")
    result = {
        "kind": "dexagon.ainglish.whole-part-carrier-audit.v1",
        "items_sha256": sha256(canonical(rows)).hexdigest(),
        "target_items_sha256": target_digest,
        "scientific_items": len(real),
        "calibration_items": len(calibration),
        "form_counts": dict(Counter(row.get("form") for row in real)),
        "exact_pair_overlaps": len(overlaps),
        "problems": problems,
        "passed": not problems,
        "model_calls": 0,
    }
    (ROOT / "audit.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if problems:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
