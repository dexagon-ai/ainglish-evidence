#!/usr/bin/env python3
"""Audit the candidate funnel and its two selected flagship candidates."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(name: str) -> dict:
    value = json.loads((ROOT / name).read_text())
    sealed = dict(value)
    expected = sealed.pop("content_sha256")
    assert hashlib.sha256(canonical(sealed)).hexdigest() == expected
    return value


def main() -> None:
    register = checked("register-snapshot.json")
    census = checked("census.json")
    assert register["count"] == len(register["proposals"]) >= 195
    assert census["register_snapshot_sha256"] == register["content_sha256"]
    assert census["selected"] == ["explicit-pronoun-referent", "universal-negation-scope"]
    exact_forms = {str(row.get("form") or "").lower() for row in register["proposals"]}
    for row in census["candidates"]:
        assert len(row["checks"]) == 5
        assert row["editorial_score"] == sum(row["checks"])
        assert row["decision"] in {"select", "hold", "reject-neighbor"}
        assert row["proposed_form"].lower() not in exact_forms
        if row["decision"] == "select":
            assert row["editorial_score"] == 5
            assert row["seam"] and row["top_lexical_neighbors"]
    assert census["model_calls"] == 0 and census["governance_writes"] == 0
    print("audit ok: full register screened, ten candidates triaged, two five-of-five gaps selected")


if __name__ == "__main__":
    main()
