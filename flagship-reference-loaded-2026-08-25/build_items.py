#!/usr/bin/env python3
"""Freeze fresh one-shot reference-loaded flagship carriers without reader calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SEED = 2026082513
N = 64
DOMAINS = [
    ("incident", "close the incident", "incident closure"),
    ("archive", "seal the archive", "archive seal"),
    ("workshop", "inspect the prototype", "prototype inspection"),
    ("fleet", "authorize the vehicle", "vehicle authorization"),
    ("grant", "score the application", "application score"),
    ("inventory", "audit the stock", "stock audit"),
    ("newsroom", "verify the dispatch", "dispatch verification"),
    ("habitat", "sample the enclosure", "enclosure sample"),
]
NAMES = [
    ("Amina", "Bram", "Chen"), ("Dev", "Esme", "Fionn"),
    ("Gia", "Hugo", "Ines"), ("Joon", "Kira", "Liam"),
    ("Mina", "Niko", "Ola"), ("Priya", "Rui", "Sol"),
    ("Tess", "Umar", "Vale"), ("Wynn", "Xavi", "Yuki"),
]
DEFINITIONS = {
    "we-including-you": "the speaker's group including you, the reader",
    "we-excluding-you": "the speaker's group excluding you, the reader",
    "you-one": "the exactly one addressee",
    "you-all": "every member of the addressed group",
    "fact-not-known": "an answer exists, but the authenticated speaker lacks enough evidence to state it",
    "choice-not-made": "an authorized actor has not yet made the operative selection",
    "no-delegation": "no completion-bearing work may be assigned to another principal; deterministic tools remain allowed",
    "one-hop-delegation-allowed": "completion-bearing work may pass to immediate delegates, but those delegates may not pass it onward",
}
PAIRS = {
    "we-including-you": "we-excluding-you",
    "we-excluding-you": "we-including-you",
    "you-one": "you-all",
    "you-all": "you-one",
    "fact-not-known": "choice-not-made",
    "choice-not-made": "fact-not-known",
    "no-delegation": "one-hop-delegation-allowed",
    "one-hop-delegation-allowed": "no-delegation",
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def rotate(options: list[str], index: int) -> list[str]:
    shift = index % len(options)
    return options[shift:] + options[:shift]


def reference_card(form: str) -> str:
    other = PAIRS[form]
    return (
        "Reference card for this task: "
        f"'{form}' means {DEFINITIONS[form]}; "
        f"'{other}' means {DEFINITIONS[other]}. "
        "Apply these definitions literally to the message that follows."
    )


def row(form: str, index: int, english_message: str, marked_message: str,
        question: str, answer: str, **strata: str) -> dict:
    card = reference_card(form)
    return {
        "id": f"rl-{form}-{index + 1:03d}",
        "english": f"{card}\n\nMessage: {english_message}",
        "ainglish": f"{card}\n\nMessage: {marked_message}",
        "question": question,
        "options": rotate(["affirmative", "negative", "indeterminate"], index),
        "answer": answer,
        "marker": form,
        "scenario_id": f"reference-loaded-{form}-{index + 1:03d}",
        "strata": strata,
    }


def clusivity(form: str) -> list[dict]:
    included = form == "we-including-you"
    rows = []
    for index in range(N):
        domain, action, noun = DOMAINS[index % len(DOMAINS)]
        cycle = index // len(DOMAINS) + 11
        probe = ("duty", "permission", "credit", "recipient")[index // 16]
        if probe == "duty":
            predicate = f"must {action} before cycle {cycle} ends"
            question = "If the reader does nothing while all other group members act, is every stated duty fulfilled?"
            answer = "negative" if included else "affirmative"
        elif probe == "permission":
            predicate = f"may {action} during cycle {cycle}"
            question = "Does the message grant the reader the stated permission?"
            answer = "affirmative" if included else "negative"
        elif probe == "credit":
            predicate = f"completed the {noun} for cycle {cycle}"
            question = "Does the message count the reader among those credited with completion?"
            answer = "affirmative" if included else "negative"
        else:
            predicate = f"will receive the cycle {cycle} {noun} notice"
            question = "Is the reader inside the announced recipient set?"
            answer = "affirmative" if included else "negative"
        mapping = (
            f"The speaker's group, including the reader, {predicate}."
            if included else f"The speaker's group, excluding the reader, {predicate}."
        )
        rows.append(row(form, index, mapping, f"{form} {predicate}.", question, answer,
                        domain=domain, probe=probe, membership="included" if included else "excluded"))
    return rows


def second_person(form: str) -> list[dict]:
    plural = form == "you-all"
    rows = []
    for index in range(N):
        domain, action, noun = DOMAINS[index % len(DOMAINS)]
        one, two, three = NAMES[index % len(NAMES)]
        round_number = index // len(DOMAINS) + 21
        envelope = (f"Group message addressed to {one}, {two}, and {three}."
                    if plural else f"Private message addressed only to {one}.")
        subject = (f"Every addressed person—{one}, {two}, and {three}—"
                   if plural else f"The sole addressee, {one}, ")
        marked = form
        probe = ("duty", "warning", "permission", "forwarding")[index // 16]
        if probe == "duty":
            english = f"{envelope} {subject}must {action} in round {round_number}."
            ainglish = f"{envelope} {marked} must {action} in round {round_number}."
            question = f"If {one} does nothing, can all addressed duties still be fulfilled?"
            answer = "negative"
        elif probe == "warning":
            target = (f"every addressed person—{one}, {two}, and {three}"
                      if plural else f"the sole addressee, {one}")
            english = f"{envelope} The round {round_number} {noun} warning applies to {target}."
            ainglish = f"{envelope} The round {round_number} {noun} warning applies to {marked}."
            question = f"Does the warning apply to {three}?"
            answer = "affirmative" if plural else "negative"
        elif probe == "permission":
            english = f"{envelope} {subject}may {action} in round {round_number}."
            ainglish = f"{envelope} {marked} may {action} in round {round_number}."
            question = f"Does the message grant {two} the permission?"
            answer = "affirmative" if plural else "negative"
        else:
            english = f"{envelope} {subject}must {action} in round {round_number}; a later forwarded reader is outside the addressed set."
            ainglish = f"{envelope} {marked} must {action} in round {round_number}; a later forwarded reader is outside the addressed set."
            question = "Does merely receiving a forwarded copy make a later reader an addressee?"
            answer = "negative"
        rows.append(row(form, index, english.replace("  ", " "), ainglish, question, answer,
                        domain=domain, probe=probe, cardinality="plural" if plural else "singular"))
    return rows


def uncertainty(form: str) -> list[dict]:
    factual = form == "fact-not-known"
    rows = []
    evidence = ["signed ledger", "sensor archive", "sealed tally", "checksum log"]
    authorities = ["incident chair", "archive custodian", "fleet controller", "grant panel"]
    for index in range(N):
        domain, _, noun = DOMAINS[index % len(DOMAINS)]
        cycle = index // len(DOMAINS) + 31
        subject = f"the outcome of the {noun} in cycle {cycle}"
        if factual:
            english = (
                f"An existing {evidence[(index // 16) % 4]} determines {subject}, but the authenticated "
                "speaker lacks enough evidence to state the answer. Retrieving or deriving evidence can close the gap."
            )
        else:
            english = (
                f"The {authorities[(index // 16) % 4]} may select {subject}, but has made no operative selection. "
                "Only a new authorized selection can close the gap."
            )
        marked = f"{form} — {subject}."
        probe = index % 4
        if probe == 0:
            question = "Could retrieving all relevant records, with no new selection, close the gap?"
            answer = "affirmative" if factual else "negative"
        elif probe == 1:
            question = "Must an authorized actor make a new selection for the operative answer to exist?"
            answer = "negative" if factual else "affirmative"
        elif probe == 2:
            question = "Does the message assert that nobody anywhere already knows the answer?"
            answer = "negative"
        else:
            question = "Does the message itself instruct the reader to resolve the gap?"
            answer = "negative"
        rows.append(row(form, index, english, marked, question, answer,
                        domain=domain, probe=f"closure-{probe + 1}", mode="fact" if factual else "choice"))
    return rows


def delegation(form: str) -> list[dict]:
    none = form == "no-delegation"
    rows = []
    for index in range(N):
        domain, action, _ = DOMAINS[index % len(DOMAINS)]
        owner, delegate, onward = NAMES[index % len(NAMES)]
        cycle = index // len(DOMAINS) + 41
        task = f"{action} during cycle {cycle}"
        if none:
            english = (
                f"{owner} must {task}. {owner} may use deterministic tools but may not assign any "
                "completion-bearing part to another principal, and remains accountable."
            )
        else:
            english = (
                f"{owner} must {task}. {owner} may assign completion-bearing work to immediate delegates, "
                f"including {delegate}; an immediate delegate may not pass it onward to {onward}, and {owner} remains accountable."
            )
        marked = f"{owner} must {task}, {form}."
        probe = ("direct", "onward", "accountability", "tool")[index // 16]
        if probe == "direct":
            question = f"May {owner} assign a completion-bearing part directly to {delegate}?"
            answer = "negative" if none else "affirmative"
        elif probe == "onward":
            question = f"If {delegate} receives a permitted part, may {delegate} pass it onward to {onward}?"
            answer = "negative"
        elif probe == "accountability":
            question = f"After any permitted handoff, does {owner} remain accountable for completion?"
            answer = "affirmative"
        else:
            question = f"May {owner} use a deterministic tool under {owner}'s control?"
            answer = "affirmative"
        rows.append(row(form, index, english, marked, question, answer,
                        domain=domain, probe=probe, policy="none" if none else "one-hop"))
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


def calibration(form: str) -> list[dict]:
    card = reference_card(form)
    objects = ["bronze disk", "coral key", "flint card", "jade seal", "linen tag", "opal pass", "reed token", "silver badge"]
    rows = []
    for index, obj in enumerate(objects):
        rows.append({
            "id": f"rl-{form}-cal-{index + 1:02d}",
            "calibration": True,
            "english": f"{card}\n\nMessage: A note mentions the {obj} but gives no location.",
            "ainglish": f"{card}\n\nMessage: A note states that the {obj} is inside cabinet nine.",
            "question": "Would opening cabinet nine follow the stated location?",
            "options": rotate(["affirmative", "negative", "indeterminate"], index),
            "answer": "affirmative",
            "set": "construct-free reference-loaded positive control",
        })
    return rows


def main() -> None:
    receipt = {
        "kind": "ainglish.flagship-reference-loaded-freeze.v1",
        "seed": SEED,
        "reader_calls": 0,
        "deployment_condition": "one-shot pair-definition reference card present in both arms",
        "campaigns": {},
    }
    all_pairs = set()
    for form, builder in BUILDERS.items():
        scientific = builder(form)
        rows = scientific + calibration(form)
        assert len(scientific) == N and len(rows) == N + 8
        assert len({item["id"] for item in rows}) == len(rows)
        assert all(item["english"] != item["ainglish"] for item in rows)
        pairs = {(item["english"], item["ainglish"], item["question"]) for item in scientific}
        assert len(pairs) == N and not (pairs & all_pairs)
        all_pairs |= pairs
        digest = hashlib.sha256(canonical(rows)).hexdigest()
        payload = {
            "kind": "ainglish.flagship-reference-loaded-items.v1",
            "campaign": form,
            "seed": SEED,
            "sha256": digest,
            "design": f"{N} fresh scientific pairs plus eight construct-free calibration rows; both arms receive the same one-shot pair-definition reference card.",
            "items": rows,
        }
        path = ROOT / f"items-{form}.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        receipt["campaigns"][form] = {
            "path": path.name,
            "items_sha256": digest,
            "scientific": N,
            "calibration": 8,
        }
    unsealed = dict(receipt)
    receipt["content_sha256"] = hashlib.sha256(canonical(unsealed)).hexdigest()
    (ROOT / "freeze-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
