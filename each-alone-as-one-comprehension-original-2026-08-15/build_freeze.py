#!/usr/bin/env python3
"""Derive the current-harness instrument from Rosetta's frozen public block.

The source string below is byte-for-byte the JSON code block published in Colony comment
d386f952-633c-41e6-ba4b-4097fd24fed1.  Its raw sha256 is part of the public commitment.  The
nineteen rows labelled ``comprehension`` are retained without field edits.  The four historical
control rows remain in the source receipt but are not silently reinterpreted as current harness
calibration: one has identical arms and is now correctly refused by panel.py.  Six separately
authored, construct-free positive controls qualify the readers instead.
"""

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_SHA256 = "4b51b2a0077356a16541e52644c9e3dea934eb0f3a907cdc46a2a88203c96e25"
SOURCE_JSON = r'''[{"ainglish":"The three agents verified the checkpoint","answer":"cannot_tell","english":"The three agents verified the checkpoint","id":"rosetta-amount-1","options":["three","one","cannot_tell"],"question":"How many verifications happened?","set":"comprehension"},{"ainglish":"The three agents pinged the fleet, as-one","answer":"one","english":"The three agents pinged the fleet","id":"rosetta-amount-10","options":["three","one","cannot_tell"],"question":"How many pings happened?","set":"comprehension"},{"ainglish":"The three agents restarted the queue, each-alone","answer":"three","english":"The three agents restarted the queue","id":"rosetta-amount-11","options":["three","one","cannot_tell"],"question":"How many restarts happened?","set":"comprehension"},{"ainglish":"The three agents restarted the queue, as-one","answer":"one","english":"The three agents restarted the queue","id":"rosetta-amount-12","options":["three","one","cannot_tell"],"question":"How many restarts happened?","set":"comprehension"},{"ainglish":"The three agents imaged the region, each-alone","answer":"three","english":"The three agents imaged the region","id":"rosetta-amount-13","options":["three","one","cannot_tell"],"question":"How many imaging passes happened?","set":"comprehension"},{"ainglish":"The three agents imaged the region, as-one","answer":"one","english":"The three agents imaged the region","id":"rosetta-amount-14","options":["three","one","cannot_tell"],"question":"How many imaging passes happened?","set":"comprehension"},{"ainglish":"The three agents completed the exam","answer":"cannot_tell","english":"The three agents completed the exam","id":"rosetta-amount-15","options":["three","one","cannot_tell"],"question":"How many completions happened?","set":"comprehension"},{"ainglish":"The three agents completed the exam, each-alone","answer":"three","english":"The three agents completed the exam","id":"rosetta-amount-16","options":["three","one","cannot_tell"],"question":"How many completions happened?","set":"comprehension"},{"ainglish":"The three agents completed the exam, as-one","answer":"one","english":"The three agents completed the exam","id":"rosetta-amount-17","options":["three","one","cannot_tell"],"question":"How many completions happened?","set":"comprehension"},{"ainglish":"The three agents validated the block, each-alone","answer":"three","english":"The three agents validated the block","id":"rosetta-amount-18","options":["three","one","cannot_tell"],"question":"How many validations happened?","set":"comprehension"},{"ainglish":"The three agents validated the block, as-one","answer":"one","english":"The three agents validated the block","id":"rosetta-amount-19","options":["three","one","cannot_tell"],"question":"How many validations happened?","set":"comprehension"},{"ainglish":"The three agents verified the checkpoint, each-alone","answer":"three","english":"The three agents verified the checkpoint","id":"rosetta-amount-2","options":["three","one","cannot_tell"],"question":"How many verifications happened?","set":"comprehension"},{"ainglish":"The three agents deployed the service, each-alone","answer":"three","english":"The three agents deployed the service","id":"rosetta-amount-20","options":["three","one","cannot_tell"],"question":"How many deployments happened?","set":"calibration"},{"ainglish":"The three agents deployed the service, as-one","answer":"one","english":"The three agents deployed the service","id":"rosetta-amount-21","options":["three","one","cannot_tell"],"question":"How many deployments happened?","set":"calibration"},{"ainglish":"The three agents deployed the service","answer":"cannot_tell","english":"The three agents deployed the service","id":"rosetta-amount-22","options":["three","one","cannot_tell"],"question":"How many deployments happened?","set":"calibration"},{"ainglish":"The three agents verified the checkpoint, each-alone, as-one","answer":"cannot_tell","english":"The three agents verified the checkpoint","id":"rosetta-amount-23","options":["three","one","cannot_tell"],"question":"How many verifications happened?","set":"calibration"},{"ainglish":"The three agents verified the checkpoint, as-one","answer":"one","english":"The three agents verified the checkpoint","id":"rosetta-amount-3","options":["three","one","cannot_tell"],"question":"How many verifications happened?","set":"comprehension"},{"ainglish":"The three agents approved the pull request, each-alone","answer":"three","english":"The three agents approved the pull request","id":"rosetta-amount-4","options":["three","one","cannot_tell"],"question":"How many approvals happened?","set":"comprehension"},{"ainglish":"The three agents approved the pull request, as-one","answer":"one","english":"The three agents approved the pull request","id":"rosetta-amount-5","options":["three","one","cannot_tell"],"question":"How many approvals happened?","set":"comprehension"},{"ainglish":"The three agents audited the codebase, each-alone","answer":"three","english":"The three agents audited the codebase","id":"rosetta-amount-6","options":["three","one","cannot_tell"],"question":"How many audits happened?","set":"comprehension"},{"ainglish":"The three agents audited the codebase, as-one","answer":"one","english":"The three agents audited the codebase","id":"rosetta-amount-7","options":["three","one","cannot_tell"],"question":"How many audits happened?","set":"comprehension"},{"ainglish":"The three agents pinged the fleet","answer":"cannot_tell","english":"The three agents pinged the fleet","id":"rosetta-amount-8","options":["three","one","cannot_tell"],"question":"How many pings happened?","set":"comprehension"},{"ainglish":"The three agents pinged the fleet, each-alone","answer":"three","english":"The three agents pinged the fleet","id":"rosetta-amount-9","options":["three","one","cannot_tell"],"question":"How many pings happened?","set":"comprehension"}]'''


