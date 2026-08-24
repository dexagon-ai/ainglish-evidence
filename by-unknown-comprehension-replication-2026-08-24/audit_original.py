#!/usr/bin/env python3
"""Verify fresh-input disjointness after the local carrier was frozen."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import urllib.request


ROOT = Path(__file__).resolve().parent
FRESH = ROOT / "items.json"
ORIGINAL_URL = (
    "https://raw.githubusercontent.com/reticuli-labs/panel-artifacts/"
    "9f086f31a0cffe67470044a395c0cb3c1018f349/routing-evidence/"
    "unknown_items.json"
)
ORIGINAL_SHA256 = "4865276dd1616fc4464c008fb23f728431da283b931f9a7834d3f63b0e8ac2cf"
FRESH_SHA256 = "21396eaa6dd0593c767b79f0da4c6f8f2063303229d87a4bacbdcf2d01abd5cb"


def items(document: object) -> list[dict]:
    if isinstance(document, dict):
        return document["items"]
    if isinstance(document, list):
        return document
    raise SystemExit("REFUSING: unexpected item-document shape")


def canonical_digest(rows: list[dict]) -> str:
    encoded = json.dumps(
        rows, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def scientific(rows: list[dict]) -> list[dict]:
    return [row for row in rows if not row.get("calibration")]


def main() -> None:
    fresh_document = json.loads(FRESH.read_text())
    with urllib.request.urlopen(ORIGINAL_URL, timeout=30) as response:
        original_document = json.load(response)
    fresh = items(fresh_document)
    original = items(original_document)
    if canonical_digest(fresh) != FRESH_SHA256:
        raise SystemExit("REFUSING: frozen fresh carrier drifted")
    if canonical_digest(original) != ORIGINAL_SHA256:
        raise SystemExit("REFUSING: original carrier drifted")

    fresh_scored = scientific(fresh)
    original_scored = scientific(original)
    triple = lambda row: (row.get("english"), row.get("ainglish"), row.get("question"))
    arm_pair = lambda row: (row.get("english"), row.get("ainglish"))
    exact_triples = set(map(triple, fresh_scored)) & set(map(triple, original_scored))
    exact_arm_pairs = set(map(arm_pair, fresh_scored)) & set(map(arm_pair, original_scored))
    shared_ids = {row.get("id") for row in fresh_scored} & {
        row.get("id") for row in original_scored
    }
    if exact_triples or exact_arm_pairs or shared_ids:
        raise SystemExit("REFUSING: scientific input overlap detected")
    print(json.dumps({
        "original_url": ORIGINAL_URL,
        "original_items_sha256": ORIGINAL_SHA256,
        "fresh_items_sha256": FRESH_SHA256,
        "original_scientific_items": len(original_scored),
        "fresh_scientific_items": len(fresh_scored),
        "exact_scientific_triples": len(exact_triples),
        "exact_arm_pairs": len(exact_arm_pairs),
        "shared_ids": len(shared_ids),
        "same_metric_question": bool(
            {row.get("question") for row in fresh_scored}
            & {row.get("question") for row in original_scored}
        ),
        "reader_calls": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
