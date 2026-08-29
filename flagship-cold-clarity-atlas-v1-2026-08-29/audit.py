#!/usr/bin/env python3
"""Fail closed on population, arm, answer, prompt, roster, and novelty drift."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
CONDITIONS = {"ainglish_cold", "ainglish_defined", "careful_english", "bare_english", "corrupted_ainglish"}
EXPECTED_POLES = {
    "list_completeness": Counter({"among_others": 4, "and_no_others": 4}),
    "role_cardinality": Counter({"one_or_more": 4, "exactly_one": 4}),
    "event_or_state_recurrence": Counter({"repeat_event": 4, "restore_state": 4}),
    "pronoun_number": Counter({"they_one": 4, "they_many": 4}),
    "claim_source": Counter({"observed": 3, "reported": 3, "inferred": 2}),
    "failure_contract": Counter({"attempt": 4, "ensure": 4}),
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    proposals = json.loads((ROOT / "proposal-snapshot.json").read_text(encoding="utf-8"))["proposals"]
    roster = json.loads((ROOT / "reader-roster.json").read_text(encoding="utf-8"))["readers"]
    constructs = json.loads((ROOT / "constructs.json").read_text(encoding="utf-8"))["constructs"]
    packet = json.loads((ROOT / "items.json").read_text(encoding="utf-8"))
    items = packet["items"]
    prompts = jsonl(ROOT / "prompts.jsonl")
    plan = json.loads((ROOT / "RUN_PLAN.json").read_text(encoding="utf-8"))
    failures: list[str] = []

    if len(proposals) != 6 or len(constructs) != 6 or len(roster) != 6 or len(items) != 240 or len(prompts) != 30:
        failures.append("population counts drifted")
    if len({row["slug"] for row in proposals}) != 6 or {row["slug"] for row in proposals} != {row["slug"] for row in constructs}:
        failures.append("proposal population mismatch")
    if any(not row.get("form") or not row.get("english_mapping") for row in proposals):
        failures.append("proposal reference text missing")
    families = [row.get("details", {}).get("family") for row in roster]
    if len(set(families)) != 6 or any(not family for family in families):
        failures.append("reader families are not six distinct declared values")
    if len({row.get("digest") for row in roster}) != 6 or any(len(str(row.get("digest", ""))) != 64 for row in roster):
        failures.append("reader digests missing or duplicated")

    ids = [row["id"] for row in items]
    if len(ids) != len(set(ids)):
        failures.append("duplicate item IDs")
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    by_frame: dict[tuple[str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in items:
        grouped[(row["key"], row["condition"])].append(row)
        by_frame[(row["key"], row["frame_id"])][row["condition"]] = row
        if row["condition"] not in CONDITIONS or row.get("development_only") is not True:
            failures.append(f"{row['id']}: condition/development boundary drift")
        labels = [option["label"] for option in row["options"]]
        semantics = [option["semantic"] for option in row["options"]]
        if len(labels) != len(set(labels)) or labels != [chr(65 + index) for index in range(len(labels))]:
            failures.append(f"{row['id']}: option labels malformed")
        if len(semantics) != len(set(semantics)) or row["expected"] not in labels:
            failures.append(f"{row['id']}: option semantics/expected label malformed")
        resolved = next(option["semantic"] for option in row["options"] if option["label"] == row["expected"])
        if resolved != row["expected_semantic"]:
            failures.append(f"{row['id']}: expected label does not bind expected semantic")
        if row["condition"] == "bare_english" and row["expected_semantic"] != "unspecified":
            failures.append(f"{row['id']}: bare arm assigned hidden pole")
        if row["condition"] != "bare_english" and row["expected_semantic"] == "unspecified":
            failures.append(f"{row['id']}: determinate arm assigned unspecified")
    if set(grouped) != {(key, condition) for key in EXPECTED_POLES for condition in CONDITIONS}:
        failures.append("construct/condition matrix incomplete")
    for (key, condition), rows in grouped.items():
        if len(rows) != 8 or Counter(row["pole"] for row in rows) != EXPECTED_POLES[key]:
            failures.append(f"{key}/{condition}: count or pole balance drift")
        label_counts = Counter(row["expected"] for row in rows)
        if max(label_counts.values()) - min(label_counts.values()) > 3:
            failures.append(f"{key}/{condition}: excessive answer-position imbalance {dict(label_counts)}")
    for (key, frame_id), arms in by_frame.items():
        if set(arms) != CONDITIONS:
            failures.append(f"{key}/{frame_id}: incomplete arm set")
            continue
        if arms["ainglish_cold"]["message"] != arms["ainglish_defined"]["message"]:
            failures.append(f"{key}/{frame_id}: cold/defined message bytes differ")
        canonical = arms["ainglish_cold"]["message"]
        for condition in ("careful_english", "bare_english", "corrupted_ainglish"):
            if arms[condition]["message"] == canonical:
                failures.append(f"{key}/{frame_id}: {condition} does not alter the message")
        target = arms["ainglish_cold"]["expected_semantic"]
        for condition in ("ainglish_defined", "careful_english", "corrupted_ainglish"):
            if arms[condition]["expected_semantic"] != target:
                failures.append(f"{key}/{frame_id}: meaning-matched arm changed target")

    prompt_keys = [(row["key"], row["condition"]) for row in prompts]
    if len(prompt_keys) != len(set(prompt_keys)) or set(prompt_keys) != set(grouped):
        failures.append("prompt matrix mismatch")
    for prompt in prompts:
        rows = grouped[(prompt["key"], prompt["condition"])]
        if set(prompt["item_ids"]) != {row["id"] for row in rows} or len(prompt["item_ids"]) != 8:
            failures.append(f"{prompt['key']}/{prompt['condition']}: prompt item population mismatch")
        if hashlib.sha256(prompt["prompt"].encode()).hexdigest() != prompt["prompt_sha256"]:
            failures.append(f"{prompt['key']}/{prompt['condition']}: prompt digest mismatch")
        has_card = "AUTHORITATIVE REFERENCE CARD FOR THIS BATCH:" in prompt["prompt"]
        if has_card != (prompt["condition"] == "ainglish_defined"):
            failures.append(f"{prompt['key']}/{prompt['condition']}: definition-card isolation failure")

    expected_plan = {"constructs": 6, "conditions": 5, "readers": 6, "calls_per_reader": 30, "planned_calls": 180, "planned_cells": 1440, "downloads": 0}
    for key, expected in expected_plan.items():
        if plan.get(key) != expected:
            failures.append(f"run plan {key} drifted")
    for key, filename in (("proposal_snapshot_sha256", "proposal-snapshot.json"), ("roster_sha256", "reader-roster.json"), ("constructs_sha256", "constructs.json"), ("items_sha256", "items.json"), ("prompts_sha256", "prompts.jsonl")):
        if plan.get(key) != digest(ROOT / filename):
            failures.append(f"run plan digest drift: {filename}")

    # Exact-message novelty: the new packet is permanently excluded from governance evidence,
    # but independent development cells still avoid accidentally rerunning old project prompts.
    needles = {row["message"] for row in items}
    collisions: dict[str, list[str]] = defaultdict(list)
    scanned = 0
    for path in REPO.rglob("*"):
        if not path.is_file() or ROOT in path.parents or ".git" in path.parts or "__pycache__" in path.parts:
            continue
        if path.suffix.lower() not in {".json", ".jsonl", ".md", ".txt", ".py"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        scanned += 1
        for needle in needles:
            if needle in text:
                collisions[needle].append(str(path.relative_to(REPO)))
    if collisions:
        sample = {key: value[:3] for key, value in list(collisions.items())[:5]}
        failures.append(f"exact development-message reuse detected: {sample}")

    if failures:
        raise SystemExit("REFUSING:\n- " + "\n- ".join(failures))
    print(json.dumps({
        "ok": True,
        "proposals": len(proposals),
        "readers": len(roster),
        "items": len(items),
        "prompts": len(prompts),
        "external_files_scanned_for_exact_message_reuse": scanned,
        "exact_message_collisions": 0,
        "expected_label_counts": dict(Counter(row["expected"] for row in items)),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
