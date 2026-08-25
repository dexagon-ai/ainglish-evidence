#!/usr/bin/env python3
"""Freeze the remaining ratified language census without external calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FORMS = [
    "passed-not-applied",
    "human_needed",
    "stopped",
    "done-under",
    "complete-for",
    "claim-tag",
    "ctl-control",
    "ctl-none",
    "force-suspended",
    "eta",
    "still",
    "or-both",
    "not-both",
    "start-by",
    "complete-by",
    "each-alone",
    "as-one",
    "text-fixed",
    "meaning-fixed",
    "grader-is-graded",
    "true-as-worded",
    "false-as-worded",
    "by-unknown",
    "by-withheld",
]
DOMAINS = [
    ("release", "publish the release", "release record"),
    ("security", "rotate the access key", "access record"),
    ("operations", "restart the queue", "queue record"),
    ("research", "validate the sample", "sample record"),
    ("finance", "settle the invoice", "invoice record"),
    ("transport", "open the route", "route record"),
    ("moderation", "resolve the appeal", "appeal record"),
    ("procurement", "accept the quotation", "quotation record"),
]
NAMES = ["Ava", "Bo", "Cy", "Diya", "Eli", "Fara", "Gus", "Hana"]


REFERENCES = {
    "passed-not-applied": "passed-not-applied means accepted by a check, vote, or claim but not actually enacted or used.",
    "human_needed": "X human_needed(w) means X requires a human decision because of w; an agent must not resolve or act on X without it.",
    "stopped": "stopped: reports only that work ceased; it makes no correctness or completeness claim and licenses no downstream action.",
    "done-under": "done-under(C): asserts that the artifact works under named tested conditions C only; readers inherit that boundary.",
    "complete-for": "complete-for(R): asserts an unqualified handoff: the artifact is ready for named consumer R to build on.",
    "claim-tag": "[c=q; refute: F] appends the speaker's confidence q and the observation F that would show the assertion wrong.",
    "ctl-control": "X ctl(C) says the known-positive control C was demonstrated live in the same run, so the result could have differed.",
    "ctl-none": "X ctl(none) says no positive control was run, so the speaker cannot show the result could have differed.",
    "force-suspended": "force-suspended makes the remainder of its physical line mentioned text only; the current speaker does not issue any inner claim or request.",
    "eta": "X eta(t) promises a report-back about X at approximately t; earlier silence is not failure and later silence breaks the promise.",
    "still": "still(t) says the proposition was true at the last check t, no re-check has happened since, and truth now is unconfirmed.",
    "or-both": "A or B, or-both requires at least one and explicitly licenses choosing both.",
    "not-both": "A or B, not-both requires exactly one: at least one and not both.",
    "start-by": "ACTION start-by(t) requires genuine execution to begin at or before t; it adds no completion deadline.",
    "complete-by": "ACTION complete-by(t) requires the declared success condition by t; mere stop, timeout, or failure does not qualify.",
    "each-alone": "A plural predicate tagged each-alone holds independently of every member, producing one instance per member.",
    "as-one": "A plural predicate tagged as-one holds of the group as one unit, producing one collective instance; it does not state timing.",
    "text-fixed": "ACTION, text-fixed(ref) requires the referenced logical text's exact decoded Unicode sequence, including spacing and punctuation.",
    "meaning-fixed": "ACTION, meaning-fixed(ref) permits rewording but requires complete meaning, scope, force, attribution, and opaque literals to survive.",
    "grader-is-graded": "grader-is-graded says the evaluating party is also the evaluated party, so a pass shows agreement with self, not independent correctness.",
    "true-as-worded": "true-as-worded asserts the exact proposition obtained from the salient polar question while retaining every written negation.",
    "false-as-worded": "false-as-worded asserts the logical negation of the exact proposition in the salient polar question.",
    "by-unknown": "by-unknown says the author omits the doer because the author cannot name them.",
    "by-withheld": "by-withheld says the author knows the doer and deliberately chooses not to name them.",
}


def rotate(values: list[str], index: int) -> list[str]:
    shift = index % len(values)
    return values[shift:] + values[:shift]


def yes_no(index: int, positive_q: str, negative_q: str, truth: bool) -> tuple[str, list[str], str]:
    options = ["yes", "no", "cannot tell"]
    if index % 2 == 0:
        return positive_q, rotate(options, index), "yes" if truth else "no"
    return negative_q, rotate(options, index), "no" if truth else "yes"


def make(form: str, index: int) -> dict:
    domain, action, record = DOMAINS[index % len(DOMAINS)]
    name = NAMES[(index // len(DOMAINS)) % len(NAMES)]
    cycle = index // len(DOMAINS) + 1
    t = f"{12 + index % 8}:00Z"
    if form == "passed-not-applied":
        marker = f"The {domain} change passed-not-applied in cycle {cycle}."
        english = f"The {domain} change passed its check in cycle {cycle}, but it was not enacted or used."
        question, options, answer = yes_no(index, "Was the accepted change actually enacted?", "Did the change remain unapplied?", False)
    elif form == "human_needed":
        marker = f"Approve the {record} human_needed(conflicting policy owners)."
        english = f"Approving the {record} requires a human decision because policy owners conflict; an agent must not decide or act without it."
        question, options, answer = yes_no(index, "May an agent resolve and act on this without a human decision?", "Must an agent refrain until a human decides?", False)
    elif form == "stopped":
        marker = f"stopped: {name}'s work on the {record}."
        english = f"{name} stopped working on the {record}, making no claim that it is correct, complete, or safe to use."
        question, options, answer = yes_no(index, "Does the message license a consumer to build on the result?", "Does the message decline to assert result correctness?", False)
    elif form == "done-under":
        condition = f"linux-{cycle} with fixture-{index + 11}"
        marker = f"done-under({condition}): the {record}."
        english = f"The {record} works under the tested conditions {condition}; no claim is made outside those conditions."
        question, options, answer = yes_no(index, "Does this guarantee the result under untested conditions?", "Is the correctness claim limited to the named tested conditions?", False)
    elif form == "complete-for":
        consumer = f"team-{name.lower()}"
        marker = f"complete-for({consumer}): the {record}."
        english = f"The {record} is complete and ready for {consumer} to act on without a further qualification."
        question, options, answer = yes_no(index, "May the named consumer build on the handoff as complete?", "Does the marker withhold an unqualified handoff from the named consumer?", True)
    elif form == "claim-tag":
        confidence = ["0.55", "0.70", "0.85", "0.95"][index % 4]
        falsifier = f"three authenticated {domain} checks fail"
        marker = f"The {record} is sound [c={confidence}; refute: {falsifier}]."
        english = f"I am {float(confidence) * 100:.0f}% confident that the {record} is sound; observing that {falsifier} would show my assertion wrong."
        options = rotate([
            f"confidence={confidence}; refuter={falsifier}",
            f"confidence=1.00; refuter={falsifier}",
            f"confidence={confidence}; refuter=no possible observation",
            "confidence and refuter are both unstated",
        ], index)
        question = "What confidence and falsifying observation does the writer declare?"
        answer = f"confidence={confidence}; refuter={falsifier}"
    elif form in {"ctl-control", "ctl-none"}:
        control = f"known-positive-{domain}-{cycle}"
        if form == "ctl-control":
            marker = f"No effect detected ctl({control})."
            english = f"No effect was detected, and {control} was demonstrated live in the same run, showing that the result could have differed."
            truth = True
        else:
            marker = "No effect detected ctl(none)."
            english = "No effect was detected, but no positive control was run, so the writer cannot show that the result could have differed."
            truth = False
        question, options, answer = yes_no(index, "Was a known-positive control demonstrated live in this run?", "Did this run lack a demonstrated positive control?", truth)
    elif form == "force-suspended":
        inner = f"req: {action}"
        marker = f"force-suspended — {inner}"
        english = f"I display the text '{inner}' for inspection only; I do not issue its request."
        question, options, answer = yes_no(index, "Did the current writer issue the displayed request?", "Are the request words merely mentioned rather than issued?", False)
    elif form == "eta":
        marker = f"Status of the {record} eta({t})."
        english = f"The writer promises to report back about the {record} at approximately {t}; silence before then is not failure, and silence after then breaks the promise."
        if index % 2 == 0:
            question, options, answer = "Is silence one minute before the named time a broken promise?", rotate(["yes", "no", "cannot tell"], index), "no"
        else:
            question, options, answer = "If no report arrives after the named time, is the report-back promise broken?", rotate(["yes", "no", "cannot tell"], index), "yes"
    elif form == "still":
        marker = f"The {record} is valid still(check-{cycle})."
        english = f"The {record} was valid at check-{cycle}; it has not been checked again, so validity now is unconfirmed."
        question, options, answer = yes_no(index, "Does this say present validity was re-verified after the named check?", "Does the message leave present validity unconfirmed?", False)
    elif form in {"or-both", "not-both"}:
        marker = f"For the {domain} response, {action} or archive the request, {form}."
        both = form == "or-both"
        english = (
            f"For the {domain} response, do at least one of these: {action}, or archive the request; doing both is allowed."
            if both else f"For the {domain} response, do exactly one of these: {action}, or archive the request; do not do both."
        )
        question, options, answer = yes_no(index, "Does satisfying the instruction permit doing both listed actions?", "Is doing both listed actions forbidden?", both)
    elif form in {"start-by", "complete-by"}:
        marker = f"{action} {form}({t})."
        if form == "start-by":
            english = f"Begin genuine execution of '{action}' no later than {t}; it need not be complete then."
            options = rotate(["actual execution must have begun", "successful completion must have occurred", "only scheduling is required"], index)
            answer = "actual execution must have begun"
        else:
            english = f"Satisfy the successful completion condition of '{action}' no later than {t}; merely stopping or failing does not satisfy it."
            options = rotate(["actual execution must have begun", "successful completion must have occurred", "only scheduling is required"], index)
            answer = "successful completion must have occurred"
        question = "What must be true at the named deadline?"
    elif form in {"each-alone", "as-one"}:
        people = f"{name}, {NAMES[(index + 1) % len(NAMES)]}, and {NAMES[(index + 2) % len(NAMES)]}"
        marker = f"{people} verified the {record}, {form}."
        if form == "each-alone":
            english = f"Each of {people} independently verified the {record}, producing three verification instances."
            answer = "three independent verification instances"
        else:
            english = f"The group consisting of {people} jointly verified the {record} as one unit, producing one verification instance."
            answer = "one collective verification instance"
        options = rotate(["three independent verification instances", "one collective verification instance", "the sentence gives no multiplicity"], index)
        question = "How many verification instances does the sentence assert?"
    elif form in {"text-fixed", "meaning-fixed"}:
        ref = f"span-{domain}-{cycle}"
        marker = f"Publish the referenced instruction, {form}({ref})."
        if form == "text-fixed":
            english = f"Publish {ref} with the exact decoded words, case, punctuation, spacing, and line breaks; paraphrase inside the span is forbidden."
            answer = "exact text required; meaning-preserving paraphrase forbidden"
        else:
            english = f"Publish {ref} with complete meaning, scope, force, attribution, and opaque literals preserved; rewording is allowed when all survive."
            answer = "exact text optional; complete meaning required"
        options = rotate([
            "exact text required; meaning-preserving paraphrase forbidden",
            "exact text optional; complete meaning required",
            "lossy summary allowed",
            "the reference may be changed silently",
        ], index)
        question = "Which preservation rule constrains the referenced span?"
    elif form == "grader-is-graded":
        marker = f"The {domain} evaluation is grader-is-graded."
        english = f"The party evaluating the {domain} result is the same party being evaluated, so a pass shows agreement with self rather than independent correctness."
        question, options, answer = yes_no(index, "Does a pass here independently certify correctness?", "Is the evaluator the same party as the evaluated party?", False)
    elif form in {"true-as-worded", "false-as-worded"}:
        negative = index % 2 == 0
        if negative:
            polar = f"Didn't {name} {action}?"
            p = f"{name} did not {action}"
            not_p = f"{name} did {action}"
        else:
            polar = f"Did {name} fail to {action}?"
            p = f"{name} failed to {action}"
            not_p = f"{name} did not fail to {action}"
        marker = f"{polar} {form}."
        if form == "true-as-worded":
            english = f"Question: {polar} Answer: the exact proposition as worded is true; therefore {p}."
            answer = p
        else:
            english = f"Question: {polar} Answer: the exact proposition as worded is false; therefore {not_p}."
            answer = not_p
        options = rotate([p, not_p, "the answer expresses agreement but no truth value", "cannot tell"], index)
        question = "What state of affairs does the answer assert?"
    elif form in {"by-unknown", "by-withheld"}:
        marker = f"The {record} was deleted {form}."
        known = form == "by-withheld"
        english = (
            f"The {record} was deleted by a party known to the author whom the author deliberately chooses not to name."
            if known else f"The {record} was deleted by a party the author cannot name because their identity is unknown to the author."
        )
        question, options, answer = yes_no(index, "Could the author supply the doer's name if asked?", "Is the doer's identity unknown to the author?", known)
    else:
        raise AssertionError(form)
    return {
        "id": f"{form}-{index + 1:03d}",
        "proposal_form": form,
        "scenario_id": f"{form}-cell-{index + 1:03d}",
        "cold_ainglish": marker,
        "reference_loaded_ainglish": f"Reference: {REFERENCES[form]}\nMessage: {marker}",
        "careful_english": english,
        "reference": REFERENCES[form],
        "question": question,
        "options": options,
        "answer": answer,
        "strata": {"domain": domain, "cycle": cycle, "probe_orientation": index % 2},
    }


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    rows = [make(form, index) for form in FORMS for index in range(32)]
    assert len(rows) == len(FORMS) * 32
    assert len({row["id"] for row in rows}) == len(rows)
    assert all(row["answer"] in row["options"] for row in rows)
    blob = canonical(rows)
    (ROOT / "items.json").write_bytes(blob + b"\n")
    index = {
        "kind": "ainglish.ratified-language-census.v1",
        "proposals": 15,
        "forms": len(FORMS),
        "rows": len(rows),
        "rows_per_form": 32,
        "arms": ["cold_ainglish", "reference_loaded_ainglish", "careful_english"],
        "items_sha256": hashlib.sha256(blob).hexdigest(),
        "form_counts": {form: sum(row["proposal_form"] == form for row in rows) for form in FORMS},
    }
    (ROOT / "index.json").write_text(json.dumps(index, indent=2, sort_keys=True) + "\n")
    print(json.dumps(index, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
