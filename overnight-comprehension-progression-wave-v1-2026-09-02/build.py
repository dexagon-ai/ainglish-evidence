#!/usr/bin/env python3
"""Build three fresh 160-item Ainglish comprehension carriers without inference."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(items: list[dict]) -> str:
    return sha256(canonical(items)).hexdigest()


def rotated(answer: str, distractors: list[str], index: int) -> list[str]:
    values: list[str] = []
    for value in [answer, *distractors]:
        if value not in values:
            values.append(value)
        if len(values) == 4:
            break
    assert len(values) == 4 and answer in values
    shift = index % 4
    return values[shift:] + values[:shift]


def calibrations(prefix: str) -> list[dict]:
    rows = []
    nouns = [
        ("amber token", "locker 17"), ("blue key", "drawer 22"),
        ("cedar card", "cabinet 14"), ("dune badge", "vault 19"),
        ("elm seal", "locker 23"), ("flint pass", "drawer 25"),
        ("granite tag", "cabinet 18"), ("hazel chip", "vault 12"),
        ("indigo note", "locker 21"), ("jade disk", "drawer 15"),
        ("kelp token", "cabinet 24"), ("linen key", "vault 16"),
        ("maple card", "locker 13"), ("nickel badge", "drawer 20"),
        ("ochre seal", "cabinet 11"), ("pearl pass", "vault 26"),
    ]
    for i, (thing, location) in enumerate(nouns):
        rows.append({
            "id": f"{prefix}-cal-{i + 1:02d}",
            "calibration": True,
            "english": f"A sealed inventory note mentions the {thing}, but gives no location.",
            "ainglish": f"A sealed inventory note states that the {thing} is in {location}.",
            "question": f"Where does the note state that the {thing} is?",
            "options": rotated(location, ["the dispatch desk", "the archive room", "the location is not stated"], i),
            "answer": location,
            "probe": "construct-free explicit-location planted effect",
        })
    return rows


ACK_DOMAINS = [
    ("policy", "policy-v{n}@clause-{m}"),
    ("contract", "contract-{n}@schedule-{m}"),
    ("design review", "design-{n}@comment-{m}"),
    ("incident handoff", "incident-{n}@handoff-{m}"),
    ("safety instruction", "safety-{n}@step-{m}"),
    ("workplace request", "request-{n}@revision-{m}"),
    ("change control", "change-{n}@patch-{m}"),
    ("audit finding", "audit-{n}@finding-{m}"),
]
PRINCIPALS = ["Ari", "Bela", "Cato", "Dina", "Eli", "Faye", "Gus", "Hana"]


def ack_items() -> list[dict]:
    rows = []
    forms = ["ack-as-receipt", "ack-as-agreement"]
    states = {
        "ack-as-receipt": "receipt=yes; agreement=unasserted; authority=unasserted; compliance=unasserted",
        "ack-as-agreement": "receipt=yes; agreement=yes; authority=unasserted; compliance=unasserted",
    }
    base_distractors = [
        "receipt=yes; agreement=no; authority=unasserted; compliance=unasserted",
        "receipt=yes; agreement=yes; authority=yes; compliance=yes",
        "receipt=unasserted; agreement=unasserted; authority=unasserted; compliance=unasserted",
    ]
    for form in forms:
        for i in range(80):
            domain, ref_pattern = ACK_DOMAINS[i % len(ACK_DOMAINS)]
            principal = PRINCIPALS[(i + (0 if form == forms[0] else 3)) % len(PRINCIPALS)]
            reference = ref_pattern.format(n=100 + i, m=1 + (i % 9))
            comparator = "careful" if i % 2 == 0 else "bare"
            if form == "ack-as-receipt":
                careful = (
                    f"{principal} deliberately signalled that {principal} received and could identify exact "
                    f"{reference}; agreement, authority, and compliance remain unasserted."
                )
            else:
                careful = (
                    f"{principal} deliberately signalled receipt of exact {reference} and substantive agreement "
                    "with its bounded content; authority and compliance remain unasserted."
                )
            english = careful if comparator == "careful" else f"{principal} acknowledged {reference}."
            ainglish = f"{principal} {form}({reference})."
            edge = ["plain response", "later objection", "no decision authority", "no implementation record"][i % 4]
            if edge == "later objection" and form == "ack-as-receipt" and comparator == "careful":
                english += f" {principal} later objected to its content."
                ainglish += f" {principal} later objected to its content."
                answer = "receipt=yes; agreement=no; authority=unasserted; compliance=unasserted"
            elif edge == "no decision authority" and comparator == "careful":
                english += " No evidence of decision authority is supplied."
                ainglish += " No evidence of decision authority is supplied."
                answer = states[form]
            elif edge == "no implementation record" and comparator == "careful":
                english += " No implementation record is supplied."
                ainglish += " No implementation record is supplied."
                answer = states[form]
            else:
                answer = states[form]
            distractors = [value for value in [*base_distractors, *states.values()] if value != answer]
            rows.append({
                "id": f"ack-{form}-{i + 1:03d}",
                "english": english,
                "ainglish": ainglish,
                "question": f"According to this {domain} response record, which exact status is established for {principal}?",
                "options": rotated(answer, distractors, i + (0 if form == forms[0] else 1)),
                "answer": answer,
                "form": form,
                "comparator": comparator,
                "settlement_stratum": f"{form}/{comparator}",
                "strata": {"domain": domain, "edge": edge, "reference": reference},
            })
    return rows + calibrations("ack")


CAUSE_DOMAINS = [
    ("incident response", "service restart", "restart-{n}@evt-{m}"),
    ("file operation", "file deletion", "delete-{n}@evt-{m}"),
    ("deployment", "deployment rollback", "rollback-{n}@evt-{m}"),
    ("moderation", "account suspension", "suspend-{n}@evt-{m}"),
    ("payments", "payment refund", "refund-{n}@evt-{m}"),
    ("scheduling", "meeting cancellation", "cancel-{n}@evt-{m}"),
    ("access control", "credential revocation", "revoke-{n}@evt-{m}"),
    ("safety", "emergency shutdown", "shutdown-{n}@evt-{m}"),
]


def cause_items() -> list[dict]:
    rows = []
    forms = ["cause-question", "justification-question"]
    answers = {
        "cause-question": "the triggers, inputs, state transitions, or process that produced the event",
        "justification-question": "the rule, authority, obligation, goal, value, or trade-off that warranted the action, including that none did",
    }
    distractors = [
        "the identity of whoever should be blamed",
        "a promise that the event will be reversed",
        "both mechanism and valid warrant are presupposed by the question",
    ]
    intentionality = [
        "known cause; no valid warrant", "valid warrant; proximate cause unknown",
        "one fact may be both cause and warrant", "accidental event; no attributable choice",
        "coercion", "automation executing a policy", "authorized act produced by a bug",
        "unjustified act with a complete trace",
    ]
    actors = ["Ari", "Bela", "Cato", "Dina", "Eli", "Faye", "Gus", "Hana"]
    for form in forms:
        for i in range(80):
            domain, action, ref_pattern = CAUSE_DOMAINS[i % len(CAUSE_DOMAINS)]
            actor = actors[(i + (0 if form == forms[0] else 2)) % len(actors)]
            reference = ref_pattern.format(n=200 + i, m=10 + (i % 17))
            comparator = "careful" if i % 2 == 0 else "bare"
            if form == "cause-question":
                careful = (
                    f"What triggers, inputs, state transitions, decisions, or faults produced exact {action} event "
                    f"{reference}? This asks for mechanism, not whether the event was warranted."
                )
            else:
                careful = (
                    f"What rule, authority, obligation, goal, value, or trade-off, if any, made {actor}'s exact "
                    f"{action} action {reference} warranted? 'No valid basis' is a responsive answer; mechanism is not requested."
                )
            english = careful if comparator == "careful" else f"Why did {actor} perform {action} {reference}?"
            ainglish = f"{form}({reference})?"
            answer = answers[form]
            rows.append({
                "id": f"why-{form}-{i + 1:03d}",
                "english": english,
                "ainglish": ainglish,
                "question": "Which kind of answer directly satisfies this question without adding a relation it did not request?",
                "options": rotated(answer, distractors, i + (0 if form == forms[0] else 2)),
                "answer": answer,
                "form": form,
                "comparator": comparator,
                "settlement_stratum": f"{form}/{comparator}",
                "strata": {"domain": domain, "intentionality": intentionality[i % len(intentionality)], "reference": reference},
            })
    return rows + calibrations("why")


VALUE_CASES = [
    ("personnel record", "middle-name", "employee"),
    ("service catalog", "pager-number", "service"),
    ("medical table", "allergy-code", "patient"),
    ("research table", "follow-up-date", "participant"),
    ("public form", "licence-number", "applicant"),
    ("audit export", "approval-id", "transaction"),
    ("API export", "owner-email", "resource"),
    ("asset register", "engine-serial", "asset"),
    ("case file", "salary", "subject"),
    ("inventory", "expiry-date", "item"),
]


def value_items() -> list[dict]:
    rows = []
    vectors = {
        "value-unknown": "property-applies=yes; ordinary-value-existence=unresolved; deliberate-source-removal=no",
        "value-none": "property-applies=yes; ordinary-value-existence=false; deliberate-source-removal=no",
        "value-redacted": "property-applies=yes; ordinary-source-value-existed=true; deliberate-source-removal=yes",
        "value-inapplicable": "property-applies=no; ordinary-value-existence=not-meaningful; deliberate-source-removal=no",
    }
    all_vectors = list(vectors.values())
    for form_index, form in enumerate(vectors):
        for i in range(40):
            domain, prop, subject_kind = VALUE_CASES[i % len(VALUE_CASES)]
            subject = f"{subject_kind}-{300 + form_index * 40 + i}"
            redactor = ["HR", "audit-team", "policy-7", "records-office"][i % 4]
            boundary = ["retry-count=0", "enabled=false", "note=''", "tags=[]"][i % 4]
            if form == "value-unknown":
                ainglish_value = "value-unknown"
                careful = (
                    f"The {prop} property applies to {subject}, but this record establishes neither whether an ordinary "
                    "value exists nor what it is."
                )
            elif form == "value-none":
                ainglish_value = "value-none"
                careful = (
                    f"The {prop} property applies to {subject}, and under this record's schema, scope, and time no ordinary value exists."
                )
            elif form == "value-redacted":
                ainglish_value = f"value-redacted({redactor})"
                careful = (
                    f"The {prop} property applies to {subject}; an ordinary source value existed and {redactor} deliberately "
                    "removed it from this representation."
                )
            else:
                ainglish_value = "value-inapplicable"
                careful = (
                    f"Under this record's schema, the {prop} property does not apply to {subject}; asking it for an ordinary value is ill-typed."
                )
            suffix = f" A neighbouring field, {boundary}, is an ordinary supplied value and is not a missing-value marker."
            answer = vectors[form]
            distractors = [value for value in all_vectors if value != answer]
            rows.append({
                "id": f"missing-{form}-{i + 1:02d}",
                "english": careful + suffix,
                "ainglish": f"{prop}({subject}) = {ainglish_value}." + suffix,
                "question": f"Which exact semantic vector does the {domain} record assert for {prop}({subject})?",
                "options": rotated(answer, distractors, i + form_index),
                "answer": answer,
                "form": form,
                "comparator": "careful",
                "settlement_stratum": form,
                "strata": {"domain": domain, "boundary_control": boundary, "redactor": redactor if form == "value-redacted" else None},
            })
    return rows + calibrations("missing")


def write(name: str, slug: str, construct: str, items: list[dict], strata: list[str]) -> dict:
    payload = {
        "kind": "dexagon.ainglish.overnight-comprehension-carrier.v1",
        "proposal_revision": slug,
        "construct": construct,
        "comparison": "registered compact form versus the committed comparator named per item",
        "reader_calls": 0,
        "items": items,
    }
    path = ROOT / f"{name}.items.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    real = [row for row in items if not row.get("calibration")]
    cal = [row for row in items if row.get("calibration")]
    counts = Counter(row["settlement_stratum"] for row in real)
    return {
        "name": name,
        "slug": slug,
        "construct": construct,
        "file": path.name,
        "items_sha256": digest(items),
        "scientific_items": len(real),
        "calibration_items": len(cal),
        "settlement_strata": [{"id": value, "weight": 1} for value in strata],
        "stratum_counts": dict(sorted(counts.items())),
    }


def main() -> None:
    campaigns = [
        write(
            "acknowledgement-type",
            "p-ack-as-receipt-r-p-ack-as-agreement-r",
            "ack-as-receipt / ack-as-agreement",
            ack_items(),
            ["ack-as-receipt/careful", "ack-as-receipt/bare", "ack-as-agreement/careful", "ack-as-agreement/bare"],
        ),
        write(
            "why-relation",
            "cause-question-event-ref-justification-question-action-ref",
            "cause-question / justification-question",
            cause_items(),
            ["cause-question/careful", "cause-question/bare", "justification-question/careful", "justification-question/bare"],
        ),
        write(
            "typed-missing-value",
            "value-unknown-value-none-value-redacted-redactor-ref-value",
            "value-unknown / value-none / value-redacted / value-inapplicable",
            value_items(),
            ["value-unknown", "value-none", "value-redacted", "value-inapplicable"],
        ),
    ]
    index = {
        "kind": "dexagon.ainglish.overnight-comprehension-wave.v1",
        "model_calls": 0,
        "campaigns": {row["name"]: row for row in campaigns},
    }
    index["content_sha256"] = sha256(canonical(index)).hexdigest()
    (ROOT / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(index, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
