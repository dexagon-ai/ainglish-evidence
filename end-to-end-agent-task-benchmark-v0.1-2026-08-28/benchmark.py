#!/usr/bin/env python3
"""Validate, export and descriptively score Ainglish agent-task benchmark v0.1."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent
TASKS_PATH = ROOT / "tasks.json"
ARMS = ("bare", "careful", "ainglish")
TRACKS = ("cold", "one_exposure")


class ContractError(ValueError):
    pass


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def load_tasks() -> dict[str, Any]:
    with TASKS_PATH.open(encoding="utf-8") as handle:
        packet = json.load(handle)
    validate_packet(packet)
    return packet


def validate_packet(packet: dict[str, Any]) -> None:
    if packet.get("benchmark") != "ainglish-agent-task-v0.1":
        raise ContractError("unexpected benchmark identifier")
    if tuple(packet.get("arms", [])) != ARMS:
        raise ContractError(f"arms must be {ARMS}")
    if tuple(packet.get("tracks", [])) != TRACKS:
        raise ContractError(f"tracks must be {TRACKS}")
    release = packet.get("source_release", {})
    if release.get("version") != "0.35.0" or not is_sha256(release.get("register_digest")):
        raise ContractError("source release must bind v0.35.0 and its SHA-256 register digest")

    items = packet.get("items")
    if not isinstance(items, list) or len(items) < 12:
        raise ContractError("packet needs at least 12 curated items")
    ids: set[str] = set()
    poles: dict[str, set[str]] = defaultdict(set)
    for item in items:
        item_id = required_text(item, "id")
        if item_id in ids:
            raise ContractError(f"duplicate item id: {item_id}")
        ids.add(item_id)
        construct = required_text(item, "construct")
        poles[construct].add(required_text(item, "pole"))
        for field in ("source_slug", "context", "source_intent", "clarification"):
            required_text(item, field)
        actions = item.get("actions")
        if not isinstance(actions, list) or len(actions) < 2:
            raise ContractError(f"{item_id}: actions must contain at least two choices")
        action_ids = [required_text(action, "id") for action in actions]
        if len(action_ids) != len(set(action_ids)):
            raise ContractError(f"{item_id}: duplicate action id")
        for action in actions:
            required_text(action, "description")
        valid_sets = item.get("valid_action_sets")
        if not isinstance(valid_sets, list) or not valid_sets:
            raise ContractError(f"{item_id}: valid_action_sets must be non-empty")
        normalized: set[tuple[str, ...]] = set()
        for action_set in valid_sets:
            if not isinstance(action_set, list) or not action_set:
                raise ContractError(f"{item_id}: each valid action set must be non-empty")
            if len(action_set) != len(set(action_set)) or not set(action_set) <= set(action_ids):
                raise ContractError(f"{item_id}: valid action set contains duplicates or unknown actions")
            key = tuple(sorted(action_set))
            if key in normalized:
                raise ContractError(f"{item_id}: duplicate valid action set")
            normalized.add(key)
        arms = item.get("arms")
        if not isinstance(arms, dict) or set(arms) != set(ARMS):
            raise ContractError(f"{item_id}: exactly the three declared arms are required")
        messages: set[str] = set()
        for arm in ARMS:
            arm_record = arms[arm]
            message = required_text(arm_record, "message")
            if message in messages:
                raise ContractError(f"{item_id}: arm messages must differ")
            messages.add(message)
            if arm == "ainglish":
                required_text(arm_record, "reference")
            elif "reference" in arm_record:
                raise ContractError(f"{item_id}: only the Ainglish arm may carry a project-specific reference")
    for construct, seen_poles in poles.items():
        if len(seen_poles) < 2:
            raise ContractError(f"{construct}: benchmark must include at least two poles")


def required_text(record: dict[str, Any], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{field} must be non-empty text")
    return value


def is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def prompt_for(item: dict[str, Any], arm: str, track: str) -> str:
    arm_record = item["arms"][arm]
    blocks = [
        "You are the receiving agent in an operational task benchmark.",
        item["context"],
    ]
    if track == "one_exposure" and arm == "ainglish":
        blocks.append("One-use reference: " + arm_record["reference"])
    blocks.extend([
        "Message from the sender: " + arm_record["message"],
        "Available actions:\n" + "\n".join(
            f'- {action["id"]}: {action["description"]}' for action in item["actions"]
        ),
        (
            'Respond with JSON only. Either {"decision":"act","actions":["action-id"]} using one or more '
            'available action IDs, or {"decision":"clarify","question":"one concise question"}. Do not add keys.'
        ),
    ])
    return "\n\n".join(blocks)


def export_records(packet: dict[str, Any], arm_choice: str, track: str, seed: int) -> Iterable[dict[str, Any]]:
    records = []
    arms = ARMS if arm_choice == "all" else (arm_choice,)
    for item in packet["items"]:
        for arm in arms:
            records.append({
                "item_id": item["id"],
                "construct": item["construct"],
                "arm": arm,
                "track": track,
                "prompt": prompt_for(item, arm, track),
                "clarification": item["clarification"],
            })
    random.Random(seed).shuffle(records)
    for order, record in enumerate(records, 1):
        yield {"order": order, **record}


def parse_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ContractError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
            if not isinstance(row, dict):
                raise ContractError(f"{path}:{line_no}: each row must be an object")
            row["_line"] = line_no
            rows.append(row)
    return rows


def normalize_decision(decision: Any, action_ids: set[str], where: str) -> dict[str, Any]:
    if not isinstance(decision, dict):
        raise ContractError(f"{where}: decision must be an object")
    kind = decision.get("decision")
    if kind == "act":
        if set(decision) - {"decision", "actions", "input_tokens", "output_tokens", "latency_ms"}:
            raise ContractError(f"{where}: unexpected act-response keys")
        actions = decision.get("actions")
        if not isinstance(actions, list) or not actions or not all(isinstance(v, str) for v in actions):
            raise ContractError(f"{where}: act response needs a non-empty action list")
        if len(actions) != len(set(actions)) or not set(actions) <= action_ids:
            raise ContractError(f"{where}: duplicate or unknown action")
        question = None
    elif kind == "clarify":
        if set(decision) - {"decision", "question", "input_tokens", "output_tokens", "latency_ms"}:
            raise ContractError(f"{where}: unexpected clarify-response keys")
        question = decision.get("question")
        if not isinstance(question, str) or not question.strip():
            raise ContractError(f"{where}: clarify response needs a question")
        actions = []
    elif kind == "invalid":
        if set(decision) - {"decision", "raw", "input_tokens", "output_tokens", "latency_ms"}:
            raise ContractError(f"{where}: unexpected invalid-response keys")
        raw = decision.get("raw")
        if not isinstance(raw, str) or not raw:
            raise ContractError(f"{where}: invalid response must preserve the complete non-empty raw output")
        actions = []
        question = None
    else:
        raise ContractError(f"{where}: decision must be act, clarify or invalid")
    usage: dict[str, float] = {}
    for field in ("input_tokens", "output_tokens", "latency_ms"):
        value = decision.get(field)
        if value is not None:
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
                raise ContractError(f"{where}: {field} must be a non-negative number")
            usage[field] = float(value)
    return {"decision": kind, "actions": sorted(actions), "question": question, "usage": usage}


def classify_rows(packet: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {item["id"]: item for item in packet["items"]}
    seen: set[tuple[str, str, str, str]] = set()
    classified = []
    for row in rows:
        line = row.pop("_line", "?")
        item_id = row.get("item_id")
        arm = row.get("arm")
        track = row.get("track")
        reader_id = row.get("reader_id")
        if item_id not in by_id:
            raise ContractError(f"line {line}: unknown item_id")
        if arm not in ARMS or track not in TRACKS:
            raise ContractError(f"line {line}: unknown arm or track")
        if not isinstance(reader_id, str) or not reader_id.strip():
            raise ContractError(f"line {line}: reader_id must be non-empty")
        key = (reader_id, track, item_id, arm)
        if key in seen:
            raise ContractError(f"line {line}: duplicate reader/track/item/arm row")
        seen.add(key)
        item = by_id[item_id]
        action_ids = {action["id"] for action in item["actions"]}
        valid_sets = {tuple(sorted(v)) for v in item["valid_action_sets"]}
        first = normalize_decision(row.get("first"), action_ids, f"line {line} first")
        repair_raw = row.get("repair")
        repair = None if repair_raw is None else normalize_decision(repair_raw, action_ids, f"line {line} repair")
        if first["decision"] != "clarify" and repair is not None:
            raise ContractError(f"line {line}: repair is allowed only after first-turn clarification")
        if first["decision"] == "clarify" and repair is not None and repair["decision"] != "act":
            raise ContractError(f"line {line}: repair must be an action")
        first_correct = first["decision"] == "act" and tuple(first["actions"]) in valid_sets
        wrong_action = first["decision"] == "act" and not first_correct
        final_correct = first_correct or (
            first["decision"] == "clarify"
            and repair is not None
            and tuple(repair["actions"]) in valid_sets
        )
        usage = merge_usage(first["usage"], repair["usage"] if repair else {})
        classified.append({
            "item_id": item_id,
            "construct": item["construct"],
            "arm": arm,
            "track": track,
            "reader_id": reader_id,
            "zero_repair_success": first_correct,
            "final_success": final_correct,
            "clarified": first["decision"] == "clarify",
            "invalid_output": first["decision"] == "invalid",
            "wrong_action": wrong_action,
            "repair_missing": first["decision"] == "clarify" and repair is None,
            **usage,
        })
    return classified


def merge_usage(first: dict[str, float], repair: dict[str, float]) -> dict[str, float | None]:
    token_fields = ("input_tokens", "output_tokens")
    total_tokens = None
    if all(field in first for field in token_fields) and (not repair or all(field in repair for field in token_fields)):
        total_tokens = sum(first[field] for field in token_fields) + sum(repair.get(field, 0.0) for field in token_fields)
    latency_ms = None
    if "latency_ms" in first and (not repair or "latency_ms" in repair):
        latency_ms = first["latency_ms"] + repair.get("latency_ms", 0.0)
    return {"total_tokens": total_tokens, "latency_ms": latency_ms}


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(row["track"], row["arm"])].append(row)
    return {
        "schema": "ainglish.agent-task-score.v0.1",
        "rows": len(rows),
        "groups": [group_summary(track, arm, group) for (track, arm), group in sorted(groups.items())],
    }


def group_summary(track: str, arm: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    tokens = [row["total_tokens"] for row in rows if row["total_tokens"] is not None]
    latencies = [row["latency_ms"] for row in rows if row["latency_ms"] is not None]
    return {
        "track": track,
        "arm": arm,
        "n": n,
        "reader_ids": sorted({row["reader_id"] for row in rows}),
        "zero_repair_success": count_rate(rows, "zero_repair_success"),
        "final_success": count_rate(rows, "final_success"),
        "clarification": count_rate(rows, "clarified"),
        "invalid_output": count_rate(rows, "invalid_output"),
        "wrong_action": count_rate(rows, "wrong_action"),
        "repair_missing": count_rate(rows, "repair_missing"),
        "total_tokens": numeric_summary(tokens, n),
        "latency_ms": numeric_summary(latencies, n),
    }


def count_rate(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    count = sum(bool(row[field]) for row in rows)
    return {"count": count, "rate": round(count / len(rows), 6) if rows else None}


def numeric_summary(values: list[float], denominator: int) -> dict[str, Any]:
    return {
        "coverage": len(values),
        "denominator": denominator,
        "mean": round(statistics.fmean(values), 4) if values else None,
        "median": round(statistics.median(values), 4) if values else None,
    }


def self_test(packet: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for item in packet["items"]:
        rows.append({
            "item_id": item["id"],
            "arm": "ainglish",
            "track": "cold",
            "reader_id": "self-test/fixture",
            "first": {"decision": "act", "actions": item["valid_action_sets"][0], "input_tokens": 1, "output_tokens": 1, "latency_ms": 1},
        })
        rows.append({
            "item_id": item["id"],
            "arm": "careful",
            "track": "one_exposure",
            "reader_id": "self-test/fixture",
            "first": {"decision": "clarify", "question": "Please clarify.", "input_tokens": 1, "output_tokens": 1, "latency_ms": 1},
            "repair": {"decision": "act", "actions": item["valid_action_sets"][0], "input_tokens": 1, "output_tokens": 1, "latency_ms": 1},
        })
    result = summarize(classify_rows(packet, rows))
    expected = {
        ("cold", "ainglish"): (1.0, 1.0, 0.0, 2.0),
        ("one_exposure", "careful"): (0.0, 1.0, 1.0, 4.0),
    }
    for group in result["groups"]:
        key = (group["track"], group["arm"])
        actual = (
            group["zero_repair_success"]["rate"],
            group["final_success"]["rate"],
            group["clarification"]["rate"],
            group["total_tokens"]["mean"],
        )
        if actual != expected[key]:
            raise AssertionError(f"self-test mismatch for {key}: {actual}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    export = sub.add_parser("export")
    export.add_argument("--arm", choices=(*ARMS, "all"), default="all")
    export.add_argument("--track", choices=TRACKS, required=True)
    export.add_argument("--seed", type=int, default=20260828)
    score = sub.add_parser("score")
    score.add_argument("responses", type=Path)
    sub.add_parser("self-test")
    args = parser.parse_args()

    try:
        packet = load_tasks()
        if args.command == "validate":
            print(json.dumps({
                "ok": True,
                "items": len(packet["items"]),
                "constructs": len({item["construct"] for item in packet["items"]}),
                "tasks_sha256": hashlib.sha256(canonical_json(packet)).hexdigest(),
            }, sort_keys=True))
        elif args.command == "export":
            for record in export_records(packet, args.arm, args.track, args.seed):
                print(json.dumps(record, ensure_ascii=False, sort_keys=True))
        elif args.command == "score":
            print(json.dumps(summarize(classify_rows(packet, parse_jsonl(args.responses))), indent=2, sort_keys=True))
        elif args.command == "self-test":
            result = self_test(packet)
            print(json.dumps({"ok": True, "rows": result["rows"], "groups": len(result["groups"])}, sort_keys=True))
    except (ContractError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
