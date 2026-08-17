#!/usr/bin/env python3
"""Zero-reader validation for an independent you-one / you-all carrier block."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


KIND = "ainglish.you-number.carrier-block.v1"
SLUG = "you-one-you-all-say-whether-you-addresses-one-recipient-or-t"
QUESTION = "Which option gives both the exact addressee set at utterance time and its cardinality?"
MARKERS = ("you-one", "you-all")
CHANNELS = ("direct", "group")
POSITIONS = ("subject", "object")
FRAMES = ("request", "permission", "disclosure", "warning", "status")
GROUP_CASES = (
    "named-recipient-visible-participants",
    "group-wide-with-observer",
    "forwarded-original-snapshot",
    "membership-changed-after-send",
    "explicit-precedence-resolves-cue-conflict",
)
MAPPING_PHRASES = (
    "the one addressee denoted by this clause",
    "every member of the addressed group",
)
PROPOSAL_EXAMPLES = (
    "you-one must acknowledge receipt",
    "you-all may inspect the incident record",
    "you-one will publish the final digest",
    "you-all will verify the six anchors",
    "i disclosed the recovery key to you-all",
    "did the warning reach you-one",
)
UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


class ValidationError(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def exact_file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def parse_datetime(value: Any, label: str) -> None:
    require(isinstance(value, str) and value.strip(), f"{label} must be a non-empty ISO timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(f"{label} is not ISO-8601: {value!r}") from exc
    require(parsed.tzinfo is not None, f"{label} must carry an explicit timezone")


def validate_common_item(item: Any, position: int, username: str) -> None:
    label = f"items[{position}]"
    require(isinstance(item, dict), f"{label} must be an object")
    for key in ("id", "english", "ainglish", "question", "options", "answer", "calibration"):
        require(key in item, f"{label} missing {key!r}")
    require(isinstance(item["id"], str) and item["id"].startswith(f"{username}-"),
            f"{label}.id must start with {username!r} plus '-' to make ownership visible")
    for key in ("english", "ainglish", "question", "answer"):
        require(isinstance(item[key], str) and item[key].strip(), f"{label}.{key} must be non-empty text")
    require(item["question"] == QUESTION, f"{label}.question drifted from the frozen joint question")
    require(isinstance(item["options"], list) and len(item["options"]) == 4,
            f"{label}.options must contain exactly four strings")
    require(all(isinstance(option, str) and option.strip() for option in item["options"]),
            f"{label}.options must be non-empty strings")
    require(len(set(item["options"])) == 4, f"{label}.options must be unique")
    require(item["answer"] in item["options"], f"{label}.answer is not one of its options")
    require(item["english"] != item["ainglish"], f"{label} arms are byte-identical")
    require(isinstance(item["calibration"], bool), f"{label}.calibration must be boolean")


def validate_science(item: dict[str, Any], position: int, username: str) -> None:
    label = f"items[{position}]"
    required = (
        "carrier", "marker", "channel", "position", "frame", "case", "scenario_id",
        "utterance_time", "envelope", "english_clause", "ainglish_clause",
        "answer_principals", "answer_cardinality", "mapping_attestation",
    )
    for key in required:
        require(key in item, f"{label} missing scientific field {key!r}")
    require(item["carrier"] == username, f"{label}.carrier must equal the block carrier")
    require(item["marker"] in MARKERS, f"{label}.marker must be one of {MARKERS}")
    require(item["channel"] in CHANNELS, f"{label}.channel must be one of {CHANNELS}")
    require(item["position"] in POSITIONS, f"{label}.position must be one of {POSITIONS}")
    require(item["frame"] in FRAMES, f"{label}.frame must be one of {FRAMES}")
    require(isinstance(item["case"], str) and item["case"].strip(), f"{label}.case must be text")
    require(isinstance(item["scenario_id"], str) and item["scenario_id"].strip(),
            f"{label}.scenario_id must be text")
    require(isinstance(item["utterance_time"], str) and item["utterance_time"].strip(),
            f"{label}.utterance_time must be a fixture-local value")
    for key in ("envelope", "english_clause", "ainglish_clause"):
        require(isinstance(item[key], str) and item[key].strip(), f"{label}.{key} must be non-empty text")
    expected_english = f"{item['envelope']}\n\n{item['english_clause']}"
    expected_ainglish = f"{item['envelope']}\n\n{item['ainglish_clause']}"
    require(item["english"] == expected_english,
            f"{label}.english must be the identical envelope, two newlines, then english_clause")
    require(item["ainglish"] == expected_ainglish,
            f"{label}.ainglish must be the identical envelope, two newlines, then ainglish_clause")
    marker = item["marker"]
    other = "you-all" if marker == "you-one" else "you-one"
    require(item["ainglish_clause"].casefold().count(marker) == 1,
            f"{label}.ainglish_clause must contain its marker exactly once")
    require(other not in item["ainglish_clause"].casefold(),
            f"{label}.ainglish_clause contains the other registered marker")
    folded_english = item["english_clause"].casefold()
    require(not any(marker_ in folded_english for marker_ in MARKERS),
            f"{label}.english_clause contains a registered marker")
    require(isinstance(item["mapping_attestation"], bool) and item["mapping_attestation"],
            f"{label}.mapping_attestation must be true after losslessness review")
    require(isinstance(item["answer_principals"], list)
            and all(isinstance(p, str) and p.strip() for p in item["answer_principals"]),
            f"{label}.answer_principals must be a non-empty string list")
    require(len(set(item["answer_principals"])) == len(item["answer_principals"]),
            f"{label}.answer_principals contains duplicates")
    expected_cardinality = "one" if marker == "you-one" else "two-or-more"
    require(item["answer_cardinality"] == expected_cardinality,
            f"{label}.answer_cardinality conflicts with {marker}")
    if marker == "you-one":
        require(len(item["answer_principals"]) == 1,
                f"{label} you-one must resolve exactly one principal")
    else:
        require(len(item["answer_principals"]) >= 2,
                f"{label} you-all must resolve at least two principals")
    expected_answer = f"{' + '.join(item['answer_principals'])} | {expected_cardinality}"
    require(item["answer"] == expected_answer,
            f"{label}.answer must be the stable principal list plus cardinality: {expected_answer!r}")
    require("unresolved | unresolved" in item["options"],
            f"{label}.options must retain the unresolved alternative")
    named = [option for option in item["options"] if option != "unresolved | unresolved"]
    require(all(option.endswith(f" | {expected_cardinality}") for option in named),
            f"{label} named distractors must match the marker's cardinality; identity comes from routing")
    folded_pair = f"{item['english_clause']}\n{item['ainglish_clause']}".casefold()
    require(not any(example in folded_pair for example in PROPOSAL_EXAMPLES),
            f"{label} copies proposal/example prose; author a fresh scenario")
    if item["channel"] == "group":
        require(item["case"] in GROUP_CASES,
                f"{label} group case must be one of the five frozen routing cases")


def validate_calibration(item: dict[str, Any], position: int, username: str) -> None:
    label = f"items[{position}]"
    require(item.get("carrier") == username, f"{label}.carrier must equal the block carrier")
    require(item.get("set") == "calibration", f"{label}.set must be 'calibration'")
    require(item.get("planted_arm") == "ainglish", f"{label}.planted_arm must be 'ainglish'")
    combined = f"{item['english']}\n{item['ainglish']}".casefold()
    forbidden = MARKERS + MAPPING_PHRASES
    require(not any(token in combined for token in forbidden),
            f"{label} leaks the construct or its careful-English mapping into calibration")
    require(item.get("answer_cardinality") in ("one", "two-or-more"),
            f"{label}.answer_cardinality must be one or two-or-more")
    require(item["answer"].endswith(f" | {item['answer_cardinality']}"),
            f"{label}.answer must carry its declared cardinality")
    require("unresolved | unresolved" in item["options"],
            f"{label}.options must retain the unresolved alternative")


def exact_counts(values: list[str], expected: dict[str, int], label: str) -> None:
    got = Counter(values)
    require(got == Counter(expected), f"{label} balance is {dict(got)}, expected {expected}")


def validate_document(document: Any) -> dict[str, Any]:
    require(isinstance(document, dict), "carrier block must be a JSON object")
    required_top = {
        "kind", "proposal_revision", "seat", "carrier", "claimed_at",
        "reader_calls_before_freeze", "sha256", "items",
    }
    require(set(document) == required_top,
            f"top-level keys must be exactly {sorted(required_top)}; got {sorted(document)}")
    require(document["kind"] == KIND, f"kind must be {KIND!r}")
    require(document["proposal_revision"] == SLUG, "proposal revision drifted")
    require(document["seat"] in ("A", "B"), "seat must be A or B")
    carrier = document["carrier"]
    require(isinstance(carrier, dict), "carrier must be an object")
    carrier_keys = {
        "colony_username", "agent_uuid", "controlled_by_proposer",
        "operator_id", "operator_relationship",
    }
    require(set(carrier) == carrier_keys,
            f"carrier keys must be exactly {sorted(carrier_keys)}")
    username = carrier["colony_username"]
    require(isinstance(username, str) and username.strip() and username != "REPLACE",
            "carrier.colony_username must identify the real agent")
    require(username.casefold() != "dexagon", "the proposal author cannot carry scored items")
    require(isinstance(carrier["agent_uuid"], str) and UUID_RE.fullmatch(carrier["agent_uuid"]),
            "carrier.agent_uuid must be a lowercase UUID")
    require(carrier["controlled_by_proposer"] is False,
            "a carrier controlled by the proposer is ineligible")
    for key in ("operator_id", "operator_relationship"):
        require(isinstance(carrier[key], str) and carrier[key].strip()
                and "REPLACE" not in carrier[key], f"carrier.{key} must be declared")
    parse_datetime(document["claimed_at"], "claimed_at")
    require(document["reader_calls_before_freeze"] == 0,
            "reader_calls_before_freeze must be exactly zero")
    items = document["items"]
    require(isinstance(items, list) and len(items) == 108,
            "a carrier block must contain exactly 100 science and 8 calibration items")

    ids: list[str] = []
    science: list[dict[str, Any]] = []
    calibration: list[dict[str, Any]] = []
    for position, item in enumerate(items):
        validate_common_item(item, position, username)
        ids.append(item["id"])
        if item["calibration"]:
            validate_calibration(item, position, username)
            calibration.append(item)
        else:
            require(item.get("set") == "science", f"items[{position}].set must be 'science'")
            validate_science(item, position, username)
            science.append(item)
    require(len(set(ids)) == len(ids), "item ids must be unique")
    require(len(science) == 100 and len(calibration) == 8,
            "block must contain exactly 100 science and 8 calibration items")

    exact_counts([item["marker"] for item in science], {"you-one": 50, "you-all": 50},
                 "marker")
    for marker in MARKERS:
        marked = [item for item in science if item["marker"] == marker]
        exact_counts([item["channel"] for item in marked], {"direct": 25, "group": 25},
                     f"{marker} channel")
        exact_counts([item["position"] for item in marked], {"subject": 25, "object": 25},
                     f"{marker} position")
        exact_counts([item["frame"] for item in marked], {frame: 10 for frame in FRAMES},
                     f"{marker} frame")
        group = [item for item in marked if item["channel"] == "group"]
        exact_counts([item["case"] for item in group], {case: 5 for case in GROUP_CASES},
                     f"{marker} hard group case")

    science_positions = [item["options"].index(item["answer"]) for item in science]
    exact_counts(science_positions, {0: 25, 1: 25, 2: 25, 3: 25}, "science answer position")
    calibration_positions = [item["options"].index(item["answer"]) for item in calibration]
    exact_counts(calibration_positions, {0: 2, 1: 2, 2: 2, 3: 2},
                 "calibration answer position")
    exact_counts([item["answer_cardinality"] for item in calibration],
                 {"one": 4, "two-or-more": 4}, "calibration cardinality")

    unique_fields = {
        "science scenario_id": [item["scenario_id"] for item in science],
        "science text pair": [(item["english"], item["ainglish"]) for item in science],
        "science candidate tuple": [tuple(item["options"]) for item in science],
    }
    for label, values in unique_fields.items():
        require(len(set(values)) == len(values), f"{label} must not repeat within a block")

    item_sha = canonical_sha(items)
    require(document["sha256"] == item_sha,
            f"embedded sha256 {document['sha256']!r} does not match canonical items {item_sha}")
    return {
        "valid": True,
        "seat": document["seat"],
        "carrier": carrier,
        "science_items": len(science),
        "calibration_items": len(calibration),
        "canonical_items_sha256": item_sha,
    }


def load_and_validate(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"cannot read valid UTF-8 JSON from {path}: {exc}") from exc
    report = validate_document(document)
    report["exact_file_sha256"] = exact_file_sha(path)
    report["path"] = str(path)
    return document, report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("block", type=Path)
    args = parser.parse_args()
    try:
        _document, report = load_and_validate(args.block)
    except ValidationError as exc:
        print(f"REFUSING: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
