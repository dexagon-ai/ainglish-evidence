#!/usr/bin/env python3
"""Freeze four additional flagship comprehension carriers without inference."""

from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
V2_ROOT = ROOT.parent / "flagship-modern-carriers-v2-2026-08-27"
SPEC = importlib.util.spec_from_file_location("carrier_v2_build", V2_ROOT / "build.py")
assert SPEC and SPEC.loader
BASE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BASE)

PUBLISHED_COMMIT = "REPLACE_AFTER_FIRST_COMMIT"
PUBLISHED_BASE = (
    "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
    f"{PUBLISHED_COMMIT}/flagship-modern-carriers-v3-2026-08-27"
)

SLUGS = {
    "attribution": "by-unknown-by-withheld-typed-doer-omission-why-mistakes-were-3",
    "deadline": "start-by-complete-by-say-which-task-event-a-deadline-constra",
    "disjunction": "or-both-not-both-english-or-never-says-whether-both-is-allow",
    "polarity": "true-as-worded-false-as-worded-unambiguous-answers-to-negati",
}

CONTEXTS = [
    ("audit", "Nia", "audit ledger 41", "review the audit ledger"),
    ("release", "Sol", "release candidate 18", "sign the release receipt"),
    ("incident", "Teo", "incident report 73", "inspect the incident trace"),
    ("archive", "Mira", "archive batch 26", "classify the archive batch"),
    ("payment", "Oren", "payment record 55", "approve the payment record"),
    ("research", "Pia", "research sample 92", "review the research sample"),
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def seal(value: dict) -> dict:
    unsigned = dict(value)
    unsigned.pop("content_sha256", None)
    unsigned["content_sha256"] = hashlib.sha256(canonical(unsigned)).hexdigest()
    return unsigned


def write(name: str, value: dict) -> dict:
    sealed = seal(value)
    (ROOT / name).write_text(json.dumps(sealed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"file": name, "content_sha256": sealed["content_sha256"]}


def row(prefix: str, index: int, form: str, seam: str, english: str, ainglish: str,
        question: str, options: list[str], answer: str, extra: dict | None = None) -> dict:
    return BASE.row(prefix, index, form, seam, english, ainglish, question, options, answer, extra)


def calibrations(prefix: str) -> list[dict]:
    return BASE.calibrations(prefix)


def attribution() -> list[dict]:
    rows = []
    for i, (domain, actor, obj, _action) in enumerate(CONTEXTS):
        case = 5100 + i
        for form in ("by-unknown", "by-withheld"):
            unknown = form == "by-unknown"
            careful = (
                f"Case {case}: {obj} was changed. The author cannot name who changed it."
                if unknown else
                f"Case {case}: {obj} was changed. The author knows who changed it but deliberately does not name that person."
            )
            marked = f"Case {case}: {obj} was changed, {form}."
            common = {"domain": domain, "named_actor_distractor": actor, "author_can_name": not unknown}
            rows.extend([
                row("attr", i, form, "author-can-name", careful, marked,
                    "Could the author produce the doer's name from the author's present knowledge?",
                    ["yes", "no", "cannot tell"], "no" if unknown else "yes", common),
                row("attr", i, form, "author-next-hop", careful, marked,
                    "If the reader needs the doer's name, is asking the author a useful next hop?",
                    ["yes", "no", "cannot tell"], "no" if unknown else "yes", common),
                row("attr", i, form, "omission-cause", careful, marked,
                    "Why is the doer's name absent from this sentence?",
                    ["the author cannot name the doer", "the author knows but withholds the name", "the doer is authorised", "cannot tell"],
                    "the author cannot name the doer" if unknown else "the author knows but withholds the name", common),
                row("attr", i, form, "identity-nonclaim", careful, marked,
                    f"Does this marker itself identify {actor} as the doer?",
                    ["yes", "no", "cannot tell"], "no", common),
            ])
    return rows


def deadline() -> list[dict]:
    rows = []
    states = (
        ("queue-only", "The request was acknowledged and queued before the deadline, but execution had not begun.", False, False),
        ("started-unfinished", "Genuine execution began before the deadline, but the success condition remained unsatisfied then.", True, False),
        ("successful-completion", "Genuine execution began and the declared success condition was satisfied before the deadline.", True, True),
        ("terminal-failure", "Genuine execution began before the deadline and ended in failure before it; the success condition was never satisfied.", True, False),
    )
    for i, (domain, _actor, _obj, action) in enumerate(CONTEXTS):
        instant = f"2026-09-{10 + i:02d}T17:00:00Z"
        for form in ("start-by", "complete-by"):
            start = form == "start-by"
            careful_instruction = (
                f"Begin genuine execution of the task at or before {instant}; acknowledgement, queueing, or scheduling alone does not count."
                if start else
                f"Satisfy the task's declared success condition at or before {instant}; stopping or failure does not count."
            )
            marked_instruction = f"{action.capitalize()} {form}({instant})."
            for seam_index, (seam, state, began, succeeded) in enumerate(states):
                answer = "yes" if (began if start else succeeded) else "no"
                common = {"domain": domain, "genuine_execution_began": began, "success_condition_satisfied": succeeded}
                rows.append(row("dead", i, form, seam,
                    f"Instruction: {careful_instruction} Status: {state}",
                    f"Instruction: {marked_instruction} Status: {state}",
                    "Has the instruction's deadline condition been satisfied?",
                    ["yes", "no", "cannot tell"], answer, {**common, "state_index": seam_index + 1}))
    return rows


def disjunction() -> list[dict]:
    rows = []
    outcomes = (
        ("neither", "Neither option was selected.", False, False),
        ("left-only", "Only the first option was selected.", True, False),
        ("right-only", "Only the second option was selected.", False, True),
        ("both", "Both options were selected.", True, True),
    )
    for i, (domain, _actor, _obj, _action) in enumerate(CONTEXTS):
        left = f"use the {domain} fast path"
        right = f"use the {domain} audited path"
        for form in ("or-both", "not-both"):
            both_ok = form == "or-both"
            careful_instruction = (
                f"Select at least one of these two options: {left} or {right}; selecting both is permitted."
                if both_ok else
                f"Select exactly one of these two options: {left} or {right}; selecting both is forbidden."
            )
            marked_instruction = f"Select {left} or {right}, {form}."
            for seam_index, (seam, outcome, picked_left, picked_right) in enumerate(outcomes):
                compliant = (picked_left or picked_right) and (both_ok or not (picked_left and picked_right))
                common = {"domain": domain, "left_selected": picked_left, "right_selected": picked_right}
                rows.append(row("disj", i, form, seam,
                    f"Instruction: {careful_instruction} Outcome: {outcome}",
                    f"Instruction: {marked_instruction} Outcome: {outcome}",
                    "Does the outcome satisfy the selection instruction?",
                    ["yes", "no", "cannot tell"], "yes" if compliant else "no",
                    {**common, "outcome_index": seam_index + 1}))
    return rows


def polarity() -> list[dict]:
    rows = []
    groups = ["reviewer", "operator", "auditor", "archivist", "approver", "researcher"]
    for i, (domain, actor, obj, _action) in enumerate(CONTEXTS):
        approved = f"{actor} approved {obj}"
        not_approved = f"{actor} did not approve {obj}"
        frames = (
            ("positive", f"Did {actor} approve {obj}?", approved, not_approved),
            ("contracted-negative", f"Didn't {actor} approve {obj}?", not_approved, approved),
            ("uncontracted-not", f"Did {actor} not approve {obj}?", not_approved, approved),
            ("lexical-negative", f"Did {actor} reject {obj}?", f"{actor} rejected {obj}", f"{actor} did not reject {obj}"),
            ("scoped-quantifier", f"Did every {groups[i]} not approve {obj}?", f"no {groups[i]} approved {obj}", f"at least one {groups[i]} approved {obj}"),
            ("double-negation", f"Is it not true that {actor} did not approve {obj}?", approved, not_approved),
        )
        for form in ("true-as-worded", "false-as-worded"):
            is_true = form == "true-as-worded"
            careful_reply = (
                "The single proposition expressed by that entire question, preserving every written negation, is true."
                if is_true else
                "The single proposition expressed by that entire question, preserving every written negation, is false."
            )
            for seam_index, (seam, question_text, true_outcome, false_outcome) in enumerate(frames):
                answer = true_outcome if is_true else false_outcome
                options = [true_outcome, false_outcome, "the reply only expresses agreement", "cannot tell"]
                rows.append(row("pol", i, form, seam,
                    f"Question: {question_text} Reply: {careful_reply}",
                    f"Question: {question_text} Reply: {form}.",
                    "What real-world consequence does the reply assert?",
                    options, answer, {"domain": domain, "question_index": seam_index + 1}))
    return rows


def template(key: str, construct: str, rows: list[dict], seed: int) -> dict:
    counts = Counter(item["settlement_stratum"] for item in rows)
    assert set(counts.values()) == {6}
    items = calibrations(key) + rows
    artifact_name = f"{key}.items.json"
    items_sha = hashlib.sha256(canonical(items)).hexdigest()
    artifact = {"kind": "dexagon.ainglish.manifest-bound-panel-items.v3", "sha256": items_sha, "items": items}
    (ROOT / artifact_name).write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "kind": "dexagon.ainglish.manifest-bound-panel-template.v3",
        "proposal_revision": SLUGS[key],
        "slug": SLUGS[key],
        "construct": construct,
        "metric": "comprehension_accuracy_delta",
        "seed": seed,
        "comparator": {
            "kind": "complete-careful-english-v1",
            "description": "Every marked form is compared with its complete registered careful-English meaning; no bare or partial comparator enters the primary estimand.",
        },
        "settlement_strata": [{"id": ident, "weight": 1} for ident in sorted(counts)],
        "items": items,
        "items_artifact": {
            "file": artifact_name,
            "published_url": f"{PUBLISHED_BASE}/{artifact_name}",
            "items_sha256": items_sha,
        },
        "panel": [
            {"name": "REPLACE-QUALIFIED-READER-A", "provider": "replace", "model": "replace"},
            {"name": "REPLACE-QUALIFIED-READER-B", "provider": "replace", "model": "replace"},
        ],
        "panel_neff": 2,
        "panel_neff_axis": "reader",
        "scientific_items": len(rows),
        "calibration_items": 12,
        "settlement_design": "form x semantic seam; every cell is equal-weight and load-bearing",
        "filing_mode": "fresh modern stratified original",
        "activation": {
            "runnable": False,
            "reason": "The required two-lineage independently qualified reader roster remains closed at 1/2.",
            "how": "Use activate_nine.py after the roster gate clears; publish its exact outputs before attempt minting or reader spend.",
        },
        "model_calls": 0,
        "governance_writes": 0,
    }


def main() -> None:
    definitions = [
        ("attribution", "by-unknown / by-withheld", attribution(), 2026082761),
        ("deadline", "start-by / complete-by", deadline(), 2026082762),
        ("disjunction", "or-both / not-both", disjunction(), 2026082763),
        ("polarity", "true-as-worded / false-as-worded", polarity(), 2026082764),
    ]
    outputs = {}
    for key, construct, rows, seed in definitions:
        value = template(key, construct, rows, seed)
        receipt = write(f"{key}.template.json", value)
        receipt.update({
            "construct": construct,
            "proposal_revision": SLUGS[key],
            "scientific_items": len(rows),
            "settlement_strata": len(value["settlement_strata"]),
            "items_sha256": value["items_artifact"]["items_sha256"],
        })
        outputs[key] = receipt
    index = {
        "kind": "dexagon.ainglish.flagship-modern-carrier-index.v3",
        "purpose": "four additional flagship carriers with full semantic truth tables and careful-English comparators",
        "outputs": outputs,
        "population_status": "answer-bearing bytes frozen before every reader and governance call",
        "published_commit": PUBLISHED_COMMIT,
        "model_calls": 0,
        "governance_writes": 0,
    }
    write("index.json", index)
    print(json.dumps(index, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
