#!/usr/bin/env python3
"""Fail-closed offline audit for the next-up / next-week carrier."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
FORMS = ("next-up", "next-week")
COMPARISONS = ("careful", "bare")


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def checked_index() -> dict:
    value = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    unsigned = dict(value)
    expected = unsigned.pop("content_sha256")
    assert hashlib.sha256(canonical(unsigned)).hexdigest() == expected
    return value


def embedded_pairs(value: object) -> set[tuple[str, str]]:
    found = set()
    stack = [value]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            if not current.get("calibration") and isinstance(current.get("english"), str) and isinstance(current.get("ainglish"), str):
                found.add((current["english"], current["ainglish"]))
            stack.extend(current.values())
        elif isinstance(current, list):
            stack.extend(current)
    return found


def prior_pair_overlap(current_pairs: set[tuple[str, str]]) -> tuple[int, int]:
    overlap = set()
    files = 0
    for path in REPO.rglob("*.json"):
        if ROOT in path.parents:
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        files += 1
        overlap |= current_pairs & embedded_pairs(value)
    return len(overlap), files


def main() -> None:
    index = checked_index()
    packets = {}
    all_pairs = set()
    for form in FORMS:
        for comparison in COMPARISONS:
            receipt = index["campaigns"][f"{form}-vs-{comparison}"]
            packet = json.loads((ROOT / receipt["file"]).read_text(encoding="utf-8"))
            rows = packet["items"]
            assert hashlib.sha256(canonical(rows)).hexdigest() == packet["sha256"] == receipt["items_sha256"]
            scientific = [row for row in rows if not row.get("calibration")]
            calibration = [row for row in rows if row.get("calibration")]
            assert len(scientific) == receipt["scientific"] == 196
            assert len(calibration) == receipt["calibration"] == 12
            assert len({row["id"] for row in rows}) == len(rows) == 208
            assert all(len(row["options"]) == len(set(row["options"])) == 4 for row in scientific)
            assert Counter(row["options"].index(row["answer"]) for row in scientific) == Counter({0: 49, 1: 49, 2: 49, 3: 49})
            assert Counter(row["strata"]["anchor_weekday"] for row in scientific) == Counter({day: 28 for day in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")})
            assert Counter(row["strata"]["target_weekday"] for row in scientific) == Counter({day: 28 for day in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")})
            assert Counter(row["strata"]["weekstart"] for row in scientific) == Counter({"Monday": 98, "Sunday": 98})
            assert sum(row["strata"]["constructors_diverge"] for row in scientific) == receipt["divergent"] == 84
            assert sum(not row["strata"]["constructors_diverge"] for row in scientific) == receipt["convergent"] == 112
            assert all(form in row["ainglish"] for row in scientific)
            assert all(form not in row["question"] and form not in row["answer"] for row in scientific)
            pairs = {(row["english"], row["ainglish"]) for row in scientific}
            assert len(pairs) == 196 and not pairs & all_pairs
            all_pairs |= pairs
            packets[f"{form}-vs-{comparison}"] = {row["scenario_id"]: row for row in scientific}

    for comparison in COMPARISONS:
        up = packets[f"next-up-vs-{comparison}"]
        week = packets[f"next-week-vs-{comparison}"]
        assert set(up) == set(week)
        if comparison == "bare":
            assert all(up[key]["english"] == week[key]["english"] for key in up)
            assert sum(up[key]["answer"] != week[key]["answer"] for key in up) == 84
            assert all((up[key]["answer"] != week[key]["answer"]) == up[key]["strata"]["constructors_diverge"] for key in up)

    for form in FORMS:
        receipt = index["nonclaim_diagnostics"][form]
        packet = json.loads((ROOT / receipt["file"]).read_text(encoding="utf-8"))
        rows = packet["items"]
        assert hashlib.sha256(canonical(rows)).hexdigest() == packet["sha256"] == receipt["items_sha256"]
        assert len(rows) == receipt["scientific"] == 70
        assert Counter(row["strata"]["property"] for row in rows) == Counter({
            "time_of_day": 14, "timezone": 14, "recurrence": 14,
            "deadline_inclusion": 14, "business_day_adjustment": 14,
        })
        assert all(row["answer"] in {"yes", "no"} and "cannot tell" in row["options"] for row in rows)
        assert all(form in row["ainglish"] for row in rows)

    overlap, files = prior_pair_overlap(all_pairs)
    assert overlap == 0
    print(json.dumps({
        "status": "ok", "primary_campaigns": 4, "primary_scientific_items": 784,
        "construct_free_calibrations": 48, "secondary_nonclaim_items": 140,
        "divergent_hidden_world_cells_per_bare_campaign_pair": 84,
        "prior_complete_pair_overlap": overlap, "prior_json_files_scanned": files,
        "reader_calls": 0, "governance_writes": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
