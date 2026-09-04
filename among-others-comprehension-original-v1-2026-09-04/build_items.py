#!/usr/bin/env python3
"""Combine the two frozen careful-English carriers into one form-stratified panel."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "among-list-completeness-confirmatory-carrier-2026-08-26"
OUTPUT = ROOT / "items.json"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def load(name: str) -> dict:
    return json.loads((SOURCE / name).read_text(encoding="utf-8"))


def main() -> None:
    among = load("items-among-others-vs-careful.json")
    closed = load("items-and-no-others-vs-careful.json")
    among_real = [dict(item, settlement_stratum="among-others") for item in among["items"] if not item.get("calibration")]
    closed_real = [dict(item, settlement_stratum="and-no-others") for item in closed["items"] if not item.get("calibration")]
    controls = [
        dict(item, calibration_scope="target-independent")
        for item in among["items"]
        if item.get("calibration")
    ]
    items = among_real + closed_real + controls
    digest = hashlib.sha256(canonical(items)).hexdigest()
    output = {
        "kind": "dexagon.ainglish.among-others-careful-combined.v1",
        "proposal_revision": "among-others-and-no-others-is-the-list-the-whole-list-2",
        "sha256": digest,
        "source_files": {
            "among-others": "items-among-others-vs-careful.json",
            "and-no-others": "items-and-no-others-vs-careful.json",
        },
        "population": "240 frozen careful-English comparisons, 120 per form, plus eight construct-free calibration items",
        "reader_calls": 0,
        "items": items,
    }
    OUTPUT.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"items": len(items), "sha256": digest}))


if __name__ == "__main__":
    main()
