#!/usr/bin/env python3
"""Audit the frozen token carrier without loading any tokenizer."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    packet = json.loads((ROOT / "token-items.json").read_text(encoding="utf-8"))
    sealed = dict(packet)
    expected = sealed.pop("content_sha256")
    assert hashlib.sha256(canonical(sealed)).hexdigest() == expected
    rows = packet["test_set"]
    assert hashlib.sha256(canonical(rows)).hexdigest() == packet["items_sha256"]
    assert len(rows) == 96
    assert len({row["item_id"] for row in rows}) == 96
    assert len({row["event_clause"] for row in rows}) == 96
    for row in rows:
        assert row["event_clause"] in row["ainglish"] and row["event_clause"] in row["english"]
        if row["form"] == "repeat-event":
            assert row["ainglish"].startswith("repeat-event: ")
            assert "had previously" in row["english"]
        else:
            assert row["ainglish"].startswith(f"restore-state({row['result_state']}): ")
            assert "no earlier" in row["english"] and "is claimed" in row["english"]
    print(json.dumps({
        "items": 96,
        "form_counts": packet["form_counts"],
        "predicate_family_counts": packet["predicate_family_counts"],
        "items_sha256": packet["items_sha256"],
        "tokenizers_loaded": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
