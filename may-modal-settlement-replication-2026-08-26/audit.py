#!/usr/bin/env python3
"""Audit the frozen may-force carrier without opening the target item block."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def triples(value: object):
    if isinstance(value, dict):
        if all(key in value for key in ("english", "ainglish", "question")):
            yield (str(value["english"]), str(value["ainglish"]), str(value["question"]))
        for child in value.values():
            yield from triples(child)
    elif isinstance(value, list):
        for child in value:
            yield from triples(child)


def main() -> None:
    snapshot = json.loads((ROOT / "snapshot.json").read_text(encoding="utf-8"))
    index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    packet = json.loads((ROOT / index["items_path"]).read_text(encoding="utf-8"))
    sealed_snapshot = dict(snapshot)
    assert hashlib.sha256(canonical({key: value for key, value in sealed_snapshot.items() if key != "content_sha256"})).hexdigest() == snapshot["content_sha256"]
    sealed_index = dict(index); expected_index = sealed_index.pop("content_sha256")
    assert hashlib.sha256(canonical(sealed_index)).hexdigest() == expected_index
    rows = packet["items"]
    assert hashlib.sha256(canonical(rows)).hexdigest() == packet["sha256"] == index["items_sha256"]
    scientific = [row for row in rows if not row.get("calibration")]
    calibration = [row for row in rows if row.get("calibration")]
    assert len(scientific) == 160 and len(calibration) == 8
    assert len({(row["english"], row["ainglish"], row["question"]) for row in scientific}) == 160
    assert Counter(row["form"] for row in scientific) == Counter({"may-as-permission": 80, "may-as-possibility": 80})
    assert Counter(row["voice"] for row in scientific) == Counter({"active": 80, "passive": 80})
    assert Counter(row["options"].index(row["answer"]) for row in scientific) == Counter({0: 40, 1: 40, 2: 40, 3: 40})
    assert all(row["answer"] in row["options"] and len(set(row["options"])) == 4 for row in rows)
    assert all("may-as-" not in row["question"] and not any("may-as-" in option for option in row["options"]) for row in scientific)
    assert all(row["english"] != row["ainglish"] for row in rows)
    prior = set()
    for path in REPO.rglob("*.json"):
        if ROOT in path.parents:
            continue
        try:
            prior.update(triples(json.loads(path.read_text(encoding="utf-8"))))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
    current = {(row["english"], row["ainglish"], row["question"]) for row in scientific}
    assert not current & prior
    planned = snapshot["target_original"]["planned_sample"]
    for key, value in index["planned_sample"].items():
        assert planned.get(key) == value
    report = {
        "status": "ok",
        "scientific_items": 160,
        "calibration_items": 8,
        "forms": {"may-as-permission": 80, "may-as-possibility": 80},
        "answer_positions": {str(key): value for key, value in sorted(Counter(row["options"].index(row["answer"]) for row in scientific).items())},
        "repository_exact_triple_overlap": 0,
        "target_answer_bearing_block_opened": False,
        "model_calls": 0,
        "governance_writes": 0,
        "content_sha256": index["content_sha256"],
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