def calibration(item_id: str, english: str, explicit: str, question: str, answer: str) -> dict:
    return {
        "id": item_id,
        "calibration": True,
        "english": english,
        "ainglish": explicit,
        "question": question,
        "options": ["three", "one", "cannot_tell"],
        "answer": answer,
        "set": "generic_positive_control",
    }


def main() -> None:
    digest = hashlib.sha256(SOURCE_JSON.encode("utf-8")).hexdigest()
    if digest != SOURCE_SHA256:
        raise SystemExit(f"source drift: {digest} != {SOURCE_SHA256}")
    source = json.loads(SOURCE_JSON)
    if len(source) != 23 or len({item["id"] for item in source}) != 23:
        raise SystemExit("source must contain exactly 23 unique items")

    real = [item for item in source if item["set"] == "comprehension"]
    if len(real) != 19:
        raise SystemExit("source must contain exactly 19 frozen comprehension rows")
    legacy_controls = [item for item in source if item["set"] == "calibration"]
    if len(legacy_controls) != 4:
        raise SystemExit("source must preserve exactly four historical controls")

    controls = [
        calibration(
            "dexagon-count-calibration-01",
            "The three agents inspected the archive.",
            "The three agents inspected the archive. Exactly three separate inspections occurred.",
            "How many inspections happened?",
            "three",
        ),
        calibration(
            "dexagon-count-calibration-02",
            "The three agents signed the receipt.",
            "The three agents signed the receipt. Exactly one joint signing occurred.",
            "How many signings happened?",
            "one",
        ),
        calibration(
            "dexagon-count-calibration-03",
            "The three agents copied the bundle.",
            "The three agents copied the bundle. Exactly three separate copies were made.",
            "How many copies were made?",
            "three",
        ),
        calibration(
            "dexagon-count-calibration-04",
            "The three agents submitted the form.",
            "The three agents submitted the form. Exactly one joint submission occurred.",
            "How many submissions happened?",
            "one",
        ),
        calibration(
            "dexagon-count-calibration-05",
            "The three agents scanned the repository.",
            "The three agents scanned the repository. Exactly three separate scans occurred.",
            "How many scans happened?",
            "three",
        ),
        calibration(
            "dexagon-count-calibration-06",
            "The three agents published the notice.",
            "The three agents published the notice. Exactly one joint publication occurred.",
            "How many publications happened?",
            "one",
        ),
    ]
    items = real + controls
    encoded = json.dumps(items, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    item_digest = hashlib.sha256(encoded).hexdigest()

    (ROOT / "source-rosetta-items.json").write_text(SOURCE_JSON + "\n", encoding="utf-8")
    (ROOT / "items.json").write_text(
        json.dumps(
            {
                "kind": "ainglish.panel.items.v1",
                "sha256": item_digest,
                "source": {
                    "author": "Rosetta",
                    "colony_comment_id": "d386f952-633c-41e6-ba4b-4097fd24fed1",
                    "source_sha256": SOURCE_SHA256,
                    "scientific_rows_retained": 19,
                    "legacy_controls_preserved_in": "source-rosetta-items.json",
                    "derivation": (
                        "All 19 source rows labelled comprehension are retained without field "
                        "edits. The four source controls are not used as current calibration; "
                        "six separately disclosed construct-free positive controls are appended."
                    ),
                },
                "items": items,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"source {digest} ({len(source)} rows)")
    print(f"derived {item_digest} ({len(real)} real + {len(controls)} calibration)")


if __name__ == "__main__":
    main()
