#!/usr/bin/env python3
"""Freeze five complete-pair token populations without loading a tokenizer."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
NAMES = [
    "Ava", "Bo", "Cy", "Diya", "Eli", "Fara", "Gus", "Hana",
    "Ivo", "Jia", "Kofi", "Luz", "Mara", "Noor", "Oren", "Pia",
]
ACTIONS = [
    "publish the draft", "inspect the log", "restart the queue", "validate the sample",
    "reconcile the invoice", "review the appeal", "check the quotation", "verify the specimen",
    "archive the bundle", "rotate the key", "deliver the report", "approve the release",
    "repair the mirror", "sign the receipt", "open the case", "close the incident",
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def contexts(count: int):
    for index in range(count):
        name = NAMES[index % len(NAMES)]
        action = ACTIONS[(index * 5 + index // len(NAMES)) % len(ACTIONS)]
        yield index, name, action


def may_not() -> list[dict]:
    rows = []
    for index, name, action in contexts(32):
        cycle = index + 1
        if index % 2 == 0:
            form = "may-not-as-prohibition"
            ainglish = f"In cycle {cycle}, {name} may-not-as-prohibition {action}."
            english = f"In cycle {cycle}, an applicable rule forbids this outcome: {name} will {action}; this predicts nothing about what happens."
        else:
            form = "may-not-as-possibility"
            ainglish = f"In cycle {cycle}, {name} may-not-as-possibility {action}."
            english = f"In cycle {cycle}, under the speaker's current evidence, it remains possible that this will not occur: {name} will {action}; this imposes no rule."
        rows.append({"id": f"may-not-{index + 1:03d}", "form": form, "english": english, "ainglish": ainglish})
    return rows


def must() -> list[dict]:
    rows = []
    for index, name, action in contexts(32):
        cycle = index + 1
        if index % 2 == 0:
            form = "must-as-rule"
            ainglish = f"In cycle {cycle}, {name} must-as-rule {action}."
            english = f"In cycle {cycle}, an applicable rule requires {name} to {action}; this does not assert that the action occurs."
        else:
            form = "must-as-inference"
            ainglish = f"In cycle {cycle}, {name} must-as-inference have completed the work to {action}."
            english = f"In cycle {cycle}, from the available evidence, the speaker concludes that {name} completed the work to {action}; this creates no duty."
        rows.append({"id": f"must-{index + 1:03d}", "form": form, "english": english, "ainglish": ainglish})
    return rows


def should() -> list[dict]:
    rows = []
    for index, name, action in contexts(32):
        cycle = index + 1
        if index % 2 == 0:
            form = "should-as-rule"
            ainglish = f"In cycle {cycle}, {name} should-as-rule {action}."
            english = f"In cycle {cycle}, a norm that applies here calls for {name} to {action}; whether it happens is a separate question."
        else:
            form = "should-as-forecast"
            ainglish = f"In cycle {cycle}, {name} should-as-forecast {action}."
            english = f"In cycle {cycle}, from how things normally go, the speaker expects {name} to {action}; no norm or recommendation is invoked."
        rows.append({"id": f"should-{index + 1:03d}", "form": form, "english": english, "ainglish": ainglish})
    return rows


def will() -> list[dict]:
    rows = []
    forms = ("will-as-promise", "will-as-plan", "will-as-forecast")
    for index, name, action in contexts(64):
        cycle = index + 1
        form = forms[index % 3]
        if form == "will-as-promise":
            ainglish = f"In cycle {cycle}, {name} will-as-promise {action}."
            english = f"In cycle {cycle}, {name} promises the reader to {action}; this statement creates the commitment, and failure without release wrongs the reader."
        elif form == "will-as-plan":
            ainglish = f"In cycle {cycle}, {name} will-as-plan {action}."
            english = f"In cycle {cycle}, {name}'s current plan is to {action}; it may change, but {name} owes the reader notice if it changes."
        else:
            ainglish = f"In cycle {cycle}, the process will-as-forecast cause {name} to {action}."
            english = f"In cycle {cycle}, the speaker expects the process to cause {name} to {action}; this prediction claims no control and creates no obligation."
        rows.append({"id": f"will-{index + 1:03d}", "form": form, "english": english, "ainglish": ainglish})
    return rows


def retention() -> list[dict]:
    rows = []
    objects = [
        ("upload the report", "index the archive"), ("publish the notice", "send the alert"),
        ("write the file", "update the catalogue"), ("copy the records", "delete the source"),
        ("approve the invoice", "release the payment"), ("store the sample", "notify the lab"),
        ("create the backup", "rotate the key"), ("archive the case", "close the ticket"),
    ]
    for index in range(32):
        cycle = index + 1
        first, second = objects[index % len(objects)]
        action_set = f"cycle {cycle} [{first}; {second}]"
        if index % 2 == 0:
            form = "all-or-nothing"
            ainglish = f"For the bounded actions {action_set}, all-or-nothing."
            english = f"For {action_set}, if any required member fails, no successful member effect may remain authoritative at terminal handoff; if that cannot be guaranteed, stop before acting."
        else:
            form = "keep-successes"
            ainglish = f"For the bounded actions {action_set}, keep-successes."
            english = f"For {action_set}, a successful member effect remains committed even if another member fails; disclose every failed or unattempted member separately."
        rows.append({"id": f"retention-{index + 1:03d}", "form": form, "english": english, "ainglish": ainglish})
    return rows


def main() -> None:
    target = ROOT / "items.json"
    if target.exists():
        raise SystemExit("REFUSING: items.json exists")
    campaigns = {
        "may-not": {"slug": "may-not-as-prohibition-may-not-as-possibility-forbidden-or-p", "test_set": may_not()},
        "must": {"slug": "must-as-rule-must-as-inference-does-must-impose-a-requiremen", "test_set": must()},
        "should": {"slug": "should-as-rule-should-as-forecast-is-should-a-norm-or-an-exp", "test_set": should()},
        "will": {"slug": "will-as-promise-will-as-plan-will-as-forecast-mark-whether-a-2", "test_set": will()},
        "retention": {"slug": "all-or-nothing-keep-successes-say-what-survives-when-part-of-2", "test_set": retention()},
    }
    for row in campaigns.values():
        pairs = row["test_set"]
        if len(pairs) & (len(pairs) - 1):
            raise SystemExit("REFUSING: pair count is not a power of two")
        if len({(item["english"], item["ainglish"]) for item in pairs}) != len(pairs):
            raise SystemExit("REFUSING: duplicate complete pair")
        row["items_sha256"] = hashlib.sha256(canonical(pairs)).hexdigest()
    payload = {"kind": "ainglish.modal-operational-token-items.v1", "campaigns": campaigns}
    payload["content_sha256"] = hashlib.sha256(canonical(payload)).hexdigest()
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({name: {"pairs": len(row["test_set"]), "sha256": row["items_sha256"]} for name, row in campaigns.items()}, indent=2))


if __name__ == "__main__":
    main()
