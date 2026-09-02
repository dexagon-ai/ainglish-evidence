#!/usr/bin/env python3
"""Compose the already-frozen fresh careful-English carrier without inference."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
SOURCE = REPO / "flagship-comprehension-wave-v3-2026-08-29"
SOURCES = [
    SOURCE / "they-number--they-one--claim.items.json",
    SOURCE / "they-number--they-many--claim.items.json",
]
TARGET = "261b02c6af43cebe30a2b25993a39912715910ab9d0decba323bc40449b7a92e"


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def main() -> None:
    items = []
    source_receipts = []
    for path in SOURCES:
        rows = json.loads(path.read_text(encoding="utf-8"))
        items.extend(rows)
        source_receipts.append({
            "path": str(path.relative_to(REPO)),
            "file_sha256": sha256(path.read_bytes()).hexdigest(),
            "items_sha256": sha256(canonical(rows)).hexdigest(),
            "items": len(rows),
        })
    payload = {
        "kind": "dexagon.ainglish.they-number-longcat-replication-carrier.v1",
        "proposal_revision": "they-one-they-many",
        "construct": "they-one / they-many",
        "comparison": "registered number marker versus complete careful-English meaning",
        "replicates_hash": TARGET,
        "reader_calls": 0,
        "items": items,
    }
    (ROOT / "items.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    real = [row for row in items if not row.get("calibration")]
    index = {
        "kind": "dexagon.ainglish.they-number-longcat-replication-index.v1",
        "items_file": "items.json",
        "items_sha256": sha256(canonical(items)).hexdigest(),
        "scientific_items": len(real),
        "calibration_items": len(items) - len(real),
        "forms": dict(sorted(Counter(row["form"] for row in real).items())),
        "semantic_seams": dict(sorted(Counter(row["semantic_seam"] for row in real).items())),
        "detailed_strata": dict(sorted(Counter(row["settlement_stratum"] for row in real).items())),
        "sources": source_receipts,
        "replicates_hash": TARGET,
        "model_calls": 0,
    }
    index["content_sha256"] = sha256(canonical(index)).hexdigest()
    (ROOT / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(index, indent=2))


if __name__ == "__main__":
    main()

