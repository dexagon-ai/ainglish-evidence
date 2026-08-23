#!/usr/bin/env python3
"""Build and validate the we-including-you / we-excluding-you diagnostic."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FORMS = ("we-including-you", "we-excluding-you")
PROBES = (
    "obligation_routing",
    "permission_routing",
    "commitment_membership",
    "completed_action_membership",
    "notification_membership",
)

# domain, group label, base verb, past participle, object, notification
FRAMES = [
    ("governance", "review group", "approve", "approved", "the amendment", "ballot receipt"),
    ("operations", "operations group", "restart", "restarted", "the queue", "restart notice"),
    ("security", "audit group", "inspect", "inspected", "the access log", "security alert"),
    ("deployment", "release group", "publish", "published", "the release", "deployment notice"),
    ("science", "research group", "analyse", "analysed", "the sample", "analysis report"),
    ("incident", "response group", "restore", "restored", "the service", "recovery alert"),
    ("archive", "curation group", "index", "indexed", "the collection", "index receipt"),
    ("transport", "control group", "clear", "cleared", "the route", "clearance notice"),
    ("compliance", "stewardship group", "sign", "signed", "the declaration", "signature receipt"),
    ("network", "monitoring group", "probe", "probed", "the endpoint", "probe report"),
    ("education", "teaching group", "grade", "graded", "the examination", "grading notice"),
    ("media", "editorial group", "issue", "issued", "the correction", "publication notice"),
    ("recovery", "engineering group", "replay", "replayed", "the transaction", "replay receipt"),
    ("records", "custodian group", "seal", "sealed", "the archive", "sealing receipt"),
    ("storage", "technical group", "recover", "recovered", "the database", "recovery report"),
    ("finance", "accounting group", "reconcile", "reconciled", "the ledger", "reconciliation notice"),
    ("health", "clinical group", "interpret", "interpreted", "the scan", "clinical report"),
    ("logistics", "dispatch group", "release", "released", "the shipment", "dispatch notice"),
    ("quality", "testing group", "certify", "certified", "the build", "certification receipt"),
    ("voting", "delegate group", "submit", "submitted", "the ballot", "submission receipt"),
]

READINGS = {
    "obligation_routing": (
        "the reader is included among those required to act",
        "the reader is excluded from those required to act and is only being informed",
    ),
    "permission_routing": (
        "the reader is included among those granted permission",
        "the reader is outside the permitted group; this message does not grant the reader permission",
    ),
    "commitment_membership": (
        "the reader is included in the group making the commitment",
        "the reader is outside the group making the commitment and is only being informed",
    ),
    "completed_action_membership": (
        "the reader is included in the group claimed to have completed the action",
        "the reader is excluded from the group claimed to have completed the action",
    ),
    "notification_membership": (
        "the reader is included among the people who will receive the notification",
        "the reader is excluded from the notification-recipient group",
    ),
}

CALIBRATION_FRAMES = [
    ("review team", "inspect the record"),
    ("release team", "publish the notice"),
    ("audit team", "check the receipt"),
    ("response team", "restore the service"),
    ("research team", "analyse the sample"),
    ("storage team", "recover the archive"),
    ("governance team", "submit the ballot"),
    ("security team", "rotate the key"),
    ("network team", "probe the endpoint"),
    ("quality team", "certify the build"),
    ("records team", "seal the collection"),
    ("finance team", "reconcile the ledger"),
    ("clinical team", "review the scan"),
    ("dispatch team", "release the shipment"),
    ("education team", "grade the examination"),
    ("editorial team", "issue the correction"),
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


def predicate_for(probe: str, frame: tuple[str, ...]) -> str:
    _, _, base, past, obj, notification = frame
    if probe == "obligation_routing":
        return f"must {base} {obj} before the next checkpoint"
    if probe == "permission_routing":
        return f"may {base} {obj} after the notice arrives"
    if probe == "commitment_membership":
        return f"will {base} {obj} during the next cycle"
    if probe == "completed_action_membership":
        return f"have {past} {obj} during this cycle"
    if probe == "notification_membership":
        return f"will receive the {notification} when it is issued"
    raise AssertionError(probe)


def careful_sentence(form: str, predicate: str) -> str:
    if form == "we-including-you":
        return f"We — and that includes you, the reader — {predicate}."
    return (
        f"We, not including you, {predicate}; you are informed but outside this "
        "‘we’ group for this statement."
    )


def primary_row(probe: str, frame: tuple[str, ...], scenario: int, form: str, position: int) -> dict:
    domain, group, _, _, _, _ = frame
    predicate = predicate_for(probe, frame)
    included, excluded = READINGS[probe]
    answer = included if form == "we-including-you" else excluded
    return {
        "id": f"clusivity-{probe}-{scenario:02d}-{form.replace('-', '')}",
        "english": careful_sentence(form, predicate),
        "ainglish": f"{form} {predicate}.",
        "question": "What does the message say about the reader’s place in the group and the stated consequence?",
        "options": options_with_answer(
            answer,
            [
                included,
                excluded,
                "the reader alone is the entire ‘we’ group",
                "the wording only adds a warmer team tone; whether the reader is included remains unresolved",
            ],
            position,
        ),
        "answer": answer,
        "form": form,
        "probe": probe,
        "scenario_id": f"{probe}-{scenario:02d}",
        "strata": {"domain": domain, "group": group},
    }


def primary_items(form: str) -> list[dict]:
    rows = []
    for probe_index, probe in enumerate(PROBES):
        for scenario, frame in enumerate(FRAMES, start=1):
            position = (probe_index * len(FRAMES) + scenario - 1 + (0 if form == FORMS[0] else 2)) % 4
            rows.append(primary_row(probe, frame, scenario, form, position))
    return rows


def calibration_items() -> list[dict]:
    rows = []
    for index, (group, action) in enumerate(CALIBRATION_FRAMES, start=1):
        included = index % 2 == 1
        answer = "the reader is included" if included else "the reader is excluded"
        explicit = (
            f"The {group} explicitly includes the reader and will {action}."
            if included
            else f"The {group} explicitly excludes the reader and will {action}."
        )
        rows.append({
            "id": f"clusivity-calibration-{index:02d}",
            "english": f"The {group} will {action}.",
            "ainglish": explicit,
            "question": f"Is the reader a member of the {group}?",
            "options": options_with_answer(
                answer,
                [
                    "the reader is included",
                    "the reader is excluded",
                    "the reader is the only member",
                    "the message does not say",
                ],
                (index - 1) % 4,
            ),
            "answer": answer,
            "calibration": True,
            "probe": "construct_free_planted_effect",
            "strata": {"explicit_status": "included" if included else "excluded"},
        })
    return rows


def bare_items(real: list[dict]) -> list[dict]:
    rows = []
    for row in real:
        bare = row["ainglish"]
        for form in FORMS:
            bare = bare.replace(form, "we", 1)
        rows.append({
            "id": row["id"].replace("clusivity-", "clusivity-bare-", 1),
            "bare_english": bare,
            "question": row["question"],
            "options": row["options"],
            "form_intent": row["form"],
            "probe": row["probe"],
            "scenario_id": row["scenario_id"],
            "comparison": "bare-we descriptive ambiguity arm only",
        })
    return rows


def overread_items() -> list[dict]:
    questions = [
        ("group_size", "Does the marker state the total number of people in the ‘we’ group?"),
        ("personal_action", "Does the marker require every group member to perform the action personally?"),
        ("simultaneity", "Does the marker say that all group members act at the same time?"),
        ("relationship_warmth", "Does the marker assert that the speaker feels warm or close toward the reader?"),
        ("bare_reverse_inference", "Does this marker make every later unmarked ‘we’ an exclusive ‘we’?"),
    ]
    rows = []
    for q_index, (probe, question) in enumerate(questions):
        for f_index, form in enumerate(FORMS):
            for scenario, frame in enumerate(FRAMES[:4], start=1):
                predicate = predicate_for(PROBES[q_index], frame)
                rows.append({
                    "id": f"clusivity-overread-{probe}-{scenario:02d}-{form.replace('-', '')}",
                    "english": careful_sentence(form, predicate),
                    "ainglish": f"{form} {predicate}.",
                    "question": question,
                    "options": options_with_answer(
                        "no",
                        ["yes", "no", "cannot tell whether the reader is included", "the form is invalid"],
                        (q_index + f_index + scenario - 1) % 4,
                    ),
                    "answer": "no",
                    "form": form,
                    "probe": probe,
                    "scenario_id": f"overread-{probe}-{scenario:02d}",
                    "comparison": "descriptive over-read diagnostic outside the primary scalar",
                })
    return rows


def validate_form(rows: list[dict], form: str) -> dict:
    real = [row for row in rows if not row.get("calibration")]
    calibration = [row for row in rows if row.get("calibration")]
    assert len(real) == 100 and len(calibration) == 16
    assert len({row["id"] for row in rows}) == len(rows)
    assert all(row["form"] == form for row in real)
    assert all(row["english"] != row["ainglish"] for row in rows)
    assert all(row["answer"] in row["options"] and len(set(row["options"])) == 4 for row in rows)
    assert all(not any(marker in row["english"] for marker in FORMS) for row in real)
    assert all(row["ainglish"].startswith(form + " ") for row in real)
    probes = Counter(row["probe"] for row in real)
    positions = Counter(row["options"].index(row["answer"]) for row in real)
    assert probes == Counter({probe: 20 for probe in PROBES})
    assert positions == Counter({0: 25, 1: 25, 2: 25, 3: 25})
    return {
        "real_items": len(real),
        "calibration_items": len(calibration),
        "probes": dict(probes),
        "answer_positions": {str(k): v for k, v in sorted(positions.items())},
    }


def main() -> None:
    calibration = calibration_items()
    documents = {}
    validations = {}
    for form in FORMS:
        rows = primary_items(form) + calibration
        path = ROOT / f"{form}-items.json"
        path.write_text(json.dumps({"items": rows}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        documents[form] = (path, rows)
        validations[form] = validate_form(rows, form)

    real = primary_items(FORMS[0]) + primary_items(FORMS[1])
    bare = bare_items(real)
    overread = overread_items()
    bare_path = ROOT / "bare-we-items.json"
    overread_path = ROOT / "overread-items.json"
    bare_path.write_text(json.dumps({"items": bare}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    overread_path.write_text(json.dumps({"items": overread}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    files = []
    for form, (path, rows) in documents.items():
        files.append({
            "path": path.name,
            "items_sha256": canonical_sha(rows),
            "file_sha256": file_sha(path),
            "role": f"{form} full-careful-English standalone claim carrier",
        })
    for path, rows, role in (
        (bare_path, bare, "bare-we descriptive ambiguity rows; not a claim carrier"),
        (overread_path, overread, "descriptive over-read controls; not a claim carrier"),
    ):
        files.append({"path": path.name, "items_sha256": canonical_sha(rows), "file_sha256": file_sha(path), "role": role})

    receipt = {
        "kind": "ainglish.evidence.freeze-receipt.v1",
        "construct": "we-including-you / we-excluding-you",
        "scientific_boundary": (
            "Each marker is separately compared with its complete registered careful-English mapping. "
            "Bare we and over-read rows are descriptive only and cannot establish non-inferiority."
        ),
        "discussion_influence": (
            "The public semantic-bleaching concern shaped the warm-tone distractor, but no public "
            "answer-bearing item block was copied or inspected."
        ),
        "human_face_validity": {
            "n": 1,
            "description": "native-English-speaking operator reports the distinction is easily understandable",
            "role": "informal face validity only; excluded from every measured estimand",
        },
        "reader_calls": 0,
        "files": files,
        "validation": validations,
    }
    (ROOT / "freeze-receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(receipt, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
