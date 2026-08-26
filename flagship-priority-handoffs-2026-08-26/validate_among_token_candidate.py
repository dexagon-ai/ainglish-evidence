#!/usr/bin/env python3
"""Validate a fresh independent among/no-others token packet without tokenizing it."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
ORIGINAL = ROOT.parent / "flagship-token-prerequisites-2026-08-26" / "items.json"
FORMS = ("among-others", "and-no-others")
SUFFIXES = {
    "among-others": (", among others.", ", among-others."),
    "and-no-others": (", and nothing else.", ", and-no-others."),
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def rows_from(value: object) -> list[dict[str, str]]:
    if isinstance(value, list):
        rows = value
    elif isinstance(value, dict) and isinstance(value.get("test_set"), list):
        rows = value["test_set"]
    elif (
        isinstance(value, dict)
        and isinstance(value.get("campaigns"), dict)
        and isinstance(value["campaigns"].get("among"), dict)
        and isinstance(value["campaigns"]["among"].get("test_set"), list)
    ):
        rows = value["campaigns"]["among"]["test_set"]
    else:
        raise ValueError("candidate must be a list, {test_set:[...]}, or {campaigns:{among:{test_set:[...]}}}")
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError("every test_set row must be an object")
    return rows


def normalized(row: dict[str, str]) -> tuple[str, str, str]:
    form = row.get("form")
    english = row.get("english")
    ainglish = row.get("ainglish")
    if form not in FORMS:
        raise ValueError(f"bad form: {form!r}")
    if not isinstance(english, str) or not english.strip():
        raise ValueError("english must be a non-empty string")
    if not isinstance(ainglish, str) or not ainglish.strip():
        raise ValueError("ainglish must be a non-empty string")
    english_suffix, ainglish_suffix = SUFFIXES[form]
    if not english.endswith(english_suffix):
        raise ValueError(f"{form} English must end exactly with {english_suffix!r}")
    if not ainglish.endswith(ainglish_suffix):
        raise ValueError(f"{form} Ainglish must end exactly with {ainglish_suffix!r}")
    english_base = english[: -len(english_suffix)]
    ainglish_base = ainglish[: -len(ainglish_suffix)]
    if english_base != ainglish_base:
        raise ValueError(f"{form} pair changes more than the declared careful control: {english!r}")
    if not english_base.strip():
        raise ValueError("pair base must be non-empty")
    return form, english_base, english + "\0" + ainglish


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: validate_among_token_candidate.py CANDIDATE.json")
    candidate_path = Path(sys.argv[1]).resolve()
    rows = rows_from(json.loads(candidate_path.read_text(encoding="utf-8")))
    if len(rows) != 32:
        raise SystemExit(f"REFUSING: expected exactly 32 complete pairs, got {len(rows)}")

    candidate = [normalized(row) for row in rows]
    counts = {form: sum(value[0] == form for value in candidate) for form in FORMS}
    if counts != {"among-others": 16, "and-no-others": 16}:
        raise SystemExit(f"REFUSING: expected 16 pairs per form, got {counts}")
    if len({value[2] for value in candidate}) != 32:
        raise SystemExit("REFUSING: duplicate complete pair in candidate")
    bases = {form: {value[1] for value in candidate if value[0] == form} for form in FORMS}
    if any(len(values) != 16 for values in bases.values()):
        raise SystemExit("REFUSING: duplicate normalized base within a form")
    if bases["among-others"] != bases["and-no-others"]:
        raise SystemExit("REFUSING: forms must use the same 16 normalized bases")

    original_doc = json.loads(ORIGINAL.read_text(encoding="utf-8"))
    original_rows = rows_from(original_doc)
    original = [normalized(row) for row in original_rows]
    original_pairs = {value[2] for value in original}
    original_bases = {value[1] for value in original}
    pair_overlap = sorted({value[2] for value in candidate} & original_pairs)
    base_overlap = sorted((bases["among-others"] | bases["and-no-others"]) & original_bases)
    if pair_overlap:
        raise SystemExit(f"REFUSING: {len(pair_overlap)} complete pair(s) reuse the original")
    if base_overlap:
        raise SystemExit(f"REFUSING: {len(base_overlap)} normalized base(s) reuse the original")

    clean_rows = [
        {"form": row["form"], "english": row["english"], "ainglish": row["ainglish"]}
        for row in rows
    ]
    print(json.dumps({
        "status": "candidate-valid",
        "pairs": 32,
        "form_counts": counts,
        "matched_bases": 16,
        "complete_pair_overlap_with_original": 0,
        "normalized_base_overlap_with_original": 0,
        "candidate_items_sha256": hashlib.sha256(canonical(clean_rows)).hexdigest(),
        "tokenizer_calls": 0,
        "network_calls": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
