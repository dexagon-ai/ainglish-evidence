#!/usr/bin/env python3
"""Fail-closed offline audit for the role-cardinality carrier."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
OPTIONS = ("yes", "no", "cannot tell")
DESIGNATED_SUCCESSORS = (
    REPO / "manifest-bound-flagship-carriers-v1-2026-08-27" / "role-cardinality.items.json",
    REPO / "manifest-bound-flagship-carriers-v1-2026-08-27" / "role-cardinality.template.json",
)


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    sealed = dict(value)
    expected = sealed.pop("content_sha256")
    assert hashlib.sha256(canonical(sealed)).hexdigest() == expected
    return value


def embedded_pairs(value: object, *, calibration: bool | None = None) -> set[tuple[str, str]]:
    found = set()
    stack = [value]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            calibration_matches = calibration is None or bool(current.get("calibration")) is calibration
            if calibration_matches and isinstance(current.get("english"), str) and isinstance(current.get("ainglish"), str):
                found.add((current["english"], current["ainglish"]))
            stack.extend(current.values())
        elif isinstance(current, list):
            stack.extend(current)
    return found


def prior_pairs(current_pairs: set[tuple[str, str]]) -> tuple[set[tuple[str, str]], list[dict]]:
    found = set()
    successors = []
    for path in REPO.rglob("*.json"):
        if ROOT in path.parents:
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        pairs = embedded_pairs(value)
        if path in DESIGNATED_SUCCESSORS:
            # These later artifacts deliberately bind the exact frozen population
            # to a manifest; they are descendants, not prior exposed test items.
            assert embedded_pairs(value, calibration=False) == current_pairs
            assert pairs - current_pairs == embedded_pairs(value, calibration=True)
            successors.append({
                "file": str(path.relative_to(REPO)),
                "pair_count": len(pairs),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            })
            continue
        found |= pairs
    assert {REPO / receipt["file"] for receipt in successors} == set(DESIGNATED_SUCCESSORS)
    return found, successors


def main() -> None:
    index = checked(ROOT / "index.json")
    packets = {}
    all_pairs = set()
    for name, receipt in index["campaigns"].items():
        packet = json.loads((ROOT / receipt["file"]).read_text(encoding="utf-8"))
        rows = packet["items"]
        assert hashlib.sha256(canonical(rows)).hexdigest() == packet["sha256"] == receipt["items_sha256"]
        scientific = [row for row in rows if not row.get("calibration")]
        calibration = [row for row in rows if row.get("calibration")]
        assert len(scientific) == receipt["scientific"] == 120
        assert len(calibration) == receipt["calibration"] == 8
        assert len({row["id"] for row in rows}) == 128
        assert {label: sum(row["answer"] == label for row in scientific) for label in OPTIONS} == receipt["answer_counts"] == {"yes": 40, "no": 40, "cannot tell": 40}
        assert {str(position): sum(row["options"].index(row["answer"]) == position for row in scientific) for position in range(3)} == receipt["answer_positions"] == {"0": 40, "1": 40, "2": 40}
        assert all(set(row["options"]) == set(OPTIONS) for row in scientific)
        assert all(row["form"] in row["ainglish"] for row in scientific)
        assert all(row["form"] not in row["question"] and row["form"] not in row["answer"] for row in scientific)
        assert {row["strata"]["cell"] for row in scientific} == set(range(12))
        assert {row["strata"]["role"] for row in scientific} and len({row["strata"]["role"] for row in scientific}) == 10
        assert {voice: sum(row["strata"]["voice"] == voice for row in scientific) for voice in ("active", "passive")} == {"active": 60, "passive": 60}
        assert sum(row["strata"]["stratum"] == "two-distinct-load-bearing" for row in scientific) == 10
        assert sum(row["strata"]["stratum"] == "additional-principal-load-bearing" for row in scientific) == 10
        assert sum(row["strata"]["stratum"] == "bounded-two-person-seam" for row in scientific) == 10
        assert sum(row["strata"]["stratum"] == "bounded-three-person-seam" for row in scientific) == 10
        pairs = {(row["english"], row["ainglish"]) for row in scientific}
        assert len(pairs) == 120 and not all_pairs & pairs
        all_pairs |= pairs
        packets[name] = scientific
    for comparison in ("bare", "careful"):
        left = {row["scenario_id"]: row for row in packets[f"one-or-more-vs-{comparison}"]}
        right = {row["scenario_id"]: row for row in packets[f"exactly-one-vs-{comparison}"]}
        assert set(left) == set(right)
        if comparison == "bare":
            assert all(left[key]["english"] == right[key]["english"] for key in left)
            assert all(left[key]["question"] == right[key]["question"] for key in left)
            opposite = [key for key in left if left[key]["answer"] != right[key]["answer"]]
            assert len(opposite) == 20
    exposed_pairs, successors = prior_pairs(all_pairs)
    overlap = all_pairs & exposed_pairs
    assert not overlap
    print(json.dumps({
        "status": "ok",
        "campaigns": 4,
        "scientific_items": 480,
        "calibrations": 32,
        "bare_hidden_world_opposite_answer_cells": 20,
        "prior_complete_pair_overlap": 0,
        "designated_content_preserving_successors": successors,
        "reader_calls": 0,
        "governance_writes": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
