#!/usr/bin/env python3
"""Fail closed on v1 preservation, v2 seam gates, validity controls, and balance."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
V1 = REPO / "new-language-comprehension-carriers-v1-2026-08-29"
FILES = ("negation-zero-shot-v2.json", "negation-definition-conditioned-v2.json")


class Refusal(RuntimeError):
    pass


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    unsigned = dict(value)
    expected = unsigned.pop("content_sha256", None)
    if hashlib.sha256(canonical(unsigned)).hexdigest() != expected:
        raise Refusal(f"content digest drift at {path}")
    return value


def base_message(packet: dict, value: str) -> str:
    reference = packet["reference_card"]
    if reference is None:
        return value
    prefix = reference + "\nMessage: "
    if not value.startswith(prefix):
        raise Refusal("definition-conditioned message lost its exact reference prefix")
    return value[len(prefix):]


def stripped_v2_semantic(row: dict) -> dict:
    clean = deepcopy(row)
    clean.pop("section", None)
    clean.pop("source_v1_row_id", None)
    clean["questions"] = [
        question for question in clean["questions"]
        if question["id"] not in {"rely_on_one_satisfier", "n_minus_one_satisfiers"}
    ]
    return clean


def answer_positions(rows: list[dict], section: str) -> dict[str, Counter]:
    result: dict[str, Counter] = {}
    for row in rows:
        if row["section"] != section:
            continue
        for question in row["questions"]:
            result.setdefault(question["id"], Counter())[question["options"].index(question["answer"])] += 1
    return result


def audit_packet(packet: dict) -> dict:
    condition = packet["condition"]
    source_name = f"negation-{condition.replace('_', '-')}.json"
    source = checked(V1 / source_name)
    if packet["source_v1"]["content_sha256"] != source["content_sha256"]:
        raise Refusal(f"v1 source binding drift for {condition}")
    rows = packet["scientific_rows"]
    semantic = [row for row in rows if row["section"] == "semantic_interval"]
    validity = [row for row in rows if row["section"] == "set_validity"]
    if len(semantic) != 160 or len(validity) != 100 or len(packet["calibration_rows"]) != 12:
        raise Refusal(f"population drift for {condition}")
    if [stripped_v2_semantic(row) for row in semantic] != source["scientific_rows"]:
        raise Refusal(f"v1 answer-bearing semantic content changed for {condition}")
    if len({row["id"] for row in rows}) != 260:
        raise Refusal(f"duplicate row id for {condition}")
    if Counter(row["form"] for row in rows) != {"none-of": 130, "not-all-of": 130}:
        raise Refusal(f"form imbalance for {condition}")
    if Counter(row["validity_case"] for row in validity) != {
        "empty": 20,
        "missing": 20,
        "changing": 20,
        "multiply_resolved": 20,
        "fixed_receipt_epoch": 20,
    }:
        raise Refusal(f"validity-case imbalance for {condition}")
    by_context: dict[str, list[dict]] = {}
    for row in validity:
        by_context.setdefault(row["context_id"], []).append(row)
    if len(by_context) != 50 or any(len(group) != 2 for group in by_context.values()):
        raise Refusal(f"validity pairing drift for {condition}")
    for group in by_context.values():
        if len({base_message(packet, row["arms"]["bare_english"]) for row in group}) != 1:
            raise Refusal(f"paired validity bare text diverged for {condition}")
        if len({base_message(packet, row["arms"]["ainglish"]) for row in group}) != 2:
            raise Refusal(f"paired validity marked text collapsed for {condition}")
    for row in semantic:
        answers = {question["id"]: question["answer"] for question in row["questions"]}
        if answers["rely_on_one_satisfier"] != "no":
            raise Refusal("a semantic row licenses reliance on one satisfier")
        if answers["n_minus_one_satisfiers"] != ("yes" if row["form"] == "not-all-of" else "no"):
            raise Refusal("N-1 control disagrees with the form")
    for row in validity:
        answers = {question["id"]: question["answer"] for question in row["questions"]}
        valid = row["validity_case"] == "fixed_receipt_epoch"
        expected_validity = "valid quantifier claim" if valid else "invalid or unresolved"
        expected_interval = (
            "exactly zero" if valid and row["form"] == "none-of"
            else "zero through N-1" if valid
            else "no valid interval"
        )
        if answers != {
            "set_validity": expected_validity,
            "validity_interval": expected_interval,
            "rely_on_one_satisfier": "no",
            "population_overread": "no",
        }:
            raise Refusal(f"validity ground truth drift at {row['id']}")
    for section in ("semantic_interval", "set_validity"):
        for question, positions in answer_positions(rows, section).items():
            if set(positions) != {0, 1, 2} or max(positions.values()) - min(positions.values()) > 1:
                raise Refusal(f"answer-position imbalance for {condition}/{section}/{question}: {positions}")
    support = packet["contract"]["support"]
    if support.get("no_pooled_override") is not True or len(support.get("separate_gates", [])) != 7:
        raise Refusal(f"separate gate contract drift for {condition}")
    if packet["model_calls"] or packet["attempts_minted"] or packet["governance_writes"]:
        raise Refusal(f"prospective zero-spend claim drift for {condition}")
    return {
        "condition": condition,
        "semantic_rows": 160,
        "validity_rows": 100,
        "calibration_rows": 12,
        "v1_semantics_preserved_exactly": True,
        "invalid_cases_per_type": 20,
        "separate_gates": 7,
        "content_sha256": packet["content_sha256"],
    }


def main() -> None:
    packets = [checked(ROOT / name) for name in FILES]
    results = [audit_packet(packet) for packet in packets]
    zero = packets[0]
    conditioned = packets[1]
    zero_messages = {
        base_message(zero, arm)
        for row in zero["scientific_rows"]
        for arm in row["arms"].values()
    }
    conditioned_messages = {
        base_message(conditioned, arm)
        for row in conditioned["scientific_rows"]
        for arm in row["arms"].values()
    }
    if zero_messages & conditioned_messages:
        raise Refusal("zero-shot and definition-conditioned messages overlap")
    mutant = deepcopy(packets[0])
    mutant["contract"]["support"]["no_pooled_override"] = False
    try:
        audit_packet(mutant)
    except Refusal:
        mutation_control = "passed"
    else:
        raise Refusal("audit accepted a pooled-score override mutant")
    index = checked(ROOT / "index.json")
    if index["no_pooled_override"] is not True or {
        row["content_sha256"] for row in index["packets"]
    } != {packet["content_sha256"] for packet in packets}:
        raise Refusal("index binding drift")
    audit = {
        "kind": "dexagon.ainglish.universal-negation-carrier-audit.v2",
        "status": "passed",
        "packets": results,
        "zero_vs_definition_exact_message_overlap": 0,
        "pooled_override_mutation_control": mutation_control,
        "model_calls": 0,
        "attempts_minted": 0,
        "governance_writes": 0,
    }
    audit["content_sha256"] = hashlib.sha256(canonical(audit)).hexdigest()
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Refusal as error:
        raise SystemExit(f"REFUSING: {error}") from error
