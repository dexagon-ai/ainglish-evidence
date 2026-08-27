#!/usr/bin/env python3
"""Validate a fresh 32-pair token carrier without importing a tokenizer."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parent
FORMS = ("pair-by-order", "every-combination")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def normalise(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).casefold()


def refuse(message: str) -> None:
    raise SystemExit(f"REFUSING: {message}")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: validate_replication_candidate.py CANDIDATE.json")
    candidate = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    rows = candidate.get("test_set")
    if not isinstance(rows, list) or len(rows) != 32:
        refuse("candidate must contain exactly 32 test_set rows")
    counts = {form: sum(row.get("form") == form for row in rows) for form in FORMS}
    if counts != {form: 16 for form in FORMS}:
        refuse(f"forms must be balanced 16/16, got {counts}")
    required = {"item_id", "form", "ainglish", "english"}
    if any(not isinstance(row, dict) or not required.issubset(row) for row in rows):
        refuse("each row must carry item_id, form, ainglish, and english")
    if any(not all(isinstance(row[key], str) and row[key].strip() for key in required) for row in rows):
        refuse("all required row values must be non-empty strings")
    if len({row["item_id"] for row in rows}) != 32:
        refuse("item ids are not unique")
    candidate_pairs = {(normalise(row["english"]), normalise(row["ainglish"])) for row in rows}
    if len(candidate_pairs) != 32:
        refuse("candidate complete pairs are not unique")
    for row in rows:
        form = row["form"]
        marked = normalise(row["ainglish"])
        careful = normalise(row["english"])
        if form not in FORMS or form not in marked:
            refuse(f"{row['item_id']}: Ainglish arm does not carry its declared form")
        if any(marker in careful for marker in FORMS):
            refuse(f"{row['item_id']}: careful-English arm leaks a marker")
    original = json.loads((ROOT / "token-items.json").read_text(encoding="utf-8"))["test_set"]
    original_pairs = {(normalise(row["english"]), normalise(row["ainglish"])) for row in original}
    overlap = candidate_pairs & original_pairs
    if overlap:
        refuse(f"candidate reuses {len(overlap)} complete target pairs")
    result = {
        "kind": "ainglish.token-replication-candidate-validation.v1",
        "valid": True,
        "pairs": 32,
        "form_counts": counts,
        "complete_pair_overlap": 0,
        "test_set_sha256": hashlib.sha256(canonical(rows)).hexdigest(),
        "tokenizer_calls": 0,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
