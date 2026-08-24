#!/usr/bin/env python3
"""Zero-spend structural and exact-pair-overlap check for a fresh carrier."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parent
REQUIRED = {"id", "english", "ainglish", "question", "options", "answer"}


def items(document: object) -> list[dict]:
    value = document if isinstance(document, list) else document.get("items")
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError("document must be an item array or an object with an item array")
    return value


def normalized_pair(item: dict) -> tuple[str, str]:
    return (" ".join(item["english"].split()), " ".join(item["ainglish"].split()))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("target_key")
    parser.add_argument("candidate_json", type=pathlib.Path)
    args = parser.parse_args()

    handoffs = json.loads((ROOT / "handoffs.json").read_text())
    target = next((row for row in handoffs["targets"] if row["key"] == args.target_key), None)
    if target is None:
        parser.error("unknown target_key")

    candidate = items(json.loads(args.candidate_json.read_text()))
    original_path = (ROOT / target["original_items"]).resolve()
    original = items(json.loads(original_path.read_text()))
    failures: list[str] = []

    ids = [str(item.get("id", "")) for item in candidate]
    if len(ids) != len(set(ids)):
        failures.append("candidate ids are not unique")
    for index, item in enumerate(candidate):
        missing = REQUIRED - item.keys()
        if missing:
            failures.append(f"item {index} lacks {sorted(missing)}")
            continue
        if item["answer"] not in item["options"]:
            failures.append(f"item {item['id']} has an answer absent from options")

    original_pairs = {normalized_pair(item) for item in original if REQUIRED <= item.keys()}
    overlap = [item.get("id", "<missing-id>") for item in candidate if REQUIRED <= item.keys() and normalized_pair(item) in original_pairs]
    if overlap:
        failures.append(f"{len(overlap)} exact normalized pair(s) overlap the original: {overlap}")

    result = {
        "target": target["key"],
        "candidate_items": len(candidate),
        "exact_pair_overlap": len(overlap),
        "structurally_valid": not failures,
        "failures": failures,
        "semantic_review_still_required": True,
    }
    print(json.dumps(result, indent=2))
    return int(bool(failures))


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2)
