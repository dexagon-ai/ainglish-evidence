#!/usr/bin/env python3
"""Audit the -4 token freeze without importing a tokenizer."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    packet = json.loads((ROOT / "token-items.json").read_text(encoding="utf-8"))
    index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    sealed_packet = dict(packet)
    packet_digest = sealed_packet.pop("content_sha256")
    sealed_index = dict(index)
    index_digest = sealed_index.pop("content_sha256")
    assert hashlib.sha256(canonical(sealed_packet)).hexdigest() == packet_digest
    assert hashlib.sha256(canonical(sealed_index)).hexdigest() == index_digest
    rows = packet["test_set"]
    assert hashlib.sha256(canonical(rows)).hexdigest() == packet["items_sha256"] == index["items_sha256"]
    assert len(rows) == 64 and len({row["item_id"] for row in rows}) == 64
    assert len({(row["english"], row["ainglish"]) for row in rows}) == 64
    assert Counter(row["form"] for row in rows) == Counter({"repeat-event": 32, "restore-state": 32})
    assert all(
        counts == {"repeat-event": 4, "restore-state": 4}
        for counts in packet["predicate_family_counts"].values()
    )
    for row in rows:
        assert row["event_clause"] in row["english"] and row["event_clause"] in row["ainglish"]
        if row["form"] == "repeat-event":
            assert row["ainglish"].startswith("repeat-event: ")
            assert "earlier" in row["english"] and "same" in row["english"]
        else:
            assert row["ainglish"].startswith(f"restore-state({row['result_state']}): ")
            assert "earlier interval" in row["english"] and "no earlier matching" in row["english"]
    print(json.dumps({
        "status": "ok",
        "pairs": 64,
        "form_counts": packet["form_counts"],
        "predicate_family_counts": packet["predicate_family_counts"],
        "items_sha256": packet["items_sha256"],
        "tokenizers_loaded": 0,
        "model_calls": 0,
        "governance_writes": 0,
    }, indent=2))


if __name__ == "__main__":
    main()

