#!/usr/bin/env python3
"""Offline structural audit for the frozen token carrier."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def prior_pairs() -> set[tuple[str, str]]:
    found: set[tuple[str, str]] = set()
    for path in REPO.rglob("*.json"):
        if ROOT in path.parents:
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        stack = [value]
        while stack:
            current = stack.pop()
            if isinstance(current, dict):
                if isinstance(current.get("ainglish"), str) and isinstance(current.get("english"), str):
                    found.add((current["ainglish"], current["english"]))
                stack.extend(current.values())
            elif isinstance(current, list):
                stack.extend(current)
    return found


def main() -> None:
    packet = json.loads((ROOT / "token-items.json").read_text(encoding="utf-8"))
    sealed = dict(packet)
    expected = sealed.pop("content_sha256")
    assert hashlib.sha256(canonical(sealed)).hexdigest() == expected
    rows = packet["test_set"]
    assert hashlib.sha256(canonical(rows)).hexdigest() == packet["items_sha256"]
    assert len(rows) == 32 and len({row["item_id"] for row in rows}) == 32
    assert packet["form_counts"] == {
        form: sum(row["form"] == form for row in rows) for form in packet["forms"]
    } == {"each-group": 16, "groups-combined": 16}
    assert len({row["group_set_ref"] for row in rows}) == 16
    assert all(row["group_set_ref"] in row["ainglish"] and row["group_set_ref"] in row["english"] for row in rows)
    assert all(row["ainglish"].startswith(f"{row['form']}(") for row in rows)
    assert not {(row["ainglish"], row["english"]) for row in rows} & prior_pairs()
    print(
        json.dumps(
            {
                "status": "ok",
                "pairs": 32,
                "form_counts": packet["form_counts"],
                "group_set_refs": 16,
                "prior_exact_pair_overlap": 0,
                "tokenizer_calls": 0,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
