#!/usr/bin/env python3
"""Offline audit for the controlled moved-direction fidelity carrier."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    sealed = dict(value)
    expected = sealed.pop("content_sha256")
    assert hashlib.sha256(canonical(sealed)).hexdigest() == expected
    return value


def prior_cases() -> set[tuple[str, str, str]]:
    found = set()
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
                if all(key in current for key in ("source_event", "proposition", "instruction")):
                    found.add((str(current["source_event"]), str(current["proposition"]), str(current["instruction"])))
                stack.extend(current.values())
            elif isinstance(current, list):
                stack.extend(current)
    return found


def main() -> None:
    snapshot = checked(ROOT / "proposal-snapshot.json")
    index = checked(ROOT / "index.json")
    assert index["proposal_snapshot_sha256"] == snapshot["content_sha256"]
    packet = json.loads((ROOT / index["items_path"]).read_text(encoding="utf-8"))
    rows = packet["items"]
    assert hashlib.sha256(canonical(rows)).hexdigest() == packet["sha256"] == index["items_sha256"]
    assert len(rows) == 96 and len({row["id"] for row in rows}) == 96
    assert {name: sum(row["class"] == name for row in rows) for name in ("earlier", "later", "neither")} == index["classes"]
    assert [sum(row["options"].index(row["answer"]) == position for row in rows) for position in range(3)] == [32, 32, 32]
    assert all(set(row["options"]) == {"moved-earlier", "moved-later", "neither tag is warranted"} for row in rows)
    current = {(row["source_event"], row["proposition"], row["instruction"]) for row in rows}
    assert not current & prior_cases()
    print(json.dumps({"status": "ok", "cases": 96, "class_counts": index["classes"], "answer_positions": [32, 32, 32], "prior_exact_case_overlap": 0, "model_calls": 0, "governance_writes": 0}, indent=2))


if __name__ == "__main__":
    main()
