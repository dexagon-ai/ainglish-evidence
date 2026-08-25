#!/usr/bin/env python3
"""Build eight fresh, opaque-choice flagship comprehension carriers without reader calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SEED = 2026082507
DOMAINS = [
    ("release", "approve the release", "release approval"),
    ("security", "inspect the access log", "log inspection"),
    ("operations", "restart the queue", "queue restart"),
    ("research", "validate the sample", "sample validation"),
    ("finance", "reconcile the invoice", "invoice reconciliation"),
    ("moderation", "review the appeal", "appeal review"),
    ("procurement", "check the quotation", "quotation check"),
    ("health", "verify the specimen", "specimen verification"),
    ("transport", "confirm the route", "route confirmation"),
    ("education", "assess the submission", "submission assessment"),
]
NAMES = [
    ("Ava", "Bo", "Cy"), ("Diya", "Eli", "Fara"), ("Gus", "Hana", "Ivo"),
    ("Jia", "Kofi", "Luz"), ("Mara", "Noor", "Oren"), ("Pia", "Quin", "Ravi"),
    ("Sana", "Tao", "Uma"), ("Vera", "Wes", "Xia"), ("Yara", "Zane", "Ari"),
    ("Bela", "Cato", "Dara"),
]


def canonical_rows(rows: list[dict]) -> bytes:
    return json.dumps(rows, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def rotated(options: list[str], index: int) -> list[str]:
    shift = index % len(options)
    return options[shift:] + options[:shift]


def calibrations(prefix: str) -> list[dict]:
    rows = []
    objects = ["amber token", "blue key", "cedar card", "dune badge", "elm seal", "fern tag", "gold pass", "hazel slip"]
    for index, obj in enumerate(objects):
        rows.append({
            "id": f"{prefix}-cal-{index + 1:02d}",
            "calibration": True,
            "english": f"A sealed note mentions the {obj} but gives no location.",
            "ainglish": f"A sealed note states that the {obj} is in locker seven.",
            "question": "Would opening locker seven follow the stated location?",
            "options": rotated(["affirmative", "negative", "indeterminate"], index),
            "answer": "affirmative",
            "set": "construct-free explicit-location positive control",
        })
    return rows


def clusivity(form: str) -> list[dict]:
    included = form == "we-including-you"
    rows = []
    probes = ["required", "permitted", "committed", "credited", "notified"]
    for index in range(100):
        domain, action, nominal = DOMAINS[index % len(DOMAINS)]
        cycle = index // 10 + 1
        probe = probes[(index // 10) % len(probes)]
        if probe == "required":
            predicate = f"must {action} before checkpoint {cycle} closes"
            question = "If the reader does nothing while every other group member acts, is the stated requirement fully met?"
            answer = "negative" if included else "affirmative"
        elif probe == "permitted":
            predicate = f"may {action} during checkpoint {cycle}"
            question = "Does the message grant the reader the stated permission?"
            answer = "affirmative" if included else "negative"
        elif probe == "committed":
            predicate = f"will {action} before checkpoint {cycle} closes"
            question = "Does the stated commitment include action by the reader?"
            answer = "affirmative" if included else "negative"
        elif probe == "credited":
            predicate = f"have completed the {nominal} for checkpoint {cycle}"
            question = "Does the sentence count the reader among those credited with completion?"
            answer = "affirmative" if included else "negative"
        else:
            predicate = f"will receive the checkpoint {cycle} {nominal} notice"
            question = "Does the announced recipient set contain the reader?"
            answer = "affirmative" if included else "negative"
        mapping = (
            f"The members of the speaker's group, including you as the reader, {predicate}."
            if included else f"The members of the speaker's group, excluding you as the reader, {predicate}."
        )
        rows.append({
            "id": f"{form}-{index + 1:03d}",
            "english": mapping,
            "ainglish": f"{form} {predicate}.",
            "question": question,
            "options": rotated(["affirmative", "negative", "indeterminate"], index),
            "answer": answer,
            "marker": form,
            "scenario_id": f"clusivity-{index + 1:03d}",
            "strata": {"domain": domain, "probe": probe, "polarity": "included" if included else "excluded"},
        })
    return rows


def second_person(form: str) -> list[dict]:
    plural = form == "you-all"
    rows = []
    probes = ["subject-duty", "object-warning", "permission", "forwarding-boundary", "action-count-independence"]
    for index in range(100):
        domain, action, nominal = DOMAINS[index % len(DOMAINS)]
        action = f"{action} during review round {index // 10 + 1}"
        one, two, three = NAMES[index % len(NAMES)]
        probe = probes[(index // 10) % len(probes)]
        if plural:
            envelope = f"Group note addressed to {one}, {two}, and {three}."
            mapping_subject = f"Every member of the addressed group—{one}, {two}, and {three}—"
            mapping_object = f"every member of the addressed group—{one}, {two}, and {three}"
            marked_subject = form
        else:
            envelope = f"Private note addressed only to {one}."
            mapping_subject = f"The exactly one addressee, {one}, "
            mapping_object = f"the exactly one addressee, {one}"
            marked_subject = form
        if probe == "subject-duty":
            english = f"{envelope} {mapping_subject}must {action}."
            ainglish = f"{envelope} {marked_subject} must {action}."
            question = f"If {one} does nothing, can every addressed duty in the note still be fulfilled?"
            answer = "negative"
        elif probe == "object-warning":
            english = f"{envelope} The review-round {index // 10 + 1} warning about the {nominal} applies to {mapping_object}."
            ainglish = f"{envelope} The review-round {index // 10 + 1} warning about the {nominal} applies to {marked_subject}."
            question = f"Does the note apply its warning to {three}?"
            answer = "affirmative" if plural else "negative"
        elif probe == "permission":
            english = f"{envelope} {mapping_subject}may {action}."
            ainglish = f"{envelope} {marked_subject} may {action}."
            question = f"Does the note give {two} the stated permission?"
            answer = "affirmative" if plural else "negative"
        elif probe == "forwarding-boundary":
            english = f"{envelope} {mapping_subject}must {action}; later readers are outside that addressed set."
            ainglish = f"{envelope} {marked_subject} must {action}."
            question = "Would a later observer who only receives a forwarded copy enter the addressed set?"
            answer = "negative"
        else:
            english = f"{envelope} {mapping_subject}will {action}; this says who is addressed, not how many separate acts occur."
            ainglish = f"{envelope} {marked_subject} will {action}."
            question = "Does the sentence by itself require a separate performance from each addressed person?"
            answer = "indeterminate"
        rows.append({
            "id": f"{form}-{index + 1:03d}",
            "english": english.replace("  ", " "),
            "ainglish": ainglish,
            "question": question,
            "options": rotated(["affirmative", "negative", "indeterminate"], index),
            "answer": answer,
            "marker": form,
            "scenario_id": f"second-person-{index + 1:03d}",
            "strata": {"domain": domain, "probe": probe, "cardinality": "plural" if plural else "singular"},
        })
    return rows


def uncertainty(form: str) -> list[dict]:
    factual = form == "fact-not-known"
    rows = []
    criteria = ["checksum", "ledger record", "sensor trace", "published rule", "inventory count"]
    authorities = ["release board", "treasury lead", "lab director", "appeal panel", "route controller"]
    for index in range(100):
        domain, _, nominal = DOMAINS[index % len(DOMAINS)]
        criterion = criteria[(index // 10) % len(criteria)]
        authority = authorities[(index // 20) % len(authorities)]
        issue = f"the final status of the {nominal} in review cycle {index // 10 + 1}"
        if factual:
            english = (
                f"An existing {criterion} already determines {issue}. The authenticated speaker lacks enough evidence "
                "to state that answer, and retrieving or deriving the evidence can close the gap."
            )
            ainglish = f"fact-not-known — {issue}."
        else:
            english = (
                f"The {authority} has power to select {issue}, but it has made no operative selection. Evidence may "
                "inform the choice, but only an authorized selection can close the gap."
            )
            ainglish = f"choice-not-made — {issue}."
        probe = index % 4
        if probe == 0:
            question = "If every relevant record is retrieved but nobody makes a new selection, can the gap close?"
            answer = "affirmative" if factual else "negative"
        elif probe == 1:
            question = "Must someone make a new authorized selection for the operative answer to exist?"
            answer = "negative" if factual else "affirmative"
        elif probe == 2:
            question = "Does the message claim that no person anywhere already knows the answer?"
            answer = "negative"
        else:
            question = "Does the marker by itself ask the reader to resolve the issue?"
            answer = "negative"
        rows.append({
            "id": f"{form}-{index + 1:03d}",
            "english": english,
            "ainglish": ainglish,
            "question": question,
            "options": rotated(["affirmative", "negative", "indeterminate"], index),
            "answer": answer,
            "marker": form,
            "scenario_id": f"uncertainty-{index + 1:03d}",
            "strata": {"domain": domain, "probe": f"resolution-{probe + 1}", "mode": "fact" if factual else "choice"},
        })
    return rows


def delegation(form: str) -> list[dict]:
    no_delegate = form == "no-delegation"
    rows = []
    probes = ["direct-handoff", "second-hop", "accountability", "deterministic-tool", "sibling-delegates"]
    for index in range(100):
        domain, action, _ = DOMAINS[index % len(DOMAINS)]
        action = f"{action} during work cycle {index // 10 + 1}"
        owner, delegate, downstream = NAMES[index % len(NAMES)]
        probe = probes[(index // 10) % len(probes)]
        ainglish = f"{owner} must {action}, {form}."
        if no_delegate:
            english = (
                f"{owner} must {action}. {owner} must not assign any completion-bearing part to a different "
                f"principal; ordinary deterministic tools remain allowed, and {owner} remains accountable."
            )
        else:
            english = (
                f"{owner} must {action}. {owner} may assign part or all of it to one or more immediate delegates, "
                f"including {delegate}; no immediate delegate may pass it to {downstream} or another principal, and "
                f"{owner} remains accountable. Ordinary deterministic tools remain allowed."
            )
        if probe == "direct-handoff":
            question = f"May {owner} assign a completion-bearing part directly to {delegate}?"
            answer = "negative" if no_delegate else "affirmative"
        elif probe == "second-hop":
            question = f"If {delegate} receives a permitted part, may {delegate} pass it onward to {downstream}?"
            answer = "negative"
        elif probe == "accountability":
            question = f"After any permitted handoff, does {owner} still owe the issuer the completed result?"
            answer = "affirmative"
        elif probe == "deterministic-tool":
            question = f"May {owner} invoke a deterministic tool under {owner}'s control?"
            answer = "affirmative"
        else:
            question = f"May {owner} use two immediate delegates without either delegate handing work onward?"
            answer = "negative" if no_delegate else "affirmative"
        rows.append({
            "id": f"{form}-{index + 1:03d}",
            "english": english,
            "ainglish": ainglish,
            "question": question,
            "options": rotated(["affirmative", "negative", "indeterminate"], index),
            "answer": answer,
            "marker": form,
            "scenario_id": f"delegation-{index + 1:03d}",
            "strata": {"domain": domain, "probe": probe, "policy": "none" if no_delegate else "one-hop"},
        })
    return rows


BUILDERS = {
    "we-including-you": clusivity,
    "we-excluding-you": clusivity,
    "you-one": second_person,
    "you-all": second_person,
    "fact-not-known": uncertainty,
    "choice-not-made": uncertainty,
    "no-delegation": delegation,
    "one-hop-delegation-allowed": delegation,
}


def main() -> None:
    receipt = {"kind": "ainglish.flagship-comprehension-freeze.v1", "seed": SEED, "reader_calls": 0, "campaigns": {}}
    for name, builder in BUILDERS.items():
        scientific = builder(name)
        rows = scientific + calibrations(name)
        assert len(scientific) == 100 and len(rows) == 108
        assert len({row["id"] for row in rows}) == 108
        assert len({(row["english"], row["ainglish"], row["question"]) for row in scientific}) == 100
        assert all(row["english"] != row["ainglish"] for row in rows)
        digest = hashlib.sha256(canonical_rows(rows)).hexdigest()
        payload = {
            "kind": "ainglish.flagship-comprehension-items.v1",
            "campaign": name,
            "seed": SEED,
            "sha256": digest,
            "design": "100 fresh scientific pairs plus eight construct-free, both-arm calibration rows; opaque A/B/C response codes are bound by the SDK harness.",
            "items": rows,
        }
        path = ROOT / f"items-{name}.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        receipt["campaigns"][name] = {"path": path.name, "items_sha256": digest, "scientific": 100, "calibration": 8}
    encoded = json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    receipt["content_sha256"] = hashlib.sha256(encoded).hexdigest()
    (ROOT / "freeze-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
