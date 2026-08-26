#!/usr/bin/env python3
"""Build the frozen role-cardinality comprehension campaigns offline."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SEED = 2026082653
SLUG = "one-or-more-role-exactly-one-role-does-a-reviewer-require-at"
OPTIONS = ("yes", "no", "cannot tell")
ROLES = (
    ("reviewer", "approve the release", "approved the release", "release", "approved"),
    ("auditor", "sign the manifest", "signed the manifest", "manifest", "signed"),
    ("maintainer", "authorise the deployment", "authorised the deployment", "deployment", "authorised"),
    ("operator", "activate the failover", "activated the failover", "failover", "activated"),
    ("moderator", "decide the appeal", "decided the appeal", "appeal", "decided"),
    ("custodian", "attest to the artifact", "attested to the artifact", "artifact", "attested to"),
    ("observer", "verify the incident", "verified the incident", "incident", "verified"),
    ("editor", "publish the notice", "published the notice", "notice", "published"),
    ("arbiter", "settle the dispute", "settled the dispute", "dispute", "settled"),
    ("steward", "accept the dataset", "accepted the dataset", "dataset", "accepted"),
)


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def answer_options(answer: str, ordinal: int) -> list[str]:
    others = [value for value in OPTIONS if value != answer]
    position = ordinal % 3
    values = others[:]
    values.insert(position, answer)
    return values


def instruction(form: str, role: str, action: str, obj: str, participle: str, comparison: str, passive: bool) -> str:
    if comparison == "bare":
        return f"The {obj} must be {participle} by a {role}." if passive else f"A {role} must {action}."
    if form == "one-or-more":
        if passive:
            return (
                f"The {obj} must be {participle} by at least one distinct {role}; additional distinct "
                f"{role}s may also do so without violating this instruction."
            )
        return (
            f"At least one distinct {role} must {action}; additional distinct {role}s may also do "
            "so without violating this instruction."
        )
    if passive:
        return (
            f"The {obj} must be {participle} by one and only one distinct {role}; zero or two-or-more "
            f"distinct {role}s violate this instruction."
        )
    return (
        f"One and only one distinct {role} must {action}; zero or two-or-more distinct {role}s "
        "violate this instruction."
    )


def marked(form: str, role: str, action: str, obj: str, participle: str, passive: bool) -> str:
    clause = f"the {obj} must be {participle}" if passive else action
    return f"{form}({role}): {clause}."


def binary_question(positive: str, negative: str, truth: bool, role_index: int, cell: int) -> tuple[str, str]:
    if (role_index + cell) % 2 == 0:
        return positive, "yes" if truth else "no"
    return negative, "no" if truth else "yes"


def semantic_cell(form: str, role: str, action: str, past: str, role_index: int, cell: int) -> tuple[str, str, str, dict]:
    plural = role + "s"
    if cell == 0:
        context = f"The execution record shows that no distinct {role} {past}."
        question, answer = binary_question(
            "Does the recorded outcome satisfy the instruction?",
            "Does the recorded outcome violate the instruction?",
            False, role_index, cell,
        )
        stratum = "zero-distinct"
    elif cell == 1:
        context = f"The execution record shows that Rowan was the sole distinct {role} who {past}."
        question, answer = binary_question(
            "Does the recorded outcome satisfy the instruction?",
            "Does the recorded outcome violate the instruction?",
            True, role_index, cell,
        )
        stratum = "one-distinct"
    elif cell == 2:
        context = f"The execution record shows that Rowan and Sable are distinct {plural}, and both {past}."
        truth = form == "one-or-more"
        question, answer = binary_question(
            "Does the recorded outcome satisfy the instruction?",
            "Does the recorded outcome violate the instruction?",
            truth, role_index, cell,
        )
        stratum = "two-distinct-load-bearing"
    elif cell == 3:
        context = f"Rowan is a qualifying {role} and has already {past}. Sable is a different qualifying {role} and is ready to do the same."
        truth = form == "one-or-more"
        question, answer = binary_question(
            "Could Sable also act while the instruction remains satisfied?",
            "Would Sable also acting necessarily violate the instruction?",
            truth, role_index, cell,
        )
        stratum = "additional-principal-load-bearing"
    elif cell == 4:
        context = f"Rowan, a qualifying {role}, {past} twice. No other {role} acted."
        question, answer = binary_question(
            "Does the recorded outcome satisfy the instruction?",
            "Does performing the action twice by itself make the recorded outcome violate the instruction?",
            True, role_index, cell,
        )
        stratum = "repeat-action-one-principal"
    elif cell == 5:
        context = f"The accounts Rowan-A and Rowan-B each {past}, but the identity ledger proves both accounts belong to the same qualifying {role}, Rowan. No other {role} acted."
        question, answer = binary_question(
            "Does the identity ledger leave exactly one distinct qualifying principal in the recorded outcome?",
            "Do the two account names establish two distinct qualifying principals?",
            True, role_index, cell,
        )
        stratum = "aliases-one-principal"
    elif cell == 6:
        context = f"Rowan, a qualifying {role}, {past}. Two people serving only as witnesses also signed the surrounding record, but neither is a {role}."
        question, answer = binary_question(
            f"Are the witness-only signers excluded when counting principals in the named {role} role?",
            f"Do the witness-only signers increase the number of qualifying {plural} for this instruction?",
            True, role_index, cell,
        )
        stratum = "named-role-scope"
    elif cell == 7:
        context = f"The entire {role} pool is Rowan and Sable. The record states that some-but-not-all({plural}) {past}."
        question, answer = binary_question(
            "Do these facts establish that the action was performed by the only possible proper nonempty subset of the pool?",
            "Do these facts leave open whether neither or both pool members acted?",
            True, role_index, cell,
        )
        stratum = "bounded-two-person-seam"
    elif cell == 8:
        context = f"The entire {role} pool is Rowan, Sable, and Tern. The record states that some-but-not-all({plural}) {past}, without identifying the subset."
        question = "Did the acting subset contain the lower possible number of qualifying principals?"
        answer = "cannot tell"
        stratum = "bounded-three-person-seam"
    elif cell == 9:
        context = f"Rowan was the sole distinct {role} who {past}. The record says nothing about how Rowan formed the judgement."
        question = "Was the qualifying judgement independent of every other participant's judgement?"
        answer = "cannot tell"
        stratum = "independence-nonclaim"
    elif cell == 10:
        context = f"Rowan was the sole distinct {role} who {past}. The record says nothing about delegation."
        question = "Would assigning the action to a delegate have been permitted?"
        answer = "cannot tell"
        stratum = "delegation-nonclaim"
    elif cell == 11:
        context = f"Rowan was the sole distinct {role} who {past}. A separate observer role exists, but its membership is not recorded."
        question = "Is Rowan also permitted to fill the separate observer role?"
        answer = "cannot tell"
        stratum = "cross-role-nonclaim"
    else:
        raise AssertionError(cell)
    return context, question, answer, {"cell": cell, "stratum": stratum}


def build_campaign(form: str, comparison: str) -> tuple[dict, dict]:
    rows = []
    scientific = []
    for role_index, (role, action, past, obj, participle) in enumerate(ROLES):
        for cell in range(12):
            ordinal = role_index * 12 + cell
            passive = role_index % 2 == 1
            context, question, answer, strata = semantic_cell(form, role, action, past, role_index, cell)
            baseline = context + " Instruction: " + instruction(form, role, action, obj, participle, comparison, passive)
            target = context + " Instruction: " + marked(form, role, action, obj, participle, passive)
            row = {
                "id": f"role-cardinality-{form}-{comparison}-{ordinal + 1:03d}",
                "english": baseline,
                "ainglish": target,
                "question": question,
                "options": answer_options(answer, ordinal),
                "answer": answer,
                "form": form,
                "comparison": comparison,
                "scenario_id": f"role-cardinality-{role_index + 1:02d}-{cell + 1:02d}",
                "strata": {"role": role, "voice": "passive" if passive else "active", **strata},
            }
            rows.append(row)
            scientific.append(row)
    for index in range(8):
        token = f"calibration-{form}-{comparison}-{index + 1:02d}"
        answer = ("yes", "no")[index % 2]
        rows.append({
            "id": f"role-cardinality-{form}-{comparison}-cal-{index + 1:02d}",
            "calibration": True,
            "english": f"The routing note for {token} says bay fourteen is " + ("open." if answer == "yes" else "closed."),
            "ainglish": f"The routing note for {token} says bay fourteen is " + ("open." if answer == "yes" else "closed."),
            "question": "Is bay fourteen described as open?",
            "options": answer_options(answer, index),
            "answer": answer,
            "set": "construct-free literal control",
        })
    counts = {label: sum(row["answer"] == label for row in scientific) for label in OPTIONS}
    positions = {str(position): sum(row["options"].index(row["answer"]) == position for row in scientific) for position in range(3)}
    assert len(scientific) == 120 and len(rows) == 128
    assert counts == {"yes": 40, "no": 40, "cannot tell": 40}
    assert positions == {"0": 40, "1": 40, "2": 40}
    digest = hashlib.sha256(canonical(rows)).hexdigest()
    filename = f"items-{form}-{comparison}.json"
    payload = {
        "kind": "dexagon.ainglish.role-cardinality-comprehension-carrier.v1",
        "proposal_revision": SLUG,
        "form": form,
        "comparison": comparison,
        "seed": SEED,
        "sha256": digest,
        "population": "120 operational role-cardinality items over ten roles and twelve semantic cells, plus eight construct-free calibrations",
        "aggregation": "form-separated paired accuracy delta; report absolute arms and all cells, never pool forms or comparator classes",
        "reader_calls": 0,
        "items": rows,
    }
    receipt = {"file": filename, "items_sha256": digest, "scientific": 120, "calibration": 8, "answer_counts": counts, "answer_positions": positions}
    return payload, receipt


def main() -> None:
    campaigns = {}
    for form in ("one-or-more", "exactly-one"):
        for comparison in ("careful", "bare"):
            payload, receipt = build_campaign(form, comparison)
            (ROOT / receipt["file"]).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            campaigns[f"{form}-vs-{comparison}"] = receipt
    index = {
        "kind": "dexagon.ainglish.role-cardinality-comprehension-freeze.v1",
        "proposal_revision": SLUG,
        "seed": SEED,
        "scientific_items_per_campaign": 120,
        "calibrations_per_campaign": 8,
        "campaigns": campaigns,
        "reader_calls": 0,
        "governance_writes": 0,
        "execution_gate": "proposal seconded, token prerequisite complete, and at least two independently qualified reader lineages",
    }
    index["content_sha256"] = hashlib.sha256(canonical(index)).hexdigest()
    (ROOT / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(index, indent=2))


if __name__ == "__main__":
    main()
