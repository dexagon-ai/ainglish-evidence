#!/usr/bin/env python3
"""Independent structural and numeric audit of the group-scope carrier."""

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


def truth(table: dict, direction: str) -> tuple[bool, bool]:
    compare = (lambda before, after: after > before) if direction == "increased" else (lambda before, after: after < before)
    per_group = []
    for values in table.values():
        assert 0 <= values["before_success"] <= values["before_total"]
        assert 0 <= values["after_success"] <= values["after_total"]
        per_group.append(
            compare(
                values["before_success"] / values["before_total"],
                values["after_success"] / values["after_total"],
            )
        )
    before_success = sum(values["before_success"] for values in table.values())
    before_total = sum(values["before_total"] for values in table.values())
    after_success = sum(values["after_success"] for values in table.values())
    after_total = sum(values["after_total"] for values in table.values())
    return all(per_group), compare(before_success / before_total, after_success / after_total)


def prior_complete_triples() -> set[tuple[str, str, str]]:
    found: set[tuple[str, str, str]] = set()
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
                if all(isinstance(current.get(key), str) for key in ("ainglish", "question", "answer")):
                    found.add((current["ainglish"], current["question"], current["answer"]))
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
    assert hashlib.sha256(canonical(rows)).hexdigest() == packet["items_sha256"] == index["items_sha256"]
    templates_packet = json.loads((ROOT / index["templates_path"]).read_text(encoding="utf-8"))
    assert hashlib.sha256(canonical(templates_packet["templates"])).hexdigest() == templates_packet["templates_sha256"] == index["templates_sha256"]
    assert len(rows) == 192 and len({row["item_id"] for row in rows}) == 192
    assert index["forms"] == {form: sum(row["form"] == form for row in rows) for form in ("each-group", "groups-combined")} == {"each-group": 96, "groups-combined": 96}
    assert {row["direction"] for row in rows} == {"increased", "decreased"}
    assert {probe: sum(row["probe"] == probe for row in rows) for probe in ("member_same", "member_opposite_compatible", "aggregate_opposite")} == {probe: 64 for probe in ("member_same", "member_opposite_compatible", "aggregate_opposite")}
    assert {answer: sum(row["answer"] == answer for row in rows) for answer in ("yes", "no", "not stated")} == {answer: 64 for answer in ("yes", "no", "not stated")}
    assert [sum(row["options"].index(row["answer"]) == position for row in rows) for position in range(3)] == [64, 64, 64]
    assert all(set(row["options"]) == {"yes", "no", "not stated"} for row in rows)
    for row in rows:
        each, combined = truth(row["hidden_table"], row["direction"])
        assert row["derived_truth"] == {"each_group": each, "groups_combined": combined}
        assert each if row["form"] == "each-group" else combined
        assert row["hidden_table_exposed_to_reader"] is False
    pairs = {}
    for row in rows:
        pairs.setdefault(row["scenario_id"], []).append(row)
    assert len(pairs) == 96 and all(len(pair) == 2 for pair in pairs.values())
    assert all(pair[0]["bare"] == pair[1]["bare"] for pair in pairs.values())
    assert all(pair[0]["question"] == pair[1]["question"] for pair in pairs.values())
    assert all({row["form"] for row in pair} == {"each-group", "groups-combined"} for pair in pairs.values())
    current = {(row["ainglish"], row["question"], row["answer"]) for row in rows}
    assert not current & prior_complete_triples()
    print(
        json.dumps(
            {
                "status": "ok",
                "items": 192,
                "forms": index["forms"],
                "answer_labels": {answer: 64 for answer in ("yes", "no", "not stated")},
                "answer_positions": [64, 64, 64],
                "paired_identical_bare_surfaces": 96,
                "numeric_truths_rederived": 192,
                "prior_exact_answer_triple_overlap": 0,
                "templates": 4,
                "model_calls": 0,
                "governance_writes": 0,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
