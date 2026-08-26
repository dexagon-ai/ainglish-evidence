#!/usr/bin/env python3
"""Validate a fresh role-cardinality token replication packet without tokenizing it."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent
FORMS = ("one-or-more", "exactly-one")
SURFACE = re.compile(r"^(one-or-more|exactly-one)\(([^)]+)\):\s*(.+?)\.?$")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def norm(value: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())


def surface(row: dict) -> tuple[str, str, str]:
    match = SURFACE.match(row.get("ainglish", "").strip())
    if not match:
        raise ValueError(f"{row.get('item_id')}: malformed Ainglish surface")
    form, role, action = match.groups()
    if form != row.get("form"):
        raise ValueError(f"{row.get('item_id')}: form field disagrees with surface")
    return form, norm(role), norm(action)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
    rows = candidate.get("test_set")
    if not isinstance(rows, list) or len(rows) != 32:
        raise SystemExit("REFUSING: candidate must contain exactly 32 test_set rows")
    if len({row.get("item_id") for row in rows}) != 32:
        raise SystemExit("REFUSING: candidate item IDs are missing or repeated")
    counts = {form: sum(row.get("form") == form for row in rows) for form in FORMS}
    if counts != {"one-or-more": 16, "exactly-one": 16}:
        raise SystemExit(f"REFUSING: form balance is {counts}")

    original = json.loads((ROOT / "token-items.json").read_text(encoding="utf-8"))["test_set"]
    original_pairs = {(norm(row["ainglish"]), norm(row["english"])) for row in original}
    original_surfaces = [surface(row) for row in original]
    original_roles = {role for _, role, _ in original_surfaces}
    original_actions = {action for _, _, action in original_surfaces}

    candidate_pairs = set()
    candidate_roles = set()
    candidate_actions = set()
    for row in rows:
        try:
            form, role, action = surface(row)
        except ValueError as error:
            raise SystemExit(f"REFUSING: {error}") from error
        english = row.get("english")
        if not isinstance(english, str) or not english.strip():
            raise SystemExit(f"REFUSING: {row.get('item_id')} has no careful-English control")
        lowered = norm(english)
        if form == "one-or-more" and not ("at least one" in lowered and ("additional" in lowered or "more" in lowered) and ("allowed" in lowered or "permitted" in lowered)):
            raise SystemExit(f"REFUSING: {row.get('item_id')} does not carry both one-or-more bounds")
        if form == "exactly-one" and not ("exactly one" in lowered and ("multiple" in lowered or "more than one" in lowered)):
            raise SystemExit(f"REFUSING: {row.get('item_id')} does not carry the exactly-one upper bound")
        pair = (norm(row["ainglish"]), lowered)
        if pair in candidate_pairs or pair in original_pairs:
            raise SystemExit(f"REFUSING: {row.get('item_id')} repeats a candidate or original complete pair")
        if role in original_roles or action in original_actions:
            raise SystemExit(f"REFUSING: {row.get('item_id')} reuses an original role or action")
        candidate_pairs.add(pair)
        candidate_roles.add(role)
        candidate_actions.add(action)

    if len(candidate_roles) != 32 or len(candidate_actions) != 32:
        raise SystemExit("REFUSING: candidate roles and actions must each be unique")
    print(json.dumps({
        "valid": True,
        "target_original": "e2a2653b609d5819169ab02fb42497a8b285d93453df2692ee8352feb583f4fb",
        "pairs": 32,
        "form_counts": counts,
        "candidate_test_set_sha256": hashlib.sha256(canonical(rows)).hexdigest(),
        "tokenizers_loaded": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
