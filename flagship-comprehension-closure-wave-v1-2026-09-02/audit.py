#!/usr/bin/env python3
"""Offline structural audit for the comprehension closure wave."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def main() -> None:
    index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    seen_ids: set[str] = set()
    seen_pairs: set[tuple[str, str]] = set()
    report = {}
    for name, meta in index["campaigns"].items():
        payload = json.loads((ROOT / meta["file"]).read_text(encoding="utf-8"))
        items = payload["items"]
        assert sha256(canonical(items)).hexdigest() == meta["items_sha256"]
        real = [row for row in items if not row.get("calibration")]
        cal = [row for row in items if row.get("calibration")]
        assert (len(real), len(cal)) == (meta["scientific_items"], meta["calibration_items"])
        assert all(set(("id", "english", "ainglish", "question", "options", "answer")) <= row.keys() for row in items)
        assert all(2 <= len(row["options"]) <= 8 and len(set(row["options"])) == len(row["options"]) and row["answer"] in row["options"] for row in items)
        assert all(row["english"].strip() != row["ainglish"].strip() for row in items)
        assert all(row.get("settlement_stratum") for row in real)
        expected = {row["id"] for row in meta["settlement_strata"]}
        counts = Counter(row["settlement_stratum"] for row in real)
        assert set(counts) == expected and dict(sorted(counts.items())) == meta["stratum_counts"]
        ids = {row["id"] for row in items}
        assert len(ids) == len(items) and not (ids & seen_ids)
        seen_ids |= ids
        pairs = {(row["english"].strip(), row["ainglish"].strip()) for row in real}
        assert len(pairs) == len(real) and not (pairs & seen_pairs)
        seen_pairs |= pairs
        positions = Counter(row["options"].index(row["answer"]) for row in real)
        report[name] = {
            "items_sha256": meta["items_sha256"],
            "scientific_items": len(real),
            "calibration_items": len(cal),
            "strata": dict(sorted(counts.items())),
            "answer_positions": dict(sorted(positions.items())),
        }
    output = {"kind": "dexagon.ainglish.flagship-comprehension-closure-wave-audit.v1", "campaigns": report, "global_unique_ids": len(seen_ids), "global_unique_scientific_pairs": len(seen_pairs), "model_calls": 0}
    (ROOT / "audit.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
