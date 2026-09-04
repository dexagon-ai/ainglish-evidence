#!/usr/bin/env python3
"""Audit freshness and balance of the three replication handoffs."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ORIGINAL = ROOT.parent / "language-progression-comprehension-wave-v1-2026-09-04"


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def main() -> None:
    index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    report = {"kind": "dexagon.ainglish.comprehension-replication-handoff-audit.v1", "campaigns": {}}
    for name, meta in index["campaigns"].items():
        new = json.loads((ROOT / meta["file"]).read_text(encoding="utf-8"))
        old = json.loads((ORIGINAL / meta["file"]).read_text(encoding="utf-8"))
        items = new["items"]
        science = [row for row in items if not row.get("calibration")]
        controls = [row for row in items if row.get("calibration")]
        new_pairs = {(row["english"], row["ainglish"], row["question"], row["answer"]) for row in science}
        old_pairs = {(row["english"], row["ainglish"], row["question"], row["answer"]) for row in old["items"] if not row.get("calibration")}
        assert len(science) == 32 and len(controls) == 16
        assert len(new_pairs) == len(science)
        assert not new_pairs & old_pairs
        assert sha256(canonical(items)).hexdigest() == meta["items_sha256"]
        strata = Counter(row["settlement_stratum"] for row in science)
        assert len(strata) == 2 and set(strata.values()) == {16}
        assert all(len(row["options"]) == 4 and row["answer"] in row["options"] for row in items)
        assert all(row["english"] != row["ainglish"] for row in controls)
        report["campaigns"][name] = {
            "items_sha256": meta["items_sha256"],
            "scientific_items": len(science),
            "calibration_items": len(controls),
            "complete_pair_overlap_with_original": 0,
            "stratum_counts": dict(sorted(strata.items())),
            "checks": "pass",
        }
    report["content_sha256"] = sha256(canonical(report)).hexdigest()
    (ROOT / "audit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
