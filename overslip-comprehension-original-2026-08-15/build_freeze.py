#!/usr/bin/env python3
"""Build the frozen overslip comprehension item set without reader calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OPTIONS = ["watchful supervision", "an accidental miss", "a deliberate skip", "cannot tell"]


def item(item_id, english, ainglish, answer, difficulty, **strata):
    shift = int(hashlib.sha256(item_id.encode()).hexdigest(), 16) % len(OPTIONS)
    options = OPTIONS[shift:] + OPTIONS[:shift]
    return {
        "id": item_id,
        "english": english,
        "ainglish": ainglish,
        "question": "What kind of event or role does the report's focal phrase describe?",
        "options": options,
        "answer": answer,
        "difficulty": difficulty,
        "strata": strata,
    }


def anchored_items():
    domains = [
        ("key rotation", "a reviewer owned the check", "the replacement key was accidentally absent from the vault"),
        ("model rollout", "a safety lead owned the review", "the rollback threshold was accidentally left out"),
        ("backup restore", "an operator owned the rehearsal", "one encrypted volume was accidentally missed"),
    ]
    frames = {
        "definite": ("The audit documented the {word} during {topic}.", "oversight", "overslip"),
        "genitive": ("The report examined the {word} of {topic}.", "oversight", "overslip"),
        "compound": ("The incident note labelled this an {word} failure in {topic}.", "oversight", "overslip"),
        "grammar_resolved": ("The postmortem recorded an {word} in {topic}.", "oversight", "overslip"),
    }
    rows = []
    for frame, (template, english_word, ainglish_word) in frames.items():
        for index, (topic, supervision_anchor, miss_anchor) in enumerate(domains, 1):
            shared = f" {supervision_anchor.capitalize()}, and {miss_anchor}."
            miss_pin = " The cited problem was the unnoticed absence, not the review arrangement."
            supervision_pin = " The cited role was the review arrangement, not the unnoticed absence."
            base_id = f"anchored-{frame}-{index}"
            rows.append(item(
                base_id + "-miss",
                template.format(word=english_word, topic=topic) + shared + miss_pin,
                template.format(word=ainglish_word, topic=topic) + shared + miss_pin,
                "an accidental miss",
                1,
                cell="anchored_ambiguity",
                condition="no_gloss_context_pinned",
                frame=frame,
                intent="accidental_miss",
                voice="nominal",
                validity="conformant",
            ))
            rows.append(item(
                base_id + "-supervision",
                ((f"The postmortem recorded active supervision in {topic}." if frame == "grammar_resolved"
                  else template.format(word=english_word, topic=topic)) + shared + supervision_pin),
                ((f"The postmortem recorded oversight in {topic}." if frame == "grammar_resolved"
                  else template.format(word=english_word, topic=topic)) + shared + supervision_pin),
                "watchful supervision",
                1,
                cell="anchored_ambiguity",
                condition="no_gloss_context_pinned",
                frame=frame,
                intent="supervision",
                voice="nominal",
                validity="conformant",
            ))
    return rows


def cold_noun_items():
    subjects = [
        "key rotation", "model rollout", "backup restore", "access review",
        "invoice import", "certificate renewal", "queue migration", "sensor calibration",
    ]
    frames = [
        "The incident register records the {word} of {topic}.",
        "The audit entry calls the {topic} problem an {word}.",
        "The handover notes an {word} in {topic}.",
        "The postmortem lists the {topic} {word}.",
    ]
    rows = []
    for index, topic in enumerate(subjects, 1):
        template = frames[(index - 1) % len(frames)]
        rows.append(item(
            f"cold-noun-{index:02d}",
            template.format(word="oversight", topic=topic),
            template.format(word="overslip", topic=topic),
            "an accidental miss",
            3,
            cell="cold_noun_decode",
            condition="no_gloss_no_anchor",
            frame=("genitive", "definite", "grammar_resolved", "compound")[(index - 1) % 4],
            intent="accidental_miss",
            voice="nominal",
            validity="conformant",
        ))
    return rows


def careful_verb_items():
    objects = [
        "the key rotation", "the rollback threshold", "one encrypted volume", "the access expiry",
        "the tax field", "the renewal alarm", "the dead-letter queue", "the drift warning",
    ]
    rows = []
    for index, obj in enumerate(objects, 1):
        passive = index % 2 == 0
        if passive:
            english = f"{obj.capitalize()} was unintentionally missed by the team."
            ainglish = f"{obj.capitalize()} was overslipped by the team."
            voice = "passive"
        else:
            english = f"The team failed to notice {obj}, unintentionally."
            ainglish = f"The team overslipped {obj}."
            voice = "active"
        rows.append(item(
            f"careful-verb-{index:02d}", english, ainglish, "an accidental miss", 2,
            cell="careful_mapping_verb",
            condition="no_gloss_meaning_matched",
            frame="verb",
            intent="accidental_miss",
            voice=voice,
            validity="conformant",
        ))
    return rows


def deliberate_controls():
    objects = [
        "the optional review", "the redundant checksum", "the staging rehearsal", "the legacy export",
        "the advisory warning", "the duplicate scan", "the old compatibility test", "the nonessential report",
    ]
    rows = []
    for index, obj in enumerate(objects, 1):
        passive = index % 2 == 0
        reason = "to meet the deadline" if index % 3 else "under an approved exception"
        if passive:
            english = f"{obj.capitalize()} was deliberately omitted by the team {reason}."
            ainglish = f"{obj.capitalize()} was deliberately overslipped by the team {reason}."
            voice = "passive"
        else:
            english = f"The team deliberately omitted {obj} {reason}."
            ainglish = f"The team deliberately overslipped {obj} {reason}."
            voice = "active"
        rows.append(item(
            f"deliberate-control-{index:02d}", english, ainglish, "a deliberate skip", 3,
            cell="deliberate_false_positive_control",
            condition="no_gloss_explicit_intent",
            frame="verb",
            intent="deliberate_skip",
            voice=voice,
            validity="intentional_misuse_probe",
        ))
    return rows


def calibration_items():
    targets = [
        "an accidental miss", "watchful supervision", "a deliberate skip",
        "an accidental miss", "watchful supervision", "a deliberate skip",
    ]
    rows = []
    for index, answer in enumerate(targets, 1):
        row = item(
            f"calibration-{index:02d}",
            "The event was entered in the record; its kind is not stated.",
            f"The event was entered in the record and explicitly classified as {answer}.",
            answer,
            0,
            cell="calibration",
            condition="planted_explicit_label",
            frame="control",
            intent=answer.replace(" ", "_"),
            voice="nominal",
            validity="calibration",
        )
        row["calibration"] = True
        rows.append(row)
    return rows


def canonical_digest(items):
    encoded = json.dumps(items, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def main():
    real = anchored_items() + cold_noun_items() + careful_verb_items() + deliberate_controls()
    calibration = calibration_items()
    assert len(real) == 48
    assert len({row["id"] for row in real}) == len(real)
    assert len(calibration) == 6
    for row in real + calibration:
        assert row["answer"] in row["options"]
    all_items = real + calibration
    documents = {
        "items.json": {"items": all_items, "sha256": canonical_digest(all_items)},
        "calibration.json": {"items": calibration, "sha256": canonical_digest(calibration)},
    }
    for name, document in documents.items():
        (ROOT / name).write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n")
        print(name, document["sha256"])


if __name__ == "__main__":
    main()
