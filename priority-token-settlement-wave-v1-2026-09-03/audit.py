#!/usr/bin/env python3
"""Offline audit of three unspent legacy-contract successor carriers."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

from carriers import CAMPAIGNS


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    pairs: set[tuple[str, str]] = set()
    arms: set[str] = set()
    report = {}
    for key, campaign in CAMPAIGNS.items():
        items = campaign["items"]
        assert len(items) == 16
        assert len({row["id"] for row in items}) == 16
        current_pairs = {(row["english"], row["ainglish"]) for row in items}
        current_arms = {arm for row in items for arm in (row["english"], row["ainglish"])}
        assert len(current_pairs) == 16
        assert not pairs & current_pairs
        assert not arms & current_arms
        assert all(row["english"].strip() and row["ainglish"].strip() for row in items)
        pairs |= current_pairs
        arms |= current_arms
        report[key] = {
            "slug": campaign["slug"],
            "legacy_target": campaign["target"],
            "items": len(items),
            "strata": dict(sorted(Counter(row.get("stratum", "single") for row in items).items())),
            "carrier_sha256": hashlib.sha256(canonical(items)).hexdigest(),
            "model_calls": 0,
            "governance_writes": 0,
        }
    result = {"status": "passed-unspent-author-repair-handoff", "campaigns": report}
    rendered = json.dumps(result, indent=2) + "\n"
    target = Path(__file__).resolve().parent / "audit.json"
    if target.exists() and target.read_text(encoding="utf-8") != rendered:
        raise SystemExit("REFUSING: frozen audit drift")
    if not target.exists():
        target.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
