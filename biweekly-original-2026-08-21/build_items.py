#!/usr/bin/env python3
"""Freeze two non-pooled careful-English comprehension panels for the biweekly split."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from measure_token_delta_once import SUBJECTS


ROOT = Path(__file__).resolve().parent
OPTIONS_COUNT = ["twelve", "three", "six", "cannot_tell"]


def canonical_sha(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def rotate(options: list[str], index: int) -> list[str]:
    shift = index % len(options)
    return options[shift:] + options[:shift]


def calibration_items(form: str) -> list[dict]:
    rows = []
    answers = ["twelve", "three", "six"] * 4
    for index, answer in enumerate(answers, 1):
        vague = (
            f"Calibration job {index} has a recurring timetable, but this note gives no frequency "
            "from which a six-week launch count can be recovered."
        )
        explicit = (
            f"Calibration job {index} has exactly {answer} launch opportunities in the stated "
            "six-week interval."
        )
        rows.append({
            "id": f"cal-{form}-{index:02d}",
            "calibration": True,
            "english": vague,
            "ainglish": explicit,
            "question": "How many launch opportunities does the message license in the stated interval?",
            "options": rotate(OPTIONS_COUNT, index),
            "answer": answer,
            "strata": {"control": "construct_free_planted_effect", "form": form},
        })
    return rows


def count_item(form: str, subject: str, index: int) -> dict:
    weeks = (4, 6, 8, 10, 12)[index % 5]
    subject_start = subject.capitalize()
    if form == "twice-weekly":
        english = (
            f"The observation window contains {weeks} complete schedule weeks. {subject_start} has "
            "exactly two scheduled occurrence slots in each schedule week; its days, spacing, "
            "and successful completion are not stated."
        )
        marked = (
            f"The observation window contains {weeks} complete schedule weeks. {subject_start} runs "
            "twice-weekly; its days, spacing, and successful completion are not stated."
        )
        answer = str(weeks * 2)
        distractors = [str(weeks // 2), str(weeks), "cannot_tell"]
    else:
        english = (
            f"The observation window begins at the established recurrence point and contains "
            f"{weeks} complete schedule weeks. From that point, {subject} has one scheduled "
            "recurrence at intervals of two schedule weeks; its clock time and successful "
            "completion are not stated."
        )
        marked = (
            f"The observation window begins at the established recurrence point and contains "
            f"{weeks} complete schedule weeks. From that point, {subject} runs every-two-weeks; "
            "its clock time and successful completion are not stated."
        )
        answer = str(weeks // 2)
        distractors = [str(weeks * 2), str(weeks), "cannot_tell"]
    options = rotate([answer] + distractors, index)
    return {
        "id": f"real-{form}-{index + 1:03d}",
        "english": english,
        "ainglish": marked,
        "question": "How many launch opportunities does the message prescribe inside that half-open observation window?",
        "options": options,
        "answer": answer,
        "strata": {"form": form, "probe": "cadence_count", "weeks": weeks},
    }


def overread_item(form: str, subject: str, index: int) -> dict:
    subject = subject.capitalize()
    bucket = (index - 70) // 10
    if form == "twice-weekly":
        english = (
            f"{subject} has exactly two scheduled occurrence slots in every schedule week. "
            "The sentence does not choose their days, fix their spacing, or report whether a run succeeds."
        )
        marked = (
            f"{subject} runs twice-weekly. The sentence does not choose the days, fix spacing, "
            "or report whether a run succeeds."
        )
        if bucket == 0:
            question = "Which pair of weekdays must contain the launches?"
            options = ["monday_and_thursday", "tuesday_and_friday", "weekend_days", "cannot_tell"]
            answer = "cannot_tell"
            probe = "weekday_not_supplied"
        elif bucket == 1:
            question = "Does this wording require equal gaps between the two launches within a week?"
            options = ["required", "not_required", "cannot_tell"]
            answer = "not_required"
            probe = "spacing_not_supplied"
        else:
            question = "What execution outcome is established for the latest planned launch?"
            options = ["confirmed_done", "confirmed_failed", "cannot_tell"]
            answer = "cannot_tell"
            probe = "completion_not_supplied"
    else:
        english = (
            f"{subject} has one scheduled recurrence at intervals of two schedule weeks from a "
            "separately established anchor. This sentence does not supply that anchor, a clock time, "
            "or a successful execution result."
        )
        marked = (
            f"{subject} runs every-two-weeks. This sentence does not supply the external anchor, "
            "a clock time, or a successful execution result."
        )
        if bucket == 0:
            question = "What is the calendar date of the first launch?"
            options = ["first_monday", "first_friday", "month_start", "cannot_tell"]
            answer = "cannot_tell"
            probe = "anchor_not_supplied"
        elif bucket == 1:
            question = "What clock reading must the recurrence use?"
            options = ["midnight", "noon", "business_close", "cannot_tell"]
            answer = "cannot_tell"
            probe = "clock_not_supplied"
        else:
            question = "What execution outcome is established for the latest planned launch?"
            options = ["confirmed_done", "confirmed_failed", "cannot_tell"]
            answer = "cannot_tell"
            probe = "completion_not_supplied"
    return {
        "id": f"real-{form}-{index + 1:03d}",
        "english": english,
        "ainglish": marked,
        "question": question,
        "options": rotate(options, index),
        "answer": answer,
        "strata": {"form": form, "probe": probe},
    }


def build(form: str) -> dict:
    real = []
    for index, subject in enumerate(SUBJECTS[:100]):
        real.append(count_item(form, subject, index) if index < 70
                    else overread_item(form, subject, index))
    assert len(real) == 100
    assert len({row["id"] for row in real}) == 100
    assert sum(row["strata"]["probe"] == "cadence_count" for row in real) == 70
    items = calibration_items(form) + real
    document = {
        "kind": "ainglish.panel.items.v1",
        "proposal": "twice-weekly-every-two-weeks-split-biweekly-into-its-two-inc",
        "form": form,
        "baseline": "complete_careful_english",
        "real_items": 100,
        "calibration_items": 12,
        "sha256": canonical_sha(items),
        "items": items,
    }
    return document


def main() -> None:
    receipts = {}
    for form in ("twice-weekly", "every-two-weeks"):
        document = build(form)
        name = f"{form}-careful-items.json"
        path = ROOT / name
        path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        receipts[name] = {
            "items_sha256": document["sha256"],
            "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "real_items": document["real_items"],
            "calibration_items": document["calibration_items"],
        }
    print(json.dumps(receipts, indent=2))


if __name__ == "__main__":
    main()
