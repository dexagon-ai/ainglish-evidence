#!/usr/bin/env python3
"""Freeze `will-as-*` answer-bearing items before any reader call."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FORCE_QUESTION = "Which account of the writer's relation to the result is licensed by this message?"
FORCE_OPTIONS = [
    "outcome_responsibility",
    "present_intention",
    "expectation_only",
    "cannot_tell",
]
ANSWER = {
    "will-as-promise": "outcome_responsibility",
    "will-as-plan": "present_intention",
    "will-as-forecast": "expectation_only",
}

TASKS = {
    "will-as-promise": [
        "review the pull request by Friday",
        "deliver the signed bundle before noon",
        "send the audit receipt after the run",
        "repay the twelve credits tomorrow",
        "preserve the frozen artifact",
        "repair the reported parser defect tonight",
        "attend the handoff call at 09:00",
        "return the borrowed drive on Monday",
        "publish the correction before voting closes",
        "keep the mirror available through the release",
        "write the migration note this afternoon",
        "close the incident loop before dawn",
    ],
    "will-as-plan": [
        "take the migration route",
        "review the logs after lunch",
        "deploy through the blue pool",
        "start with the appendix",
        "move the archive table first",
        "compare the three variants tomorrow",
        "travel on the morning train",
        "use the larger reader model",
        "ask the maintainer after the test run",
        "prepare the examples before the prose",
        "rebuild the index overnight",
        "inspect the second replica next",
    ],
    "will-as-forecast": [
        "finish the benchmark before sunset",
        "receive a response later today",
        "detect one timeout in the final batch",
        "see the cache warm after two requests",
        "need another pass over the glossary",
        "reach the same conclusion after replication",
        "encounter a merge conflict on the release branch",
        "find the queue empty by morning",
        "observe a small difference between tokenizers",
        "complete the download within an hour",
        "discover one stale link in the archive",
        "hear from the reviewer before the deadline",
    ],
}


def canonical_sha(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def rotate_options(index: int) -> list[str]:
    shift = index % len(FORCE_OPTIONS)
    return FORCE_OPTIONS[shift:] + FORCE_OPTIONS[:shift]


def comprehension_items() -> list[dict]:
    items = []
    index = 0
    for form, tasks in TASKS.items():
        for within_form, task in enumerate(tasks, 1):
            index += 1
            items.append({
                "id": f"will-force-C-{index:02d}",
                "english": f"I will {task}.",
                "ainglish": f"I {form} {task}.",
                "question": FORCE_QUESTION,
                "options": rotate_options(index - 1),
                "answer": ANSWER[form],
                "form": form,
                "comparison": "marked_vs_untyped_bare_will",
            })
    assert len(items) == 36
    return items


def careful_english(form: str, task: str) -> str:
    if form == "will-as-promise":
        return f"I promise to {task}; this statement commits me to bringing that result about."
    if form == "will-as-plan":
        return f"My current plan is to {task}; it may change, and I must tell you if it does."
    if form == "will-as-forecast":
        return f"I expect to {task}; this is a prediction and does not commit me to cause it."
    raise AssertionError(form)


def robustness_items() -> list[dict]:
    items = []
    index = 0
    for form, tasks in TASKS.items():
        for task in tasks[:8]:
            index += 1
            items.append({
                "id": f"will-force-R-{index:02d}",
                "english": careful_english(form, task),
                "ainglish": f"I {form} {task}.",
                "question": FORCE_QUESTION,
                "options": rotate_options(index + 1),
                "answer": ANSWER[form],
                "form": form,
                "comparison": "marked_vs_complete_careful_english",
            })
    assert len(items) == 24
    return items


def calibration_items() -> list[dict]:
    # Construct-free planted-effect controls: the ainglish-labelled arm spells
    # out a category and the other arm leaves it undecidable.  These certify the
    # reader/task pipeline, not any proposed marker.
    rows = [
        ("archive the ledger", "outcome_responsibility"),
        ("deliver the parcel", "present_intention"),
        ("finish before dusk", "expectation_only"),
        ("restore the index", "outcome_responsibility"),
        ("take the eastern route", "present_intention"),
        ("need a second attempt", "expectation_only"),
        ("send the receipt", "outcome_responsibility"),
        ("inspect the logs next", "present_intention"),
        ("see one failed cell", "expectation_only"),
        ("return the key", "outcome_responsibility"),
        ("start with the smaller file", "present_intention"),
        ("hear from the reviewer tomorrow", "expectation_only"),
    ]
    explicit = {
        "outcome_responsibility": "I undertake responsibility for bringing that result about.",
        "present_intention": "I am disclosing my present intended course, which may change.",
        "expectation_only": "I am stating only what I believe is likely to occur.",
    }
    return [
        {
            "id": f"will-force-K-{index:02d}",
            "english": f"I will {task}.",
            "ainglish": f"I will {task} {explicit[answer]}",
            "question": FORCE_QUESTION,
            "options": rotate_options(index + 2),
            "answer": answer,
            "calibration": True,
            "set": "construct_free_planted_effect",
        }
        for index, (task, answer) in enumerate(rows, 1)
    ]


def notice_diagnostic_items() -> list[dict]:
    question = (
        "If the writer later chooses a different course, what follow-up does this convention say "
        "the writer owes the addressee?"
    )
    options = ["notice_of_change", "the_original_outcome", "nothing", "cannot_tell"]
    items = []
    for index, task in enumerate(TASKS["will-as-plan"], 1):
        items.append({
            "id": f"will-notice-D-{index:02d}",
            "surface": f"I will-as-plan {task}.",
            "question": question,
            "options": options[index % 4:] + options[:index % 4],
            "answer_under_filed_convention": "notice_of_change",
            "status": "diagnostic_not_part_of_force-identification_score",
        })
    return items


def write_packet(filename: str, kind: str, items: list[dict]) -> dict:
    document = {"kind": kind, "sha256": canonical_sha(items), "items": items}
    path = ROOT / filename
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "path": path.name,
        "items": len(items),
        "canonical_items_sha256": document["sha256"],
        "exact_file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def main() -> None:
    receipts = [
        write_packet(
            "comprehension-items.json",
            "ainglish.panel.items.v1:will-force-marked-vs-bare",
            comprehension_items() + calibration_items(),
        ),
        write_packet(
            "robustness-items.json",
            "ainglish.panel.items.v1:will-force-marked-vs-careful-english",
            robustness_items(),
        ),
        write_packet(
            "robustness-calibration.json",
            "ainglish.panel.calibration.v1:will-force-construct-free",
            calibration_items(),
        ),
        write_packet(
            "notice-duty-diagnostic.json",
            "ainglish.diagnostic.v1:will-as-plan-notice-duty",
            notice_diagnostic_items(),
        ),
    ]
    (ROOT / "item-freeze-receipt.json").write_text(
        json.dumps({"reader_calls": 0, "files": receipts}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipts, indent=2))


if __name__ == "__main__":
    main()
