#!/usr/bin/env python3
"""Build eight form-specific, no-reader flagship comprehension carriers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SEED = 2026082603
OPTIONS = ["yes", "no", "cannot tell"]
SCENARIOS = [
    ("harbour controller", "routing manifest", "the berth assignment"),
    ("forest observatory", "sensor profile", "the sampling interval"),
    ("ceramic archive", "catalogue record", "the glaze classification"),
    ("polar depot", "packing specification", "the insulation grade"),
    ("river laboratory", "analysis workbook", "the nitrate threshold"),
    ("alpine nursery", "propagation schedule", "the watering interval"),
    ("lunar relay", "telemetry schema", "the packet version"),
    ("tidal station", "maintenance plan", "the pump sequence"),
    ("museum store", "condition report", "the humidity limit"),
    ("desert clinic", "stock ledger", "the reserve quantity"),
    ("orchard cooperative", "harvest sheet", "the grading rule"),
    ("aurora survey", "calibration table", "the exposure offset"),
]

FORMS = {
    "same-one": {
        "slug": "same-one-same-kind-same-name-mark-whether-same-claims-one-sh-2",
        "careful": lambda place, obj, prop, n: (
            f"At the {place}, desks A and B open one single shared {obj}; a change through either "
            f"desk changes {prop} in the one object visible through both."
        ),
        "marked": lambda place, obj, prop, n: (
            f"At the {place}, desks A and B open the same-one {obj} for {prop}."
        ),
        "questions": [
            (lambda place, obj, prop: f"If desk A edits {prop}, is that edit visible through desk B without a copy or sync step?", "yes"),
            (lambda place, obj, prop: f"Can the two desks independently diverge in {prop} while the stated relationship remains true and the object is not replaced?", "no"),
        ],
    },
    "same-kind": {
        "slug": "same-one-same-kind-same-name-mark-whether-same-claims-one-sh-2",
        "careful": lambda place, obj, prop, n: (
            f"At the {place}, desk A has a distinct {obj} whose content was verified equal to desk B's "
            f"under a field-by-field check at checkpoint {n}; the copies may diverge after that checkpoint "
            "and changes do not propagate."
        ),
        "marked": lambda place, obj, prop, n: (
            f"At the {place}, desk A has a same-kind {obj} to desk B's (field-by-field check, as of checkpoint {n})."
        ),
        "questions": [
            (lambda place, obj, prop: f"Can desk A later change {prop} without that change propagating to desk B?", "yes"),
            (lambda place, obj, prop: f"Does the statement claim the desks reach one single shared {obj}?", "no"),
        ],
    },
    "same-name": {
        "slug": "same-one-same-kind-same-name-mark-whether-same-claims-one-sh-2",
        "careful": lambda place, obj, prop, n: (
            f"At the {place}, desks A and B each have a {obj} with the matching identifier 'series-{n}'; "
            "content equality is not claimed and has not been verified."
        ),
        "marked": lambda place, obj, prop, n: (
            f"At the {place}, desks A and B carry a same-name {obj}, 'series-{n}'."
        ),
        "questions": [
            (lambda place, obj, prop: f"Must a receiver verify {prop} before treating the two records as content-equal?", "yes"),
            (lambda place, obj, prop: f"Does the statement establish that {prop} is equal at the two desks?", "no"),
        ],
    },
    "by-construction": {
        "slug": "by-construction-by-rule-in-practice-mark-whether-a-standing-",
        "careful": lambda place, obj, prop, n: (
            f"At the {place}, the property that {prop} remains internally consistent is enforced by "
            f"how the {obj} is built: while the system remains "
            "unchanged, an exception cannot occur; observing one falsifies this claim or proves a change."
        ),
        "marked": lambda place, obj, prop, n: f"At the {place}, {prop} remains internally consistent by-construction in the {obj}.",
        "questions": [
            (lambda place, obj, prop: "Would observing an exception falsify the standing claim or show that the system changed?", "yes"),
            (lambda place, obj, prop: "Can an exception occur while the stated construction remains unchanged and the claim remains true?", "no"),
        ],
    },
    "by-rule": {
        "slug": "by-construction-by-rule-in-practice-mark-whether-a-standing-",
        "careful": lambda place, obj, prop, n: (
            f"At the {place}, a standing rule requires {prop} to remain internally consistent in "
            f"the {obj}; exceptions can occur, "
            "and each exception is a violation whose owner owes repair or explanation."
        ),
        "marked": lambda place, obj, prop, n: f"At the {place}, {prop} remains internally consistent by-rule in the {obj}.",
        "questions": [
            (lambda place, obj, prop: "Is a real exception possible even though it would be a rule violation?", "yes"),
            (lambda place, obj, prop: "Would an exception be mere surprising news with nobody owing repair or explanation?", "no"),
        ],
    },
    "in-practice": {
        "slug": "by-construction-by-rule-in-practice-mark-whether-a-standing-",
        "careful": lambda place, obj, prop, n: (
            f"At the {place}, {prop} has remained internally consistent in every observed case for "
            f"the {obj}; nothing claimed "
            "prevents or forbids an exception, and one would be news rather than a breach."
        ),
        "marked": lambda place, obj, prop, n: f"At the {place}, {prop} remains internally consistent in-practice for the {obj}.",
        "questions": [
            (lambda place, obj, prop: "Could a future exception be compatible with the statement rather than a breach?", "yes"),
            (lambda place, obj, prop: "Does the statement guarantee that an exception is impossible while the system remains unchanged?", "no"),
        ],
    },
    "among-others": {
        "slug": "among-others-and-no-others-is-the-list-the-whole-list-2",
        "careful": lambda place, obj, prop, n: (
            f"At the {place}, the {obj} lists cedar-{n} and basalt-{n} as members, and the list is not "
            "claimed complete; unlisted same-kind candidates are neither admitted nor excluded."
        ),
        "marked": lambda place, obj, prop, n: f"At the {place}, the {obj} lists cedar-{n}, basalt-{n}, among-others.",
        "questions": [
            (lambda place, obj, prop: f"Can an unlisted same-kind member exist compatibly with this {obj}?", "yes"),
            (lambda place, obj, prop: "Does the statement exclude every unlisted same-kind candidate in scope?", "no"),
        ],
    },
    "and-no-others": {
        "slug": "among-others-and-no-others-is-the-list-the-whole-list-2",
        "careful": lambda place, obj, prop, n: (
            f"At the {place}, the {obj} lists cedar-{n} and basalt-{n} as the complete same-kind set "
            "in scope; every unlisted same-kind candidate is excluded."
        ),
        "marked": lambda place, obj, prop, n: f"At the {place}, the {obj} lists cedar-{n}, basalt-{n}, and-no-others.",
        "questions": [
            (lambda place, obj, prop: "Does the statement exclude every unlisted same-kind candidate in scope?", "yes"),
            (lambda place, obj, prop: f"Can an additional unlisted same-kind member exist compatibly with this {obj}?", "no"),
        ],
    },
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def rotate(values: list[str], amount: int) -> list[str]:
    shift = amount % len(values)
    return values[shift:] + values[:shift]


def bind_answer(answer: str, position: int) -> list[str]:
    ordered = [answer] + [option for option in OPTIONS if option != answer]
    target = position % len(ordered)
    return ordered if target == 0 else ordered[-target:] + ordered[:-target]


def build_form(form: str, spec: dict[str, object]) -> tuple[dict[str, object], dict[str, object]]:
    scientific: list[dict[str, object]] = []
    for cycle in range(4):
        for scenario_index, (place, obj, prop) in enumerate(SCENARIOS):
            index = cycle * len(SCENARIOS) + scenario_index
            checkpoint = 910 + index
            question_fn, answer = spec["questions"][index % 2]
            english = f"Review {checkpoint}. " + spec["careful"](place, obj, prop, checkpoint)
            ainglish = f"Review {checkpoint}. " + spec["marked"](place, obj, prop, checkpoint)
            scientific.append({
                "id": f"flagship-bank-{form}-{index + 1:03d}",
                "english": english,
                "ainglish": ainglish,
                "question": question_fn(place, obj, prop),
                "options": bind_answer(answer, index),
                "answer": answer,
                "marker": form,
                "scenario_id": f"bank-{form}-{checkpoint}",
                "strata": {"domain": place, "polarity": "positive" if answer == "yes" else "negative"},
            })
    calibration: list[dict[str, object]] = []
    for index in range(8):
        token = f"control-{form}-{index + 31}"
        calibration.append({
            "id": f"flagship-bank-{form}-cal-{index + 1:02d}",
            "calibration": True,
            "english": f"The dispatch note mentions {token}, but gives no bay.",
            "ainglish": f"The dispatch note explicitly places {token} in bay twenty-three.",
            "question": "Does the note state that bay twenty-three is the place to inspect?",
            "options": rotate(["yes", "cannot tell"], index),
            "answer": "yes",
            "set": "construct-free explicit-location positive control",
        })
    rows = scientific + calibration
    assert len(scientific) == 48 and len(calibration) == 8
    assert len({row["id"] for row in rows}) == 56
    assert len({(row["english"], row["ainglish"]) for row in scientific}) == 48
    assert sum(row["answer"] == "yes" for row in scientific) == 24
    assert sum(row["answer"] == "no" for row in scientific) == 24
    assert {position: sum(row["options"].index(row["answer"]) == position for row in scientific)
            for position in range(3)} == {0: 16, 1: 16, 2: 16}
    digest = hashlib.sha256(canonical(rows)).hexdigest()
    payload = {
        "kind": "ainglish.flagship-form-comprehension-carrier.v1",
        "form": form,
        "proposal_revision": spec["slug"],
        "seed": SEED,
        "sha256": digest,
        "reader_calls": 0,
        "items": rows,
    }
    receipt = {
        "file": f"items-{form}.json",
        "items_sha256": digest,
        "scientific": 48,
        "calibration": 8,
        "yes": 24,
        "no": 24,
        "answer_positions": {"0": 16, "1": 16, "2": 16},
    }
    return payload, receipt


def main() -> None:
    campaigns: dict[str, object] = {}
    for form, spec in FORMS.items():
        payload, receipt = build_form(form, spec)
        (ROOT / receipt["file"]).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        campaigns[form] = receipt
    index = {
        "kind": "ainglish.flagship-carrier-bank.v1",
        "seed": SEED,
        "reader_calls": 0,
        "campaigns": campaigns,
        "execution_gate": {
            "same-one": "carrier-ready: token prerequisite confirmed",
            "same-kind": "carrier-ready: token prerequisite confirmed",
            "same-name": "carrier-ready: token prerequisite confirmed",
            "by-construction": "carrier-ready: token prerequisite confirmed",
            "by-rule": "carrier-ready: token prerequisite confirmed",
            "in-practice": "carrier-ready: token prerequisite confirmed",
            "among-others": "blocked: proposal seconded and token prerequisite missing",
            "and-no-others": "blocked: proposal seconded and token prerequisite missing",
        },
    }
    index["content_sha256"] = hashlib.sha256(canonical(index)).hexdigest()
    (ROOT / "index.json").write_text(json.dumps(index, indent=2) + "\n")
    print(json.dumps(index, indent=2))


if __name__ == "__main__":
    main()
