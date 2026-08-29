#!/usr/bin/env python3
"""Fail closed on clusivity carrier structure, binding, and exact novelty."""

from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
FORMS = {"we-including-you", "we-excluding-you"}
ARMS = {"ainglish", "bare_english", "careful_english"}
QUESTIONS = ["addressee_membership", "routed_consequence", "outsider_overread"]


def canonical_hash(value: dict) -> str:
    material = copy.deepcopy(value)
    material.pop("sha256", None)
    return hashlib.sha256(json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def prior_messages() -> tuple[set[str], int]:
    messages: set[str] = set()
    files = 0
    for path in REPO.rglob("*.json"):
        if ROOT == path.parent or ROOT in path.parents:
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        files += 1
        stack = [value]
        while stack:
            current = stack.pop()
            if isinstance(current, dict):
                if isinstance(current.get("arms"), dict):
                    messages.update(item for item in current["arms"].values() if isinstance(item, str))
                if isinstance(current.get("message"), str):
                    messages.add(current["message"])
                stack.extend(current.values())
            elif isinstance(current, list):
                stack.extend(current)
    return messages, files


def check_packet(path: Path, condition: str, prior: set[str]) -> tuple[dict, set[str]]:
    packet = json.loads(path.read_text(encoding="utf-8"))
    assert packet["sha256"] == canonical_hash(packet)
    assert packet["condition"] == condition
    rows = packet["scientific_rows"]
    assert len(rows) == 160 and len({row["id"] for row in rows}) == 160
    assert len(packet["calibration_rows"]) == 12
    assert Counter(row["form"] for row in rows) == {form: 80 for form in FORMS}
    assert len({row["context_id"] for row in rows}) == 80
    assert all(set(row["arms"]) == ARMS for row in rows)
    assert all([question["id"] for question in row["questions"]] == QUESTIONS for row in rows)
    assert all(len(set(question["options"])) == 3 and question["answer"] in question["options"] for row in rows for question in row["questions"])
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row["context_id"], []).append(row)
    assert all(len(group) == 2 and {row["form"] for row in group} == FORMS for group in grouped.values())
    assert all(len({row["arms"]["bare_english"] for row in group}) == 1 for group in grouped.values())
    assert all(len({row["questions"][0]["answer"] for row in group}) == 2 for group in grouped.values())
    assert all(len({row["questions"][1]["answer"] for row in group}) == 2 for group in grouped.values())
    if condition == "zero_shot":
        assert packet["reference_card"] is None
        assert all(not arm.startswith("Reference:") for row in rows for arm in row["arms"].values())
    else:
        reference = packet["reference_card"]
        assert reference
        assert all(arm.startswith(reference + "\nMessage: ") for row in rows for arm in row["arms"].values())
    positions = Counter()
    for row in rows:
        for question in row["questions"]:
            positions[(question["id"], question["options"].index(question["answer"]))] += 1
    assert all(max(positions[(question, position)] for position in range(3)) - min(positions[(question, position)] for position in range(3)) <= 1 for question in QUESTIONS)
    arm_messages = [arm for row in rows for arm in row["arms"].values()]
    unique_messages = set(arm_messages)
    intended_bare_duplicates = 80
    assert len(arm_messages) - len(unique_messages) == intended_bare_duplicates
    overlaps = sorted(unique_messages & prior)
    assert not overlaps, f"prior exact message overlap: {overlaps[:3]}"
    return ({
        "file": path.name,
        "sha256": packet["sha256"],
        "scientific_rows": len(rows),
        "calibration_rows": len(packet["calibration_rows"]),
        "forms": dict(sorted(Counter(row["form"] for row in rows).items())),
        "contexts": len(grouped),
        "frames": dict(sorted(Counter(row["strata"]["frame"] for row in rows).items())),
        "answer_positions": {f"{question}:{position}": positions[(question, position)] for question in QUESTIONS for position in range(3)},
        "intentional_within-context_bare_duplicates": intended_bare_duplicates,
        "prior_exact_message_overlap": 0,
    }, unique_messages)


def main() -> None:
    prior, files = prior_messages()
    zero, zero_messages = check_packet(ROOT / "zero-shot.json", "zero_shot", prior)
    conditioned, conditioned_messages = check_packet(ROOT / "definition-conditioned.json", "definition_conditioned", prior)
    assert not (zero_messages & conditioned_messages)
    report = {
        "kind": "dexagon.ainglish.clusivity-recertification-audit.v1",
        "status": "passed",
        "packets": [zero, conditioned],
        "prior_json_files_scanned": files,
        "cross_condition_exact_message_overlap": 0,
        "scientific_rows_total": 320,
        "scientific_arm_messages_total": 960,
        "model_calls": 0,
        "network_calls": 0,
        "governance_writes": 0,
    }
    target = ROOT / "audit.json"
    rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if target.exists() and target.read_text(encoding="utf-8") != rendered:
        raise SystemExit("REFUSING: frozen audit drift")
    if not target.exists():
        target.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
