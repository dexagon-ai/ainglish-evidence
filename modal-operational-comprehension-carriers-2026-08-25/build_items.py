#!/usr/bin/env python3
"""Freeze five matched comprehension carriers without model or governance calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DOMAINS = [
    ("release", "publish the release"),
    ("operations", "restart the queue"),
    ("security", "rotate the access key"),
    ("research", "validate the sample"),
    ("finance", "settle the invoice"),
    ("transport", "open the route"),
    ("moderation", "resolve the appeal"),
    ("procurement", "accept the quotation"),
    ("education", "grade the submission"),
    ("health", "approve the specimen"),
]
SUBJECTS = ["Ava", "Bo", "Cy", "Diya", "Eli", "Fara", "Gus", "Hana"]


def canonical(rows: list[dict]) -> bytes:
    return json.dumps(rows, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def rotate(options: list[str], index: int) -> list[str]:
    shift = index % len(options)
    return options[shift:] + options[:shift]


def may_not() -> list[dict]:
    rows = []
    answers = [
        "rule-forbids=yes; nonoccurrence-epistemically-possible=no",
        "rule-forbids=no; nonoccurrence-epistemically-possible=yes",
        "rule-forbids=yes; nonoccurrence-epistemically-possible=yes",
        "rule-forbids=no; nonoccurrence-epistemically-possible=no",
    ]
    for index in range(160):
        form = "may-not-as-prohibition" if index % 2 == 0 else "may-not-as-possibility"
        domain, action = DOMAINS[(index // 2) % len(DOMAINS)]
        subject = SUBJECTS[(index // 20) % len(SUBJECTS)]
        cycle = index // 20 + 1
        if form.endswith("prohibition"):
            context = (
                f"In {domain} cycle {cycle}, the applicable policy is the only stated constraint; "
                "weather and equipment are explicitly favourable."
            )
            english = f"{context} The policy forbids {subject} to {action}."
            marked = f"{context} {subject} {form} {action}."
            answer = answers[0]
        else:
            context = (
                f"In {domain} cycle {cycle}, no rule forbids the act; the available evidence leaves "
                "both occurrence and non-occurrence live."
            )
            english = f"{context} It remains possible, given the evidence, that {subject} will not {action}."
            marked = f"{context} {subject} {form} {action}."
            answer = answers[1]
        rows.append({
            "id": f"may-not-{index + 1:03d}",
            "scenario_id": f"may-not-cell-{index // 2 + 1:03d}",
            "form": form,
            "english": english,
            "ainglish": marked,
            "question": (
                "From the target sentence itself, jointly classify: does an applicable rule forbid the act; "
                "and does the evidence leave non-occurrence possible?"
            ),
            "options": rotate(answers, index),
            "answer": answer,
            "strata": {"domain": domain, "polarity": "positive", "cycle": cycle},
        })
    return rows


def must() -> list[dict]:
    rows = []
    answers = [
        "sentence-creates-duty=yes; later-conflict-means=noncompliance",
        "sentence-creates-duty=no; later-conflict-means=mistaken-conclusion",
        "sentence-creates-duty=yes; later-conflict-means=mistaken-conclusion",
        "sentence-creates-duty=no; later-conflict-means=noncompliance",
    ]
    for index in range(128):
        form = "must-as-rule" if index % 2 == 0 else "must-as-inference"
        domain, action = DOMAINS[(index // 2) % len(DOMAINS)]
        subject = SUBJECTS[(index // 16) % len(SUBJECTS)]
        cycle = index // 16 + 1
        if form.endswith("rule"):
            context = f"The {domain} authority is issuing an operative requirement for cycle {cycle}."
            english = f"{context} The rule requires {subject} to {action}. Later, {subject} does not do so."
            answer = answers[0]
        else:
            context = f"The {domain} analyst is reporting a conclusion from complete but fallible records for cycle {cycle}."
            english = f"{context} The evidence entails that {subject} did {action}. Later, an authenticated log shows that this did not happen."
            answer = answers[1]
        marked = f"{context} {subject} {form} {action}. Later, an incompatible authenticated fact is learned."
        rows.append({
            "id": f"must-{index + 1:03d}",
            "scenario_id": f"must-cell-{index // 2 + 1:03d}",
            "form": form,
            "english": english,
            "ainglish": marked,
            "question": "Jointly classify what the target sentence did and what the later conflict establishes.",
            "options": rotate(answers, index),
            "answer": answer,
            "strata": {"domain": domain, "aspect": "perfect" if index % 4 < 2 else "simple", "cycle": cycle},
        })
    return rows


def should() -> list[dict]:
    rows = []
    options = [
        "a norm was breached; investigate the owed performance",
        "no norm was breached; revise the expectation",
        "the sentence does not determine which response applies",
    ]
    for index in range(100):
        form = "should-as-rule" if index % 2 == 0 else "should-as-forecast"
        domain, action = DOMAINS[(index // 2) % len(DOMAINS)]
        subject = SUBJECTS[(index // 20) % len(SUBJECTS)]
        deadline = f"checkpoint {index // 10 + 1}"
        context = (
            f"Both a standing norm and a statistical expectation exist in the {domain} context, so either reading "
            "would fit the background."
        )
        if form.endswith("rule"):
            english = f"{context} The operative norm says {subject} ought to {action} by {deadline}. It did not happen."
            answer = options[0]
        else:
            english = f"{context} The writer expects, but does not require, that {subject} will {action} by {deadline}. It did not happen."
            answer = options[1]
        marked = f"{context} {subject} {form} {action} by {deadline}. It did not happen."
        rows.append({
            "id": f"should-{index + 1:03d}",
            "scenario_id": f"should-cell-{index // 2 + 1:03d}",
            "form": form,
            "english": english,
            "ainglish": marked,
            "question": "What is the first justified response to the stated non-occurrence?",
            "options": rotate(options, index),
            "answer": answer,
            "strata": {"domain": domain, "complement": "agentive" if index % 4 < 2 else "stative", "deadline": deadline},
        })
    return rows


def will() -> list[dict]:
    rows = []
    answers = [
        "wronged-reader=yes; owed=outcome-itself",
        "wronged-reader=no; owed=notice-if-plan-changed",
        "wronged-reader=no; owed=nothing-beyond-honesty",
        "wronged-reader=no; owed=cannot-tell",
        "wronged-reader=yes; owed=notice-if-plan-changed",
        "wronged-reader=yes; owed=nothing-beyond-honesty",
    ]
    forms = ["will-as-promise", "will-as-plan", "will-as-forecast"]
    for index in range(120):
        form = forms[index % 3]
        domain, action = DOMAINS[(index // 3) % len(DOMAINS)]
        subject = SUBJECTS[(index // 15) % len(SUBJECTS)]
        cycle = index // 15 + 1
        if form.endswith("promise"):
            mapping = f"{subject} commits to the reader that {subject} will {action} in cycle {cycle}."
            answer = answers[0]
        elif form.endswith("plan"):
            mapping = f"{subject} reports a present plan to {action} in cycle {cycle}, owing notice if that plan changes but not guaranteeing the outcome."
            answer = answers[1]
        else:
            mapping = f"{subject} predicts that {subject} will {action} in cycle {cycle}, without making a commitment or reporting a plan."
            answer = answers[2]
        suffix = " The event does not happen, and the writer says nothing further."
        rows.append({
            "id": f"will-{index + 1:03d}",
            "scenario_id": f"will-cell-{index // 3 + 1:03d}",
            "form": form,
            "english": mapping + suffix,
            "ainglish": f"{subject} {form} {action} in cycle {cycle}." + suffix,
            "question": "Jointly classify whether the writer wronged the reader and what was owed from the moment of writing.",
            "options": rotate(answers, index),
            "answer": answer,
            "strata": {"domain": domain, "control": "high" if index % 2 == 0 else "limited", "cycle": cycle},
        })
    return rows


def retention() -> list[dict]:
    rows = []
    answers = [
        "retained=none; reverse-success=yes; terminal=failed-no-effects",
        "retained=successful-members; reverse-success=no; terminal=partial-result",
        "retained=none; reverse-success=no; terminal=failed-no-effects",
        "retained=successful-members; reverse-success=yes; terminal=partial-result",
    ]
    operations = ["copy records", "publish notices", "index files", "archive reports", "migrate rows"]
    for index in range(200):
        form = "all-or-nothing" if index % 2 == 0 else "keep-successes"
        domain, _ = DOMAINS[(index // 2) % len(DOMAINS)]
        operation = operations[(index // 10) % len(operations)]
        cycle = index // 20 + 1
        success_member = chr(ord("A") + (index % 3))
        failed_member = chr(ord("A") + ((index + 1) % 3))
        context = (
            f"A bounded {domain} batch in cycle {cycle} has three required members. Member {success_member} "
            f"successfully performs its {operation} effect; member {failed_member} then fails. All effects are "
            "reversible, auditable, and at terminal handoff."
        )
        if form == "all-or-nothing":
            english = context + " The batch policy retains no member effect unless every required member succeeds, and reverses any earlier success after a sibling failure."
            answer = answers[0]
        else:
            english = context + " The batch policy retains every valid successful member effect even when a sibling fails, while disclosing the partial result."
            answer = answers[1]
        marked = context + f" Policy: {form}."
        rows.append({
            "id": f"retention-{index + 1:03d}",
            "scenario_id": f"retention-cell-{index // 2 + 1:03d}",
            "form": form,
            "english": english,
            "ainglish": marked,
            "question": "Jointly classify the authoritative effects, reversal duty, and terminal state solely from sibling failure.",
            "options": rotate(answers, index),
            "answer": answer,
            "strata": {"domain": domain, "operation": operation, "failure_position": failed_member, "reversible": True},
        })
    return rows


def calibrations(campaign: str) -> list[dict]:
    rows = []
    for index, obj in enumerate(["amber card", "blue key", "cedar token", "dune seal", "elm badge", "fern pass", "gold tag", "hazel slip"]):
        rows.append({
            "id": f"{campaign}-cal-{index + 1:02d}",
            "calibration": True,
            "english": f"A note mentions the {obj} but provides no shelf number.",
            "ainglish": f"A note states that the {obj} is on shelf nine.",
            "question": "Does the note state that checking shelf nine would find the named object?",
            "options": rotate(["yes", "no", "cannot tell"], index),
            "answer": "yes",
            "set": "construct-free explicit-location known positive",
        })
    return rows


def main() -> None:
    builders = {
        "may-not": may_not,
        "must": must,
        "should": should,
        "will": will,
        "retention": retention,
    }
    index = {"kind": "ainglish.modal-operational-comprehension-carriers.v1", "campaigns": {}}
    panel_dir = ROOT / "panel"
    panel_dir.mkdir(exist_ok=True)
    for campaign, builder in builders.items():
        rows = builder()
        ids = [row["id"] for row in rows]
        assert len(ids) == len(set(ids))
        assert all(row["answer"] in row["options"] for row in rows)
        blob = canonical(rows)
        path = ROOT / f"{campaign}.items.json"
        path.write_bytes(blob + b"\n")
        panel_rows = rows + calibrations(campaign)
        panel_blob = canonical(panel_rows)
        panel_path = panel_dir / f"{campaign}.json"
        panel_path.write_text(json.dumps({
            "kind": "ainglish.modal-operational-comprehension-items.v1",
            "campaign": campaign,
            "sha256": hashlib.sha256(panel_blob).hexdigest(),
            "items": panel_rows,
        }, indent=2, ensure_ascii=False) + "\n")
        index["campaigns"][campaign] = {
            "rows": len(rows),
            "sha256": hashlib.sha256(blob).hexdigest(),
            "file": path.name,
            "panel_file": str(panel_path.relative_to(ROOT)),
            "panel_rows": len(panel_rows),
            "panel_sha256": hashlib.sha256(panel_blob).hexdigest(),
            "forms": {form: sum(row["form"] == form for row in rows) for form in sorted({row["form"] for row in rows})},
        }
    (ROOT / "index.json").write_text(json.dumps(index, indent=2, sort_keys=True) + "\n")
    print(json.dumps(index, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
