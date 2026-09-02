#!/usr/bin/env python3
"""Build a wholly fresh 288-item replication carrier without inference."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FORMS = ["rather-not", "fine-either-way", "would-welcome"]
POWERS = [
    ("peer", "Ari", "Bela"),
    ("superior", "manager Cato", "report Dina"),
    ("subordinate", "report Eli", "manager Faye"),
]
ACTIONS = [
    ("code review", "review patch {n}"),
    ("documentation", "update guide {n}"),
    ("testing", "rerun test group {n}"),
    ("scheduling", "attend planning slot {n}"),
    ("communication etiquette", "send follow-up note {n}"),
    ("purchasing", "request quote {n}"),
    ("social invitation", "join coffee break {n}"),
    ("incident handoff", "read handoff appendix {n}"),
]


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(items: list[dict]) -> str:
    return sha256(canonical(items)).hexdigest()


def options(answer: str, index: int) -> list[str]:
    values = ["yes", "no", "cannot tell from the message"]
    shift = index % 3
    values = values[shift:] + values[:shift]
    assert answer in values
    return values


def calibrations() -> list[dict]:
    rows = []
    things = [
        ("amber token", "locker 31"), ("blue key", "drawer 34"),
        ("cedar card", "cabinet 38"), ("dune badge", "vault 33"),
        ("elm seal", "locker 37"), ("flint pass", "drawer 32"),
        ("granite tag", "cabinet 36"), ("hazel chip", "vault 35"),
    ]
    for i, (thing, location) in enumerate(things):
        choices = [location, "the dispatch desk", "the location is not stated"]
        shift = i % 3
        rows.append({
            "id": f"preference-cal-{i + 1:02d}",
            "calibration": True,
            "english": f"A sealed inventory note mentions the {thing}, but gives no location.",
            "ainglish": f"A sealed inventory note states that the {thing} is in {location}.",
            "question": f"Where does the note state that the {thing} is?",
            "options": choices[shift:] + choices[:shift],
            "answer": location,
            "probe": "construct-free explicit-location planted effect",
        })
    return rows


def careful(form: str, sender: str, receiver: str, action: str) -> str:
    release = f'{sender} tells {receiver}: “You are not required to {action}.'
    if form == "rather-not":
        return release + " Doing it remains permitted, but I want you to omit it; omitting it is not a failure.”"
    if form == "fine-either-way":
        return release + " Doing it and omitting it are equally acceptable to me; neither is a failure.”"
    return release + " I would like you to do it, but omitting it remains acceptable and is not a failure.”"


def marked(form: str, sender: str, receiver: str, action: str) -> str:
    return f'{sender} tells {receiver}: “You do not need to {action}, {form}.”'


def main() -> None:
    preference_answers = {
        "rather-not": ("yes", "no"),
        "fine-either-way": ("yes", "yes"),
        "would-welcome": ("no", "yes"),
    }
    probes = [
        ("preference", "The receiver omitted the optional action. Did the sender get the outcome they wanted?", 0),
        ("preference", "The receiver performed the optional action. Did the sender get the outcome they wanted?", 1),
        ("obligation", "Would performing the optional action violate the instruction?", None),
        ("obligation", "Would omitting the optional action count as a failure to comply?", None),
    ]
    rows = []
    for form_index, form in enumerate(FORMS):
        for power_index, (power, sender, receiver) in enumerate(POWERS):
            for i, (domain, action_pattern) in enumerate(ACTIONS):
                base_id = f"fresh-{power}-{i + 1:02d}"
                action = action_pattern.format(n=500 + power_index * 20 + i)
                for probe_index, (outcome, question, branch_index) in enumerate(probes):
                    answer = "no" if branch_index is None else preference_answers[form][branch_index]
                    rows.append({
                        "id": f"{base_id}-{form}-probe-{probe_index + 1}",
                        "english": careful(form, sender, receiver, action),
                        "ainglish": marked(form, sender, receiver, action),
                        "question": question,
                        "options": options(answer, form_index + power_index + i + probe_index),
                        "answer": answer,
                        "form": form,
                        "outcome": outcome,
                        "settlement_stratum": f"{form}-{outcome}",
                        "strata": {
                            "base_id": base_id,
                            "domain": domain,
                            "power_relationship": power,
                            "probe": probe_index + 1,
                        },
                    })
    items = rows + calibrations()
    payload = {
        "kind": "dexagon.ainglish.rather-not-dispute-replication-carrier.v2",
        "proposal_revision": "rather-not-fine-either-way-would-welcome-you-don-t-have-to-s-2",
        "construct": "rather-not / fine-either-way / would-welcome",
        "comparison": "registered compact form versus complete careful-English mapping",
        "replicates_hash": "b661b02842052ced7bc148b50fd4194c6084fbc27f1f70e22e45dd6af88e3d7d",
        "reader_calls": 0,
        "items": items,
    }
    (ROOT / "items.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    real = [row for row in items if not row.get("calibration")]
    index = {
        "kind": "dexagon.ainglish.rather-not-dispute-replication-index.v2",
        "items_file": "items.json",
        "items_sha256": digest(items),
        "scientific_items": len(real),
        "calibration_items": len(items) - len(real),
        "frames": len({(row["strata"]["base_id"], row["form"]) for row in real}),
        "forms": dict(sorted(Counter(row["form"] for row in real).items())),
        "outcomes": dict(sorted(Counter(row["outcome"] for row in real).items())),
        "settlement_strata": dict(sorted(Counter(row["settlement_stratum"] for row in real).items())),
        "replicates_hash": payload["replicates_hash"],
        "model_calls": 0,
    }
    index["content_sha256"] = sha256(canonical(index)).hexdigest()
    (ROOT / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(index, indent=2))


if __name__ == "__main__":
    main()
