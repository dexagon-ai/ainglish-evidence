#!/usr/bin/env python3
"""Freeze separate careful-English carriers for by-construction/by-rule/in-practice."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FORMS = ("by-construction", "by-rule", "in-practice")
QUESTION = (
    "Under the claim as written, could an exception occur without the system being changed? "
    "If an exception is then observed while the system is unchanged, what follows?"
)
PROFILES = {
    "by-construction": "no / the claim was false",
    "by-rule": "yes / breach and repair owed",
    "in-practice": "yes / news only; nothing owed",
}
OPTIONS = [
    "no / the claim was false",
    "yes / breach and repair owed",
    "yes / news only; nothing owed",
    "no / breach and repair owed",
    "cannot tell / cannot tell",
]


FRAMES = {
    "infrastructure": [
        ("The ingress rejects requests that lack a tenant identifier", "gateway owner"),
        ("The scheduler keeps two leaders from holding the same lease", "cluster operator"),
        ("The replica serves reads only after applying the committed index", "database owner"),
        ("The deployment controller blocks images without a trusted signature", "release owner"),
        ("The queue retains messages until one consumer acknowledges them", "messaging owner"),
        ("The backup service encrypts every snapshot before upload", "backup owner"),
        ("The proxy strips internal headers from external responses", "edge owner"),
        ("The allocator keeps reserved capacity available for emergency jobs", "capacity owner"),
    ],
    "data": [
        ("The export contains a provenance record for every included row", "data steward"),
        ("The ledger assigns each transfer a monotonically increasing sequence", "ledger owner"),
        ("The warehouse stores deletion receipts beside retired identifiers", "privacy owner"),
        ("The parser records the source byte range for every extracted field", "parser owner"),
        ("The catalogue links every published dataset to a licence record", "catalogue owner"),
        ("The archive preserves the checksum supplied at ingestion", "archive owner"),
        ("The report separates missing observations from measured zeroes", "analytics owner"),
        ("The index retains the original event time beside processing time", "index owner"),
    ],
    "security": [
        ("The vault releases a secret only after two distinct approvals", "security owner"),
        ("The login service expires recovery links after their first use", "identity owner"),
        ("The build pipeline records the signer of every promoted artifact", "supply-chain owner"),
        ("The firewall denies administrative traffic from public networks", "network owner"),
        ("The audit stream includes every privileged configuration change", "audit owner"),
        ("The token service binds each delegated credential to one audience", "credential owner"),
        ("The moderation queue hides quarantined material from public reads", "moderation owner"),
        ("The key ceremony records every custodian who handled a shard", "ceremony owner"),
    ],
    "workflow": [
        ("The review queue assigns each change to an independent approver", "review owner"),
        ("The release checklist records every failed prerequisite", "release coordinator"),
        ("The incident rota names one accountable commander per shift", "operations manager"),
        ("The translation process preserves unresolved terms for adjudication", "localisation owner"),
        ("The claims process acknowledges every complete submission", "claims owner"),
        ("The publication workflow exposes every outstanding objection", "editorial owner"),
        ("The procurement process records the reason for every excluded bid", "procurement owner"),
        ("The migration plan pairs every destructive step with a rollback check", "migration owner"),
    ],
    "physical": [
        ("The enclosure keeps conductive tools away from the live bus", "laboratory owner"),
        ("The airlock prevents both doors from opening together", "facility owner"),
        ("The reservoir alarm activates before the pump runs dry", "plant owner"),
        ("The lift remains stationary while its outer door is open", "maintenance owner"),
        ("The cold room records temperature throughout every storage interval", "cold-chain owner"),
        ("The charging cabinet isolates a bay after detecting excess heat", "equipment owner"),
        ("The clean-room gate logs every entry during a production run", "site owner"),
        ("The test stand contains fragments produced by a failed specimen", "test owner"),
    ],
    "governance": [
        ("The committee publishes a conflict declaration for every voting member", "committee chair"),
        ("The ballot record includes every accepted vote exactly once", "election officer"),
        ("The appeals process gives each appellant a written disposition", "appeals owner"),
        ("The budget report identifies every transfer from the reserve", "finance owner"),
        ("The standards process records the resolution of every formal objection", "standards chair"),
        ("The membership register dates every change in voting status", "membership owner"),
        ("The consultation archive preserves every response received before closure", "consultation owner"),
        ("The ethics review records each condition attached to approval", "ethics chair"),
    ],
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def rotate(answer: str, position: int) -> list[str]:
    values = [value for value in OPTIONS if value != answer]
    values.insert(position, answer)
    return values


def surfaces(form: str, statement: str, owner: str, variant: int) -> tuple[str, str, str]:
    intention = (
        "The team says this outcome was deliberate, but intention alone is not an enforcement mechanism. "
        if variant == 1 else ""
    )
    ceremony = (
        "A visible checklist accompanies the process, but this sentence makes no separate claim "
        "that the checklist causes the outcome. " if variant == 2 else ""
    )
    removal = (
        "The claim concerns the current arrangement and what follows if an exception appears without a change. "
        if variant == 3 else ""
    )
    context = intention + ceremony + removal
    if form == "by-construction":
        marked = f"{context}{statement}, by-construction."
        careful = (
            f"{context}{statement}. The current structure makes an exception impossible unless "
            "the system is changed."
        )
        trap = "intent" if variant == 1 else "removal_test" if variant == 3 else "ordinary"
    elif form == "by-rule":
        marked = f"{context}{statement}, by-rule; {owner} owes repair for an exception."
        careful = (
            f"{context}A standing rule requires this statement to hold: {statement}. "
            f"An exception remains possible; if one occurs, {owner} is in breach and owes repair."
        )
        trap = "ceremony" if variant == 2 else "named_owner"
    else:
        marked = f"{context}{statement}, in-practice."
        careful = (
            f"{context}{statement} in observations so far. An exception remains possible, and if "
            "one occurs it is news; this observation alone makes nobody owe repair."
        )
        trap = "intent" if variant == 1 else "vacuous_success" if variant == 2 else "ordinary"
    return careful, marked, trap


def build_form(form: str) -> dict:
    answer = PROFILES[form]
    real = []
    ordinal = 0
    for domain, frames in FRAMES.items():
        for local_index, (statement, owner) in enumerate(frames):
            english, ainglish, trap = surfaces(form, statement, owner, local_index % 4)
            position = ordinal % len(OPTIONS)
            real.append({
                "id": f"{form}-real-{ordinal + 1:02d}",
                "english": english,
                "ainglish": ainglish,
                "question": QUESTION,
                "options": rotate(answer, position),
                "answer": answer,
                "strata": {
                    "form": form,
                    "domain": domain,
                    "case": trap,
                    "answer_position": position,
                },
            })
            ordinal += 1

    calibration = []
    for index in range(8):
        position = (index + 1) % len(OPTIONS)
        if form == "by-construction":
            explicit = (
                "The claim says an exception cannot occur while the system is unchanged. If one "
                "does occur without a change, the claim was false."
            )
        elif form == "by-rule":
            explicit = (
                "The claim says an exception can occur, but a standing rule makes the named owner "
                "in breach and responsible for repair."
            )
        else:
            explicit = (
                "The claim reports only an observed pattern. An exception can occur; it would be "
                "news and the observation alone makes nobody owe repair."
            )
        calibration.append({
            "id": f"{form}-cal-{index + 1:02d}",
            "calibration": True,
            "english": (
                f"Calibration case {index + 1} contains a claim about whether exceptions can "
                "occur and what follows, but its substantive content is unavailable."
            ),
            "ainglish": f"Calibration case {index + 1}. {explicit}",
            "question": QUESTION,
            "options": rotate(answer, position),
            "answer": answer,
            "strata": {"form": form, "control": "construct_free_planted_effect"},
        })

    assert ordinal == 48
    assert Counter(row["strata"]["domain"] for row in real) == {domain: 8 for domain in FRAMES}
    assert all(Counter(row["strata"]["answer_position"] for row in real)[p] in (9, 10) for p in range(5))
    assert len({(row["english"], row["ainglish"]) for row in real + calibration}) == 56
    items = calibration + real
    digest = hashlib.sha256(canonical(items)).hexdigest()
    return {
        "kind": "ainglish.evidence.packet.v1",
        "proposal": "by-construction-by-rule-in-practice-mark-whether-a-standing-",
        "form": form,
        "seed_base": 2026082370 + FORMS.index(form) * 100,
        "reader_calls": 0,
        "real_items": 48,
        "calibration_items": 8,
        "sha256": digest,
        "items": items,
    }


def main() -> None:
    receipts = []
    for form in FORMS:
        document = build_form(form)
        path = ROOT / f"{form}-items.json"
        path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        receipts.append({
            "form": form,
            "path": path.name,
            "items_sha256": document["sha256"],
            "exact_file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "reader_calls": 0,
            "real_items": 48,
            "calibration_items": 8,
        })
    freeze = {"kind": "ainglish.evidence.freeze.v1", "reader_calls": 0, "files": receipts}
    (ROOT / "freeze-receipt.json").write_text(json.dumps(freeze, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(freeze, indent=2))


if __name__ == "__main__":
    main()
