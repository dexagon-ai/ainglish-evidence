#!/usr/bin/env python3
"""Fail closed on source pins, cross-over balance, disjointness, and run-plan drift."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
ATLAS = REPO / "flagship-cold-clarity-atlas-v1-2026-08-29"
GROUPS = {"a": {"list_completeness", "pronoun_number", "claim_source"}, "b": {"role_cardinality", "event_or_state_recurrence", "failure_contract"}}
TWO_POLES = {
    "list_completeness": {"among_others", "and_no_others"},
    "role_cardinality": {"one_or_more", "exactly_one"},
    "event_or_state_recurrence": {"repeat_event", "restore_state"},
    "pronoun_number": {"they_one", "they_many"},
    "failure_contract": {"attempt", "ensure"},
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def user_text(row: dict) -> str:
    messages = row["messages"]
    user = [message["content"] for message in messages if message["role"] == "user"]
    if len(user) != 1:
        raise ValueError(f"{row['id']}: expected one user message")
    return user[0]


def main() -> None:
    failures = []
    plan = json.loads((ROOT / "RUN_PLAN.json").read_text(encoding="utf-8"))
    pins = json.loads((ROOT / "source-pins.json").read_text(encoding="utf-8"))
    train = {group: rows(ROOT / f"train-{group}.jsonl") for group in GROUPS}
    evaluation = rows(ROOT / "eval.jsonl")

    if pins["source_constructs_sha256"] != digest(ATLAS / "constructs.json") or pins["source_proposal_snapshot_sha256"] != digest(ATLAS / "proposal-snapshot.json"):
        failures.append("source atlas drift")
    if {row["key"] for row in pins["constructs"]} != set().union(*GROUPS.values()):
        failures.append("source construct population drift")
    train_vocab = pins.get("training_vocabulary", {})
    eval_vocab = pins.get("evaluation_vocabulary", {})
    for field in ("roles", "actors", "objects", "kinds", "sources", "bases", "role_actions", "pronoun_actions"):
        if set(train_vocab.get(field, [])) & set(eval_vocab.get(field, [])):
            failures.append(f"training/evaluation vocabulary overlap: {field}")
    for field in ("events", "failure_actions"):
        train_flat = {part for row in train_vocab.get(field, []) for part in row}
        eval_flat = {part for row in eval_vocab.get(field, []) for part in row}
        if train_flat & eval_flat:
            failures.append(f"training/evaluation tuple vocabulary overlap: {field}")
    if plan.get("downloads") != 0 or plan.get("governance_evidence") is not False or plan.get("development_only") is not True:
        failures.append("claim/download boundary drift")
    if plan["training"]["rows_per_adapter"] != 1800 or plan["evaluation"]["prompts_per_condition"] != 864 or plan["evaluation"]["planned_predictions"] != 2592:
        failures.append("plan population drift")

    all_ids = []
    train_user_texts = set()
    for group, group_rows in train.items():
        if len(group_rows) != 1800:
            failures.append(f"group {group}: expected 1800 rows")
        counts = Counter(row["key"] for row in group_rows)
        if counts != Counter({key: 600 for key in GROUPS[group]}):
            failures.append(f"group {group}: construct balance drift {dict(counts)}")
        for row in group_rows:
            all_ids.append(row["id"])
            if row["group"] != group or row["key"] not in GROUPS[group]:
                failures.append(f"{row['id']}: cross-over assignment drift")
            messages = row["messages"]
            if [message["role"] for message in messages] != ["system", "user", "assistant"]:
                failures.append(f"{row['id']}: training chat shape drift")
                continue
            try:
                answer = json.loads(messages[-1]["content"])
            except json.JSONDecodeError:
                failures.append(f"{row['id']}: invalid assistant JSON")
                continue
            if set(answer) != {"answer"} or answer["answer"] != row["expected"]:
                failures.append(f"{row['id']}: assistant/expected mismatch")
            labels = {option["label"] for option in row["options"]}
            if row["expected"] not in labels or len(labels) != len(row["options"]):
                failures.append(f"{row['id']}: option contract drift")
            train_user_texts.add(user_text(row))
        for key in GROUPS[group]:
            subset = [row for row in group_rows if row["key"] == key]
            label_counts = Counter(row["expected"] for row in subset)
            expected_each = 150 if key == "claim_source" else 200
            if set(label_counts.values()) != {expected_each}:
                failures.append(f"group {group}/{key}: answer positions unbalanced {dict(label_counts)}")
            poles = Counter(row["pole"] for row in subset)
            expected_poles = {pole: (200 if key == "claim_source" else 300) for pole in ({"observed", "reported", "inferred"} if key == "claim_source" else TWO_POLES[key])}
            if poles != Counter(expected_poles):
                failures.append(f"group {group}/{key}: pole balance drift {dict(poles)}")

    if len(evaluation) != 864:
        failures.append("evaluation row count drift")
    eval_groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    eval_user_texts = set()
    for row in evaluation:
        all_ids.append(row["id"])
        eval_groups[(row["key"], row["condition"])].append(row)
        if [message["role"] for message in row["messages"]] != ["system", "user"]:
            failures.append(f"{row['id']}: evaluation chat shape drift")
        labels = {option["label"] for option in row["options"]}
        if row["expected"] not in labels or len(labels) != len(row["options"]):
            failures.append(f"{row['id']}: evaluation option contract drift")
        if row["condition"] == "bare_english" and row["expected_semantic"] != "unspecified":
            failures.append(f"{row['id']}: bare arm has hidden answer")
        eval_user_texts.add(user_text(row))
    expected_keys = {(key, condition) for key in set().union(*GROUPS.values()) for condition in ("ainglish_cold", "careful_english", "bare_english")}
    if set(eval_groups) != expected_keys:
        failures.append("evaluation construct/arm matrix drift")
    for (key, condition), subset in eval_groups.items():
        if len(subset) != 48:
            failures.append(f"{key}/{condition}: expected 48 rows")
        expected_each = 12 if key == "claim_source" else 16
        positions = Counter(row["expected"] for row in subset)
        if set(positions.values()) != {expected_each}:
            failures.append(f"{key}/{condition}: answer positions unbalanced {dict(positions)}")
        poles = Counter(row["pole"] for row in subset)
        expected_poles = {pole: (16 if key == "claim_source" else 24) for pole in ({"observed", "reported", "inferred"} if key == "claim_source" else TWO_POLES[key])}
        if poles != Counter(expected_poles):
            failures.append(f"{key}/{condition}: pole balance drift {dict(poles)}")
    if len(all_ids) != len(set(all_ids)):
        failures.append("duplicate row IDs")
    overlap = train_user_texts & eval_user_texts
    if overlap:
        failures.append(f"exact train/evaluation user-message overlap: {list(overlap)[:3]}")

    for filename, record in plan["outputs"].items():
        path = ROOT / filename
        if not path.is_file() or digest(path) != record["sha256"]:
            failures.append(f"plan output digest drift: {filename}")
        if "rows" in record and len(rows(path)) != record["rows"]:
            failures.append(f"plan output count drift: {filename}")
    if failures:
        raise SystemExit("REFUSING:\n- " + "\n- ".join(failures))
    print(json.dumps({
        "ok": True, "training_rows": {group: len(value) for group, value in train.items()},
        "evaluation_rows": len(evaluation), "unique_ids": len(all_ids),
        "exact_train_eval_user_message_overlap": len(overlap),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
