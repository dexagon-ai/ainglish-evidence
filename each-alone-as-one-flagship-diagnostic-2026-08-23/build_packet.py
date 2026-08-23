#!/usr/bin/env python3
"""Build and validate the each-alone / as-one flagship diagnostic packet."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FORMS = ("each-alone", "as-one")

# (domain, number word, integer, plural subject, past-tense verb, object, event noun)
ACTION_FRAMES = [
    ("verification", "three", 3, "agents", "verified", "the checkpoint", "verification"),
    ("governance", "four", 4, "reviewers", "approved", "the amendment", "approval"),
    ("operations", "five", 5, "operators", "restarted", "the queue", "restart"),
    ("security", "six", 6, "auditors", "inspected", "the access log", "inspection"),
    ("deployment", "two", 2, "maintainers", "published", "the release", "publication"),
    ("storage", "seven", 7, "replicas", "validated", "the snapshot", "validation"),
    ("incident", "eight", 8, "responders", "triaged", "the alert", "triage"),
    ("network", "nine", 9, "monitors", "probed", "the endpoint", "probe"),
    ("compliance", "ten", 10, "stewards", "signed", "the declaration", "signature"),
    ("archive", "twelve", 12, "custodians", "sealed", "the archive", "sealing"),
    ("science", "three", 3, "researchers", "analysed", "the specimen", "analysis"),
    ("logistics", "four", 4, "dispatchers", "released", "the shipment", "release"),
    ("finance", "five", 5, "accountants", "reconciled", "the ledger", "reconciliation"),
    ("education", "six", 6, "teachers", "graded", "the examination", "grading"),
    ("health", "two", 2, "clinicians", "reviewed", "the scan", "review"),
    ("media", "seven", 7, "editors", "published", "the correction", "publication"),
    ("manufacturing", "eight", 8, "inspectors", "tested", "the component", "test"),
    ("transport", "nine", 9, "controllers", "cleared", "the route", "clearance"),
    ("permissions", "three", 3, "administrators", "rotated", "the credential", "rotation"),
    ("backup", "four", 4, "technicians", "restored", "the database", "restoration"),
    ("quality", "five", 5, "testers", "certified", "the build", "certification"),
    ("legal", "six", 6, "witnesses", "attested", "the receipt", "attestation"),
    ("monitoring", "two", 2, "sentries", "checked", "the gate", "check"),
    ("data", "seven", 7, "curators", "indexed", "the collection", "indexing"),
    ("recovery", "eight", 8, "engineers", "replayed", "the transaction", "replay"),
]

TIMING_FRAMES = [
    ("verification", "three", 3, "agents", "verified", "the anchor", "verification"),
    ("incident", "four", 4, "responders", "contained", "the fault", "containment"),
    ("deployment", "five", 5, "workers", "deployed", "the patch", "deployment"),
    ("security", "six", 6, "auditors", "reviewed", "the grant", "review"),
    ("storage", "two", 2, "replicas", "rebuilt", "the index", "rebuild"),
    ("science", "seven", 7, "analysts", "classified", "the sample", "classification"),
    ("logistics", "eight", 8, "handlers", "scanned", "the container", "scan"),
    ("finance", "nine", 9, "clerks", "approved", "the invoice", "approval"),
    ("archive", "three", 3, "custodians", "copied", "the record", "copy"),
    ("network", "four", 4, "monitors", "pinged", "the service", "ping"),
]

# (domain, number word, integer, recipients, amount, object)
AMOUNT_FRAMES = [
    ("awards", "four", 4, "winners", 1000, "award"),
    ("research", "three", 3, "teams", 200, "grant"),
    ("operations", "five", 5, "departments", 300, "budget"),
    ("charity", "two", 2, "charities", 750, "donation"),
    ("science", "six", 6, "researchers", 400, "stipend"),
    ("education", "eight", 8, "schools", 250, "allocation"),
    ("community", "seven", 7, "groups", 100, "subsidy"),
    ("sport", "nine", 9, "clubs", 50, "rebate"),
    ("deployment", "ten", 10, "projects", 125, "credit"),
    ("relief", "twelve", 12, "households", 80, "payment"),
]

PARTICIPATION_FRAMES = [
    ("audit", "four", 4, "auditors", "inspected", "the archive", "inspection"),
    ("release", "three", 3, "maintainers", "signed", "the release", "signature"),
    ("incident", "five", 5, "responders", "restored", "the service", "restoration"),
    ("governance", "six", 6, "delegates", "submitted", "the ballot", "submission"),
    ("security", "two", 2, "custodians", "rotated", "the key", "rotation"),
]

CALIBRATION_FRAMES = [
    ("auditors", "review", "four"),
    ("agents", "verification", "three"),
    ("operators", "restart", "five"),
    ("stewards", "approval", "two"),
    ("monitors", "probe", "six"),
    ("editors", "publication", "four"),
    ("responders", "restoration", "three"),
    ("custodians", "sealing", "five"),
    ("inspectors", "test", "two"),
    ("reviewers", "signature", "six"),
    ("analysts", "classification", "four"),
    ("dispatchers", "release", "three"),
    ("teachers", "grading", "five"),
    ("engineers", "replay", "two"),
    ("curators", "indexing", "six"),
    ("controllers", "clearance", "four"),
]


def canonical_sha(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def options_with_answer(answer: str, distractors: list[str], position: int) -> list[str]:
    ordered = [answer] + [value for value in distractors if value != answer]
    assert len(ordered) == 4 and len(set(ordered)) == 4
    if position:
        ordered = ordered[-position:] + ordered[:-position]
    assert ordered[position] == answer
    return ordered


def action_row(frame: tuple, form: str, scenario: int, position: int) -> dict:
    domain, number_word, number, subjects, verb, obj, event = frame
    tagged = f"The {number_word} {subjects} {verb} {obj}, {form}."
    if form == "each-alone":
        careful = (
            f"Each of the {number_word} {subjects} independently {verb} {obj} in a separate act."
        )
        answer = number_word
    else:
        careful = (
            f"The {number_word} {subjects}, acting as one group, jointly {verb} {obj} in a single act."
        )
        answer = "one"
    return {
        "id": f"flagship-action-{scenario:02d}-{form.replace('-', '')}",
        "english": careful,
        "ainglish": tagged,
        "question": f"How many distinct {event} acts does the message assert?",
        "options": options_with_answer(answer, ["one", number_word, "none", "cannot determine"], position),
        "answer": answer,
        "form": form,
        "probe": "action_count",
        "scenario_id": f"action-{scenario:02d}",
        "strata": {"domain": domain, "named_members": number},
    }


def timing_row(frame: tuple, form: str, scenario: int, position: int) -> dict:
    domain, number_word, number, subjects, verb, obj, event = frame
    tagged = f"The {number_word} {subjects} {verb} {obj}, {form}."
    if form == "each-alone":
        careful = (
            f"Each of the {number_word} {subjects} independently {verb} {obj} in a separate act. "
            f"The timing of those acts is not specified."
        )
    else:
        careful = (
            f"The {number_word} {subjects}, acting as one group, jointly {verb} {obj} in a single act. "
            f"The timing of that act is not specified."
        )
    answer = "no, timing is not specified"
    return {
        "id": f"flagship-timing-{scenario:02d}-{form.replace('-', '')}",
        "english": careful,
        "ainglish": tagged,
        "question": "Does the message say whether the participants acted at the same time?",
        "options": options_with_answer(
            answer,
            ["yes, simultaneously", "yes, at different times", answer, "cannot determine whether any act happened"],
            position,
        ),
        "answer": answer,
        "form": form,
        "probe": "timing_overread",
        "scenario_id": f"timing-{scenario:02d}",
        "strata": {"domain": domain, "named_members": number},
    }


def amount_row(frame: tuple, form: str, scenario: int, position: int) -> dict:
    domain, number_word, number, recipients, amount, obj = frame
    total = number * amount
    tagged = f"The {number_word} {recipients} receive £{amount}, {form}."
    if form == "each-alone":
        careful = f"Each of the {number_word} {recipients} receives a separate £{amount} {obj}."
        answer = f"£{total}"
    else:
        careful = (
            f"The {number_word} {recipients}, as one group, collectively receive one £{amount} "
            f"{obj} to share."
        )
        answer = f"£{amount}"
    return {
        "id": f"flagship-amount-{scenario:02d}-{form.replace('-', '')}",
        "english": careful,
        "ainglish": tagged,
        "question": "What total amount does the message assert across the named recipients?",
        "options": options_with_answer(
            answer,
            [f"£{amount}", f"£{total}", "£0", "cannot determine"],
            position,
        ),
        "answer": answer,
        "form": form,
        "probe": "amount_transfer",
        "scenario_id": f"amount-{scenario:02d}",
        "strata": {"domain": domain, "named_members": number},
    }


def participation_row(frame: tuple, form: str, scenario: int, position: int) -> dict:
    domain, number_word, number, subjects, verb, obj, event = frame
    tagged = f"The {number_word} {subjects} {verb} {obj}, {form}."
    if form == "each-alone":
        careful = (
            f"Every one of the {number_word} {subjects} personally {verb} {obj} in a separate act."
        )
        answer = "every named member"
    else:
        careful = (
            f"The {number_word} {subjects}, as one group, jointly {verb} {obj} in one collective act, "
            f"without specifying how many members personally did the hands-on work."
        )
        answer = "the number of participating members is not specified"
    return {
        "id": f"flagship-participation-{scenario:02d}-{form.replace('-', '')}",
        "english": careful,
        "ainglish": tagged,
        "question": "How many of the named members does the message require to have personally performed the hands-on work?",
        "options": options_with_answer(
            answer,
            [
                "every named member",
                "some but not necessarily every named member",
                "no named member",
                "the number of participating members is not specified",
            ],
            position,
        ),
        "answer": answer,
        "form": form,
        "probe": "participation_overread",
        "scenario_id": f"participation-{scenario:02d}",
        "strata": {"domain": domain, "named_members": number},
    }


def real_items() -> list[dict]:
    rows: list[dict] = []
    builders = (
        (ACTION_FRAMES, action_row),
        (TIMING_FRAMES, timing_row),
        (AMOUNT_FRAMES, amount_row),
        (PARTICIPATION_FRAMES, participation_row),
    )
    for frames, builder in builders:
        for scenario, frame in enumerate(frames, start=1):
            for form in FORMS:
                rows.append(builder(frame, form, scenario, len(rows) % 4))
    return rows


def calibration_items() -> list[dict]:
    rows = []
    number_values = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6}
    for index, (subjects, event, number_word) in enumerate(CALIBRATION_FRAMES, start=1):
        answer = number_word
        rows.append({
            "id": f"flagship-calibration-{index:02d}",
            "english": f"The {subjects} completed the {event} work.",
            "ainglish": f"The {subjects} completed exactly {number_word} distinct {event} acts.",
            "question": f"How many distinct {event} acts does the message explicitly state?",
            "options": options_with_answer(answer, [answer, "one", "none", "cannot determine"], (index - 1) % 4),
            "answer": answer,
            "calibration": True,
            "probe": "construct_free_planted_effect",
            "strata": {"named_count": number_values[number_word]},
        })
    return rows


def bare_items(primary_rows: list[dict]) -> list[dict]:
    output = []
    for row in primary_rows:
        bare = row["ainglish"].replace(", each-alone.", ".").replace(", as-one.", ".")
        output.append({
            **row,
            "id": row["id"].replace("flagship-", "flagship-bare-"),
            "english": bare,
            "comparison": "marked_vs_bare_plural_descriptive_only",
        })
    return output


def validate(rows: list[dict]) -> dict:
    real = [row for row in rows if not row.get("calibration")]
    calibration = [row for row in rows if row.get("calibration")]
    assert len(real) == 100 and len(calibration) == 16
    assert len({row["id"] for row in rows}) == len(rows)
    assert all(row["english"] != row["ainglish"] for row in rows)
    assert all(row["answer"] in row["options"] and len(set(row["options"])) == 4 for row in rows)
    assert all("each-alone" not in row["english"] and "as-one" not in row["english"] for row in real)
    form_counts = Counter(row["form"] for row in real)
    probe_counts = Counter(row["probe"] for row in real)
    answer_positions = Counter(row["options"].index(row["answer"]) for row in real)
    assert form_counts == Counter({"each-alone": 50, "as-one": 50})
    assert probe_counts == Counter({
        "action_count": 50,
        "timing_overread": 20,
        "amount_transfer": 20,
        "participation_overread": 10,
    })
    assert answer_positions == Counter({0: 25, 1: 25, 2: 25, 3: 25})
    per_form_probe = Counter((row["form"], row["probe"]) for row in real)
    assert per_form_probe == Counter({
        ("each-alone", "action_count"): 25,
        ("as-one", "action_count"): 25,
        ("each-alone", "timing_overread"): 10,
        ("as-one", "timing_overread"): 10,
        ("each-alone", "amount_transfer"): 10,
        ("as-one", "amount_transfer"): 10,
        ("each-alone", "participation_overread"): 5,
        ("as-one", "participation_overread"): 5,
    })
    return {
        "real_items": len(real),
        "calibration_items": len(calibration),
        "forms": dict(form_counts),
        "probes": dict(probe_counts),
        "answer_positions": {str(key): value for key, value in sorted(answer_positions.items())},
        "per_form_probe": {f"{form}/{probe}": count for (form, probe), count in sorted(per_form_probe.items())},
    }


def main() -> None:
    primary = real_items() + calibration_items()
    bare = bare_items([row for row in primary if not row.get("calibration")])
    validation = validate(primary)

    primary_path = ROOT / "careful-items.json"
    bare_path = ROOT / "bare-items.json"
    primary_path.write_text(json.dumps({"items": primary}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    bare_path.write_text(json.dumps({"items": bare}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    receipt = {
        "kind": "ainglish.evidence.freeze-receipt.v1",
        "construct": "each-alone / as-one",
        "scientific_boundary": (
            "The claim carrier compares each registered marker with its complete careful-English mapping. "
            "Bare plural rows are separately frozen descriptive diagnostics and cannot establish non-inferiority."
        ),
        "reader_calls": 0,
        "files": [
            {
                "path": primary_path.name,
                "items_sha256": canonical_sha(primary),
                "file_sha256": file_sha(primary_path),
                "role": "full-careful-English claim carrier",
            },
            {
                "path": bare_path.name,
                "items_sha256": canonical_sha(bare),
                "file_sha256": file_sha(bare_path),
                "role": "bare-plural descriptive diagnostic only",
            },
        ],
        "validation": validation,
    }
    (ROOT / "freeze-receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(receipt, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
