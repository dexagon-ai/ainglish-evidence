#!/usr/bin/env python3
"""Fail-closed checks for the frozen flagship shortlist."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def verified(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    claimed = value.pop("content_sha256")
    actual = hashlib.sha256(canonical(value)).hexdigest()
    if actual != claimed:
        raise ValueError(f"digest mismatch: {path.name}")
    value["content_sha256"] = claimed
    return value


def main() -> None:
    snapshot = verified(ROOT / "snapshot.json")
    personalized = verified(ROOT / "personalized.json")
    ranking = verified(ROOT / "ranking.json")
    assert ranking["source_snapshot_sha256"] == snapshot["content_sha256"]
    assert ranking["source_personalized_sha256"] == personalized["content_sha256"]
    assert ranking["population"]["language_evidence_rows_reviewed"] == len(snapshot["language_rows"])
    assert len(ranking["rows"]) == ranking["population"]["shortlisted"] == 20
    assert len({row["slug"] for row in ranking["rows"]}) == 20
    assert [row["rank"] for row in ranking["rows"]] == list(range(1, 21))
    assert all(0 <= row["editorial_score"] <= 5 for row in ranking["rows"])
    assert ranking["model_calls"] == ranking["governance_writes"] == 0
    print(json.dumps({"status": "verified", "rows": 20, "digest": ranking["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
