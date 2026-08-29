#!/usr/bin/env python3
"""Fail closed on balance, pairing, hashes, and condition separation."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FILES = [
    "pronoun-zero-shot.json",
    "pronoun-definition-conditioned.json",
    "negation-zero-shot.json",
    "negation-definition-conditioned.json",
]


def digest(value: object) -> str:
    payload = dict(value)
    payload.pop("content_sha256", None)
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def near_balanced(counter: Counter) -> bool:
    return max(counter.values()) - min(counter.values()) <= 1


def base_message(packet: dict, value: str) -> str:
    reference = packet["reference_card"]
    if reference is None:
        return value
    prefix = reference + "\nMessage: "
    assert value.startswith(prefix)
    return value[len(prefix):]


def check(packet: dict) -> dict:
    assert packet["content_sha256"] == digest(packet)
    rows = packet["scientific_rows"]
    assert len(rows) == 160 and len(packet["calibration_rows"]) == 12
    assert len({row["id"] for row in rows}) == 160
    assert len({row["context_id"] for row in rows}) == 80
    assert all(set(row["arms"]) == {"ainglish", "bare_english", "careful_english"} for row in rows)
    by_context = {}
    for row in rows:
        by_context.setdefault(row["context_id"], []).append(row)
    assert all(len(group) == 2 for group in by_context.values())
    assert all(len({base_message(packet, row["arms"]["bare_english"]) for row in group}) == 1 for group in by_context.values())
    assert all(len({base_message(packet, row["arms"]["ainglish"]) for row in group}) == 2 for group in by_context.values())
    positions = Counter()
    for row in rows:
        for q in row["questions"]:
            assert len(q["options"]) == 3 and len(set(q["options"])) == 3 and q["answer"] in q["options"]
            positions[q["id"], q["options"].index(q["answer"])] += 1
    for qid in {key[0] for key in positions}:
        assert near_balanced(Counter({pos: positions[qid, pos] for pos in range(3)}))
    if packet["proposal_slug"] == "it-ref":
        assert Counter(row["intended_antecedent_position"] for row in rows) == {1: 80, 2: 80}
        assert all("it(" in base_message(packet, row["arms"]["ainglish"]) for row in rows)
    else:
        assert Counter(row["form"] for row in rows) == {"none-of": 80, "not-all-of": 80}
        assert all(row["set_size"] in range(2, 9) for row in rows)
        for row in rows:
            answer = next(q["answer"] for q in row["questions"] if q["id"] == "zero_satisfiers")
            assert answer == "yes"
    return {
        "proposal_slug": packet["proposal_slug"],
        "condition": packet["condition"],
        "scientific_rows": 160,
        "calibration_rows": 12,
        "content_sha256": packet["content_sha256"],
    }


def main() -> None:
    packets = [json.loads((ROOT / name).read_text(encoding="utf-8")) for name in FILES]
    results = [check(packet) for packet in packets]
    for slug in {packet["proposal_slug"] for packet in packets}:
        zero = next(packet for packet in packets if packet["proposal_slug"] == slug and packet["condition"] == "zero_shot")
        loaded = next(packet for packet in packets if packet["proposal_slug"] == slug and packet["condition"] == "definition_conditioned")
        zero_messages = {base_message(zero, value) for row in zero["scientific_rows"] for value in row["arms"].values()}
        loaded_messages = {base_message(loaded, value) for row in loaded["scientific_rows"] for value in row["arms"].values()}
        assert zero_messages.isdisjoint(loaded_messages)
    audit = {
        "kind": "dexagon.ainglish.new-language-comprehension-carrier-audit.v1",
        "status": "passed",
        "packets": results,
        "zero_vs_definition_exact_message_overlap": 0,
        "model_calls": 0,
        "governance_writes": 0,
    }
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
