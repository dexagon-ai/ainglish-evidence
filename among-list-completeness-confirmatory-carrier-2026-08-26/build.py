#!/usr/bin/env python3
"""Build four fresh form/comparator carriers without reader or network calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SLUG = "among-others-and-no-others-is-the-list-the-whole-list-2"
SEED = 2026082647
FORMS = ("among-others", "and-no-others")
COMPARATORS = ("careful", "bare")
DOMAINS = (
    ("retry policy", "response codes", "triggers retries for", "response code"),
    ("export profile", "file formats", "accepts", "file format"),
    ("network allowlist", "principals", "admits", "principal"),
    ("deployment plan", "targets", "deploys to", "target"),
    ("billing schedule", "fee codes", "charges", "fee code"),
    ("dependency manifest", "modules", "loads", "module"),
    ("event schema", "tags", "recognises", "tag"),
    ("audit mandate", "record classes", "covers", "record class"),
)


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def rotate(values: list[str], index: int) -> list[str]:
    shift = index % len(values)
    return values[shift:] + values[:shift]


def closure_answer(form: str) -> str:
    return "not claimed either way" if form == "among-others" else "claimed excluded"


def one_list(domain: tuple[str, str, str, str], serial: int) -> tuple[str, str, str, str]:
    label, kind, verb, singular = domain
    a, b, extra = f"amber-{serial}", f"cobalt-{serial}", f"indigo-{serial}"
    bare = f"Notice {serial}. The {label} {verb} {a} and {b}."
    return bare, a, b, extra


def marked_one(domain: tuple[str, str, str, str], serial: int, form: str) -> str:
    label, kind, verb, singular = domain
    a, b = f"amber-{serial}", f"cobalt-{serial}"
    return f"Notice {serial}. The {label} {verb} {a}, {b}, {form}."


def careful_one(domain: tuple[str, str, str, str], serial: int, form: str) -> str:
    label, kind, verb, singular = domain
    a, b = f"amber-{serial}", f"cobalt-{serial}"
    if form == "among-others":
        return (
            f"Notice {serial}. The {label} {verb} {a} and {b}; the list is not claimed complete, "
            f"and no claim is made either way about unlisted same-kind {kind}."
        )
    return (
        f"Notice {serial}. The {label} {verb} {a} and {b} and claims this is the complete "
        f"same-kind list in scope; every unlisted {singular} is excluded."
    )


def scientific_item(form: str, comparator: str, index: int) -> dict[str, object]:
    domain = DOMAINS[index % len(DOMAINS)]
    label, kind, verb, singular = domain
    serial = 1300 + index
    bare, listed_a, listed_b, extra = one_list(domain, serial)
    marked = marked_one(domain, serial, form)
    careful = careful_one(domain, serial, form)

    if index < 48:
        probe = "unlisted_consequence"
        question = f"What does the notice claim about whether {extra}, an unlisted same-kind {singular}, is accepted?"
        answer = closure_answer(form)
        options = ["claimed included", "claimed excluded", "not claimed either way"]
        target = "marked-list"
    elif index < 72:
        probe = "listed_health_overread"
        question = f"What does the notice claim about whether listed {listed_a} is currently working correctly?"
        answer = "not claimed either way"
        options = ["claimed working", "claimed broken", "not claimed either way"]
        target = "listed-member"
    elif index < 84:
        probe = "time_overread"
        question = "What does the notice claim about whether this membership remains unchanged forever?"
        answer = "not claimed either way"
        options = ["claimed permanent", "claimed temporary", "not claimed either way"]
        target = "time"
    elif index < 96:
        probe = "kind_overread"
        other = f"violet-{serial}"
        question = f"What does the notice claim about whether {other}, explicitly a different kind, is excluded?"
        answer = "not claimed either way"
        options = ["claimed included", "claimed excluded", "not claimed either way"]
        target = "different-kind"
    else:
        probe = "two_enumeration_attachment"
        x, y, other = f"north-{serial}", f"south-{serial}", f"west-{serial}"
        marker_first = (index - 96) % 2 == 0
        ask_marked = ((index - 96) // 2) % 2 == 0
        first_bare = f"the {label} {verb} {listed_a} and {listed_b}"
        second_bare = f"the fallback roster names {x} and {y}"
        bare = f"Notice {serial}. {first_bare}; {second_bare}."
        first_marked = f"the {label} {verb} {listed_a}, {listed_b}, {form}"
        second_marked = f"the fallback roster names {x}, {y}, {form}"
        if marker_first:
            marked = f"Notice {serial}. {first_marked}; {second_bare}."
            if form == "among-others":
                careful = f"Notice {serial}. {first_bare}, with no completeness claim about that first list; {second_bare}."
            else:
                careful = f"Notice {serial}. {first_bare}, and that first list is complete in scope; {second_bare}."
            marked_subject, unmarked_subject = extra, other
            marked_kind, unmarked_kind = singular, "fallback member"
        else:
            marked = f"Notice {serial}. {first_bare}; {second_marked}."
            if form == "among-others":
                careful = f"Notice {serial}. {first_bare}; {second_bare}, with no completeness claim about that second list."
            else:
                careful = f"Notice {serial}. {first_bare}; {second_bare}, and that second list is complete in scope."
            marked_subject, unmarked_subject = other, extra
            marked_kind, unmarked_kind = "fallback member", singular
        if ask_marked:
            question = f"What does the notice claim about whether unlisted {marked_subject}, a same-kind {marked_kind}, is accepted?"
            answer = closure_answer(form)
            target = "marked-list"
        else:
            question = f"What does the notice claim about whether unlisted {unmarked_subject}, a same-kind {unmarked_kind}, is accepted?"
            answer = "not claimed either way"
            target = "unmarked-list"
        options = ["claimed included", "claimed excluded", "not claimed either way"]

    options = rotate(options, index)
    assert answer in options
    return {
        "id": f"among-confirm-{form}-{comparator}-{index + 1:03d}",
        "english": careful if comparator == "careful" else bare,
        "ainglish": marked,
        "question": question,
        "options": options,
        "answer": answer,
        "form": form,
        "comparator": comparator,
        "frame_id": f"among-confirm-frame-{serial}",
        "strata": {"domain": label, "probe": probe, "attachment_target": target},
    }


def calibration(form: str, comparator: str, index: int) -> dict[str, object]:
    token = f"list-control-{form}-{comparator}-{index + 1}"
    options = rotate(["bay 4", "bay 9", "not stated"], index)
    return {
        "id": f"among-confirm-{form}-{comparator}-cal-{index + 1:02d}",
        "calibration": True,
        "english": f"The note mentions {token} but does not state a bay.",
        "ainglish": f"The note states that {token} is in bay 9.",
        "question": f"Which bay does the note state for {token}?",
        "options": options,
        "answer": "bay 9",
        "set": "construct-free explicit-location control",
    }


def build_campaign(form: str, comparator: str) -> tuple[dict[str, object], dict[str, object]]:
    scientific = [scientific_item(form, comparator, index) for index in range(120)]
    controls = [calibration(form, comparator, index) for index in range(8)]
    items = scientific + controls
    digest = hashlib.sha256(canonical(items)).hexdigest()
    name = f"items-{form}-vs-{comparator}.json"
    payload = {
        "kind": "ainglish.among-list-confirmatory-carrier.v1",
        "proposal_revision": SLUG,
        "form": form,
        "comparator": comparator,
        "seed": SEED,
        "items_sha256": digest,
        "reader_calls": 0,
        "items": items,
    }
    receipt = {
        "file": name,
        "items_sha256": digest,
        "scientific": 120,
        "calibration": 8,
        "probe_counts": {
            probe: sum(row["strata"]["probe"] == probe for row in scientific)
            for probe in sorted({row["strata"]["probe"] for row in scientific})
        },
    }
    return payload, receipt


def main() -> None:
    campaigns: dict[str, object] = {}
    payloads: dict[tuple[str, str], dict[str, object]] = {}
    for form in FORMS:
        for comparator in COMPARATORS:
            payload, receipt = build_campaign(form, comparator)
            payloads[(form, comparator)] = payload
            (ROOT / receipt["file"]).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
            campaigns[f"{form}-vs-{comparator}"] = receipt

    for index in range(120):
        left = payloads[("among-others", "bare")]["items"][index]
        right = payloads[("and-no-others", "bare")]["items"][index]
        assert left["frame_id"] == right["frame_id"]
        assert left["english"] == right["english"]
        assert left["question"] == right["question"]

    index = {
        "kind": "ainglish.among-list-confirmatory-freeze.v1",
        "proposal_revision": SLUG,
        "seed": SEED,
        "model_calls": 0,
        "governance_writes": 0,
        "campaigns": campaigns,
        "execution_gate": "sealed: token prerequisite unsettled and qualified reader roster is 1/2",
        "seam_rule": "whole/part is a separately labelled diagnostic, never a meaning-matched among-others control",
    }
    index["content_sha256"] = hashlib.sha256(canonical(index)).hexdigest()
    (ROOT / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(index, indent=2))


if __name__ == "__main__":
    main()
