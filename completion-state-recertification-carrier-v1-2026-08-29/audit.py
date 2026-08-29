#!/usr/bin/env python3
"""Fail closed on the completion-state carrier's frozen design."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FORMS = {"stopped", "done-under", "complete-for"}
ARMS = {"ainglish", "bare_english", "careful_english"}


def canonical_hash(value: dict) -> str:
    payload = dict(value)
    payload.pop("sha256", None)
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def check_packet(path: Path, expected_condition: str) -> dict:
    packet = json.loads(path.read_text(encoding="utf-8"))
    assert packet["sha256"] == canonical_hash(packet)
    assert packet["condition"] == expected_condition
    rows = packet["scientific_rows"]
    assert len(rows) == 60
    assert len(packet["calibration_rows"]) == 8
    assert Counter(row["form"] for row in rows) == {form: 20 for form in FORMS}
    assert len({row["id"] for row in rows}) == 60
    assert len({row["context_id"] for row in rows}) == 20
    assert all(set(row["arms"]) == ARMS for row in rows)
    assert all([q["id"] for q in row["questions"]] == ["claim_type", "licensed_action"] for row in rows)
    assert all(len(set(q["options"])) == 3 and q["answer"] in q["options"] for row in rows for q in row["questions"])

    by_context = {}
    for row in rows:
        by_context.setdefault(row["context_id"], []).append(row)
    assert all({row["form"] for row in group} == FORMS for group in by_context.values())
    assert all(len({row["arms"]["bare_english"] for row in group}) == 1 for group in by_context.values())

    if expected_condition == "zero_shot":
        assert packet["reference_card"] is None
        assert all(not value.startswith("Reference:") for row in rows for value in row["arms"].values())
    else:
        reference = packet["reference_card"]
        assert reference
        assert all(value.startswith(reference + "\nMessage: ") for row in rows for value in row["arms"].values())

    answer_positions = Counter()
    for row in rows:
        for q in row["questions"]:
            answer_positions[(q["id"], q["options"].index(q["answer"]))] += 1
    assert answer_positions == {
        ("claim_type", 0): 20,
        ("claim_type", 1): 20,
        ("claim_type", 2): 20,
        ("licensed_action", 0): 20,
        ("licensed_action", 1): 20,
        ("licensed_action", 2): 20,
    }
    return {
        "file": path.name,
        "sha256": packet["sha256"],
        "scientific_rows": len(rows),
        "calibration_rows": len(packet["calibration_rows"]),
        "forms": dict(sorted(Counter(row["form"] for row in rows).items())),
        "answer_positions": {f"{q}:{pos}": count for (q, pos), count in sorted(answer_positions.items())},
    }


def main() -> None:
    result = {
        "kind": "dexagon.ainglish.completion-state-recertification-audit.v1",
        "status": "passed",
        "packets": [
            check_packet(ROOT / "zero-shot.json", "zero_shot"),
            check_packet(ROOT / "definition-conditioned.json", "definition_conditioned"),
        ],
        "model_calls": 0,
        "governance_writes": 0,
    }
    (ROOT / "audit.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
