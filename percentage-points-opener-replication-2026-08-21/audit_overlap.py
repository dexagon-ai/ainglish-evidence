#!/usr/bin/env python3
"""Verify the original artifact and emit a no-reader complete-pair overlap receipt."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ORIGINAL = ROOT / "original-items.json"
REPLICATION = ROOT / "items.json"
OUT = ROOT / "overlap-audit.json"
ORIGINAL_SHA = "c7719b1721eaddfcada578485525839f725886fb1fc9c77ccde3ba6177c3c6bf"
REPLICATION_SHA = "4962794f1223a00dd5603b27c05339f65a621ed8654f005d5a650469659b92ca"


def items(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload["items"] if isinstance(payload, dict) else payload


def canonical_sha(rows: list[dict]) -> str:
    encoded = json.dumps(rows, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def main() -> None:
    original = items(ORIGINAL)
    replication = items(REPLICATION)
    original_sha = canonical_sha(original)
    replication_sha = canonical_sha(replication)
    if original_sha != ORIGINAL_SHA:
        raise SystemExit(f"original canonical hash mismatch: {original_sha}")
    if replication_sha != REPLICATION_SHA:
        raise SystemExit(f"replication canonical hash mismatch: {replication_sha}")

    original_real = [row for row in original if not row.get("calibration")]
    replication_real = [row for row in replication if not row.get("calibration")]
    original_pairs = {(row["english"], row["ainglish"]): row["id"] for row in original_real}
    replication_pairs = {(row["english"], row["ainglish"]): row["id"] for row in replication_real}
    overlap = [
        {
            "original_id": original_pairs[pair],
            "replication_id": replication_pairs[pair],
            "english": pair[0],
            "ainglish": pair[1],
        }
        for pair in sorted(original_pairs.keys() & replication_pairs.keys())
    ]
    receipt = {
        "kind": "dexagon.ainglish.complete_pair_overlap_receipt.v1",
        "target_manifest_hash": "f9e78cc01f6725961fc0b9b119ae6f5d09f74d2858b92d81f2f1d8a08fa75c5b",
        "original_items_canonical_sha256": original_sha,
        "replication_items_canonical_sha256": replication_sha,
        "grain": "exact complete (english, ainglish) pair among non-calibration items",
        "original_scientific_items": len(original_real),
        "replication_scientific_items": len(replication_real),
        "overlap_count": len(overlap),
        "input_disjointness": (
            (len(replication_real) - len(overlap)) / len(replication_real)
            if replication_real else None
        ),
        "overlap": overlap,
        "reader_calls": 0,
    }
    if overlap:
        raise SystemExit(json.dumps(receipt, indent=2, ensure_ascii=False))
    OUT.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
