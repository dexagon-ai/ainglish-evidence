#!/usr/bin/env python3
"""Fail-closed integrity checks for the whole-register flagship audit."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def verified(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    claimed = value.pop("content_sha256")
    actual = hashlib.sha256(canonical(value)).hexdigest()
    if claimed != actual:
        raise ValueError(f"digest mismatch: {path.name}")
    value["content_sha256"] = claimed
    return value


def main() -> None:
    snapshot = verified(ROOT / "snapshot.json")
    matrix = verified(ROOT / "matrix.json")
    assessments = json.loads((ROOT / "editorial-assessments.json").read_text(encoding="utf-8"))
    proposals = snapshot["current_language_proposals"]
    rows = matrix["rows"]
    assert matrix["source_snapshot_sha256"] == snapshot["content_sha256"]
    assert len(rows) == len(proposals) == snapshot["scope"]["current_language_rows"] == 85
    assert len({row["slug"] for row in rows}) == len(rows)
    assert {row["slug"] for row in rows} == set(assessments["entries"])
    assert [row["editorial_rank"] for row in rows] == list(range(1, len(rows) + 1))
    assert all(row["editorial_score"] == sum(row["editorial_checks"].values()) for row in rows)
    assert all(set(row["editorial_checks"]) == set(assessments["rubric"]) for row in rows)
    score_counts = Counter(str(row["editorial_score"]) for row in rows)
    assert matrix["population"]["editorial_score_counts"] == {
        key: score_counts[key] for key in sorted(score_counts, reverse=True)
    }
    omissions = [row for row in rows if row["editorial_score"] == 5 and not row["current_catalogue_entry"]]
    assert matrix["strong_catalogue_omissions"] == [row["slug"] for row in omissions]
    assert matrix["population"]["five_of_five_not_in_catalogue"] == len(omissions)
    assert matrix["population"]["current_catalogue_entries"] == len(snapshot["flagships"]["entries"]) == 17
    assert matrix["model_calls"] == matrix["governance_writes"] == 0
    print(json.dumps({
        "status": "verified",
        "population": len(rows),
        "catalogue_entries": 17,
        "five_of_five": sum(row["editorial_score"] == 5 for row in rows),
        "five_of_five_omissions": len(omissions),
        "digest": matrix["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()

