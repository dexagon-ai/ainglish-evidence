#!/usr/bin/env python3
"""Freeze a fresh, form-specific carrier for every-two-weeks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ORIGINAL_ITEMS = ROOT.parent / "biweekly-original-2026-08-21" / "every-two-weeks-careful-items.json"
OUTPUT = ROOT / "every-two-weeks-fresh-items.json"

SITES = [
    "North depot",
    "Cedar clinic",
    "Riverside school",
    "Harbor workshop",
    "Hilltop archive",
]

TASKS = [
    "humidity inspection",
    "fire-door check",
    "water-quality sample",
    "medication stock count",
    "playground safety walk",
    "furnace filter inspection",
    "emergency-light test",
    "freezer temperature audit",
    "roof-drain inspection",
    "accessibility route review",
    "generator fuel reading",
    "library return sweep",
    "wildlife camera download",
    "soil moisture reading",
    "bicycle rack inspection",
    "first-aid kit count",
    "exhibit condition report",
    "kitchen hygiene review",
    "bus shelter cleaning",
    "air filter replacement",
]

COUNT_OPTIONS = {
    8: ["4", "8", "16", "cannot_determine"],
    10: ["5", "10", "20", "cannot_determine"],
    12: ["6", "12", "24", "cannot_determine"],
    14: ["7", "14", "28", "cannot_determine"],
    16: ["8", "16", "32", "cannot_determine"],
}


def canonical_sha(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def rotate(options: list[str], index: int) -> list[str]:
    shift = index % len(options)
    return options[shift:] + options[:shift]


def subjects() -> list[str]:
    return [f"{site}'s {task}" for site in SITES for task in TASKS]


def calibration_items() -> list[dict]:
    rows = []
    answers = ["two", "three", "six"] * 4
    for index, answer in enumerate(answers, 1):
        rows.append({
            "id": f"cal-fresh-every-two-weeks-{index:02d}",
            "calibration": True,
            "english": (
                f"Calibration schedule {index} is recurring, but the note states no interval or "
                "count for the six-week window."
            ),
            "ainglish": (
                f"Calibration schedule {index} has exactly {answer} scheduled slots inside the "
                "six-week window."
            ),
            "question": "How many scheduled slots does the note state for the window?",
            "options": rotate(["two", "three", "six", "cannot_determine"], index),
            "answer": answer,
            "strata": {
                "control": "construct_free_planted_effect",
                "form": "every-two-weeks",
                "carrier": "fresh_replication",
            },
        })
    return rows


def count_item(subject: str, index: int) -> dict:
    weeks = (8, 10, 12, 14, 16)[index % 5]
    answer = str(weeks // 2)
    english_templates = [
        (
            "The half-open observation window starts at an established scheduled occurrence and "
            "ends {weeks} complete schedule weeks later. {subject} has one scheduled recurrence "
            "at the included start and then at intervals of two schedule weeks. No clock time or "
            "execution result is stated."
        ),
        (
            "Use a half-open window of {weeks} complete schedule weeks beginning at a separately "
            "established recurrence point. That point is the first included slot for {subject}; "
            "later slots follow at intervals of two schedule weeks. Timing within a day and "
            "completion are unstated."
        ),
        (
            "An external anchor is the first included occurrence in a half-open {weeks}-week "
            "schedule window. {subject} is assigned one recurrence every interval of two schedule "
            "weeks from that anchor. The message says nothing about clock time or success."
        ),
        (
            "For {subject}, count a half-open span beginning at the already fixed recurrence and "
            "lasting {weeks} complete schedule weeks. The schedule supplies one occurrence at "
            "the included start and then at two-schedule-week intervals; execution outcome is not "
            "claimed."
        ),
    ]
    marked_templates = [
        (
            "The half-open observation window starts at an established scheduled occurrence and "
            "ends {weeks} complete schedule weeks later. {subject} is scheduled every-two-weeks "
            "from that included occurrence. No clock time or execution result is stated."
        ),
        (
            "Use a half-open window of {weeks} complete schedule weeks beginning at a separately "
            "established recurrence point. That point is the first included slot for {subject}, "
            "which is scheduled every-two-weeks from there. Timing within a day and completion "
            "are unstated."
        ),
        (
            "An external anchor is the first included occurrence in a half-open {weeks}-week "
            "schedule window. From that anchor, {subject} runs every-two-weeks. The message says "
            "nothing about clock time or success."
        ),
        (
            "For {subject}, count a half-open span beginning at the already fixed recurrence and "
            "lasting {weeks} complete schedule weeks. The schedule is every-two-weeks from the "
            "included start; execution outcome is not claimed."
        ),
    ]
    template = index % len(english_templates)
    values = {"weeks": weeks, "subject": subject}
    return {
        "id": f"fresh-every-two-weeks-{index + 1:03d}",
        "english": english_templates[template].format(**values),
        "ainglish": marked_templates[template].format(**values),
        "question": "How many scheduled occurrence slots fall inside the stated window?",
        "options": rotate(COUNT_OPTIONS[weeks], index),
        "answer": answer,
        "strata": {
            "form": "every-two-weeks",
            "probe": "cadence_count",
            "weeks": weeks,
            "carrier": "fresh_replication",
        },
    }


def scope_item(subject: str, index: int) -> dict:
    bucket = (index - 70) // 10
    english = (
        f"{subject} has one scheduled recurrence at intervals of two schedule weeks from a "
        "separately established anchor. This statement does not provide the anchor date, a clock "
        "time, or an execution result."
    )
    marked = (
        f"{subject} is scheduled every-two-weeks from a separately established anchor. This "
        "statement does not provide the anchor date, a clock time, or an execution result."
    )
    if bucket == 0:
        question = "Which calendar date is the first scheduled occurrence?"
        options = ["first_monday", "first_friday", "month_start", "cannot_determine"]
        answer = "cannot_determine"
        probe = "anchor_not_supplied"
    elif bucket == 1:
        question = "What clock time must each scheduled occurrence use?"
        options = ["midnight", "noon", "business_close", "cannot_determine"]
        answer = "cannot_determine"
        probe = "clock_not_supplied"
    else:
        question = "What outcome is reported for the latest scheduled occurrence?"
        options = ["completed", "failed", "cancelled", "not_stated"]
        answer = "not_stated"
        probe = "completion_not_supplied"
    return {
        "id": f"fresh-every-two-weeks-{index + 1:03d}",
        "english": english,
        "ainglish": marked,
        "question": question,
        "options": rotate(options, index),
        "answer": answer,
        "strata": {
            "form": "every-two-weeks",
            "probe": probe,
            "carrier": "fresh_replication",
        },
    }


def build() -> dict:
    task_subjects = subjects()
    assert len(task_subjects) == 100
    real = [
        count_item(subject, index) if index < 70 else scope_item(subject, index)
        for index, subject in enumerate(task_subjects)
    ]
    assert len(real) == 100
    assert len({row["id"] for row in real}) == 100
    assert len({(row["english"], row["ainglish"]) for row in real}) == 100
    assert sum(row["strata"]["probe"] == "cadence_count" for row in real) == 70
    assert sum(row["strata"]["probe"] == "anchor_not_supplied" for row in real) == 10
    assert sum(row["strata"]["probe"] == "clock_not_supplied" for row in real) == 10
    assert sum(row["strata"]["probe"] == "completion_not_supplied" for row in real) == 10

    original = json.loads(ORIGINAL_ITEMS.read_text(encoding="utf-8"))
    old_pairs = {
        (row["english"], row["ainglish"])
        for row in original["items"]
        if not row.get("calibration")
    }
    new_pairs = {(row["english"], row["ainglish"]) for row in real}
    assert old_pairs.isdisjoint(new_pairs)

    items = calibration_items() + real
    return {
        "kind": "ainglish.panel.items.v1",
        "proposal": "twice-weekly-every-two-weeks-split-biweekly-into-its-two-inc",
        "form": "every-two-weeks",
        "baseline": "complete_careful_english",
        "replicates_hash": "ac6fb637c65705f149d2daa2034c72dd40322ce2ac430e736c1d9837d6e78181",
        "input_disjointness": 1.0,
        "original_items_sha256": original["sha256"],
        "real_items": 100,
        "calibration_items": 12,
        "sha256": canonical_sha(items),
        "items": items,
    }


def main() -> None:
    document = build()
    OUTPUT.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": OUTPUT.name,
        "items_sha256": document["sha256"],
        "file_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
        "real_items": document["real_items"],
        "calibration_items": document["calibration_items"],
        "input_disjointness": document["input_disjointness"],
    }, indent=2))


if __name__ == "__main__":
    main()
