#!/usr/bin/env python3
"""Build the frozen completion-state zero-shot and learnability carriers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SLUG = "stopped-done-under-c-complete-for-r-say-which-claim-your-don"
REFERENCE = (
    "Reference: `stopped:` says only that work ceased and licenses no downstream action. "
    "`done-under(<C>):` says the result works under the named tested conditions C and licenses "
    "only cautious use that inherits C. `complete-for(<R>):` says the result is ready for the "
    "named consumer R and licenses unqualified action by R."
)

CONTEXTS = [
    ("customs-clearance packet", "sandbox customs rules v3", "the border-operations team"),
    ("satellite-calibration table", "simulator build 18 and thermal profile K", "the orbit-planning team"),
    ("accommodation matrix", "the agreed accessibility cases dated 17 May", "the student-services team"),
    ("seed-vault inventory", "vault aisle C and scanner firmware 9", "the conservation team"),
    ("ferry-maintenance checklist", "dry-dock procedure 6 and vessel class M", "the harbour engineer"),
    ("wildfire-evacuation map", "the north-wind scenario and road closures set B", "the incident commander"),
    ("trial-codebook extract", "synthetic cohort 4 and parser revision 12", "the statistical-review team"),
    ("museum-provenance ledger", "the digitised 1998 catalogue and fields P1-P7", "the collections curator"),
    ("floodgate-inspection record", "test rig G2 and the low-tide cycle", "the water-control team"),
    ("telescope-pointing model", "simulated mount A and sky grid 2026-Q3", "the night-observing team"),
    ("crop-quarantine certificate", "the greenhouse sample set and rulebook 14", "the port agronomist"),
    ("court-transcript index", "the redacted fixture bundle and index schema 5", "the disclosure team"),
    ("grid-restoration schedule", "island-mode simulation R7", "the control-room supervisor"),
    ("cold-chain log", "the mock shipment and sensor profile L4", "the distribution pharmacist"),
    ("aircraft-load sheet", "training flight ZM42 and balance table 11", "the dispatch officer"),
    ("archaeological survey map", "sector D scans and coordinate frame 3", "the field director"),
    ("water-quality dashboard", "laboratory fixtures Q1-Q8 and browser set C", "the public-health analyst"),
    ("emergency-shelter roster", "exercise roster E9 and duplicate rules 2", "the shelter coordinator"),
    ("fisheries-quota table", "the synthetic fleet register and policy year 2030", "the quota administrator"),
    ("radio-frequency licence", "the test application and spectrum plan S6", "the licensing officer"),
]

CLAIMS = {
    "stopped": {
        "marker": "stopped: {actor}'s work on the {thing}.",
        "careful": (
            "{actor} stopped working on the {thing}; {actor} makes no claim that it is correct, "
            "complete, or safe to use."
        ),
        "claim": "work stopped; no result claim",
        "action": "no downstream action is licensed",
    },
    "done-under": {
        "marker": "done-under({condition}): {actor}'s work on the {thing}.",
        "careful": (
            "{actor} reports that the {thing} works under {condition}; use outside those tested "
            "conditions is not licensed."
        ),
        "claim": "scoped correctness under named conditions",
        "action": "cautious use inheriting the named conditions",
    },
    "complete-for": {
        "marker": "complete-for({consumer}): {actor}'s work on the {thing}.",
        "careful": (
            "{actor} reports that the {thing} is complete for {consumer} to act on without an "
            "additional completion check."
        ),
        "claim": "unqualified handoff to the named consumer",
        "action": "unqualified action by the named consumer",
    },
}

CLAIM_OPTIONS = [
    "work stopped; no result claim",
    "scoped correctness under named conditions",
    "unqualified handoff to the named consumer",
]
ACTION_OPTIONS = [
    "no downstream action is licensed",
    "cautious use inheriting the named conditions",
    "unqualified action by the named consumer",
]
ACTORS = ["Ava", "Bo", "Cy", "Diya", "Eli"]


def rotate(values: list[str], offset: int) -> list[str]:
    offset %= len(values)
    return values[offset:] + values[:offset]


def canonical_hash(value: dict) -> str:
    payload = dict(value)
    payload.pop("sha256", None)
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def calibration_rows() -> list[dict]:
    seeds = [
        ("The north gate is closed.", "Is the north gate open?", ["yes", "no", "cannot tell"], "no"),
        ("Mina may use either desk.", "Is Mina forbidden from using both desks?", ["yes", "no", "cannot tell"], "no"),
        ("Exactly three samples passed.", "Did at least one sample pass?", ["yes", "no", "cannot tell"], "yes"),
        ("The report does not state who approved it.", "Can the approver be identified from the message?", ["yes", "no", "cannot tell"], "no"),
        ("Every listed valve was inspected.", "Was each listed valve inspected?", ["yes", "no", "cannot tell"], "yes"),
        ("The shipment arrives on Tuesday or Wednesday; no day is confirmed.", "Is Tuesday confirmed?", ["yes", "no", "cannot tell"], "no"),
        ("Ravi checked the first file but not the second.", "Did Ravi check both files?", ["yes", "no", "cannot tell"], "no"),
        ("The note says only that testing began.", "Does the note say testing finished?", ["yes", "no", "cannot tell"], "no"),
    ]
    return [
        {
            "id": f"calibration-{i:02d}",
            "message": message,
            "question": question,
            "options": rotate(options, i),
            "answer": answer,
        }
        for i, (message, question, options, answer) in enumerate(seeds, 1)
    ]


def build(condition_name: str) -> dict:
    rows = []
    claim_order = list(CLAIMS)
    for context_i, (thing, constraint, consumer) in enumerate(CONTEXTS, 1):
        actor = ACTORS[(context_i - 1) % len(ACTORS)]
        bare = f"Done: {actor}'s work on the {thing}."
        for claim_i, form in enumerate(claim_order):
            spec = CLAIMS[form]
            claim_target_position = (context_i + claim_i) % 3
            action_target_position = (context_i + (2 * claim_i)) % 3
            marked = spec["marker"].format(actor=actor, thing=thing, condition=constraint, consumer=consumer)
            careful = spec["careful"].format(actor=actor, thing=thing, condition=constraint, consumer=consumer)
            if condition_name == "definition_conditioned":
                marked = f"{REFERENCE}\nMessage: {marked}"
                bare_arm = f"{REFERENCE}\nMessage: {bare}"
                careful = f"{REFERENCE}\nMessage: {careful}"
            else:
                bare_arm = bare
            rows.append(
                {
                    "id": f"{form}-{context_i:02d}",
                    "context_id": f"completion-context-{context_i:02d}",
                    "form": form,
                    "arms": {
                        "ainglish": marked,
                        "bare_english": bare_arm,
                        "careful_english": careful,
                    },
                    "questions": [
                        {
                            "id": "claim_type",
                            "question": "Which completion claim does the sender make?",
                            "options": rotate(CLAIM_OPTIONS, claim_i - claim_target_position),
                            "answer": spec["claim"],
                        },
                        {
                            "id": "licensed_action",
                            "question": "What downstream action does the message license?",
                            "options": rotate(ACTION_OPTIONS, claim_i - action_target_position),
                            "answer": spec["action"],
                        },
                    ],
                    "strata": {
                        "condition": condition_name,
                        "domain": thing,
                        "claim_type": form,
                        "claim_answer_position": claim_target_position,
                        "action_answer_position": action_target_position,
                    },
                }
            )
    packet = {
        "kind": "dexagon.ainglish.completion-state-recertification-items.v1",
        "proposal_slug": SLUG,
        "condition": condition_name,
        "reference_card": REFERENCE if condition_name == "definition_conditioned" else None,
        "contract": {
            "metric": "comprehension_accuracy_delta",
            "primary_unit": "exact joint correctness on both questions for one isolated arm",
            "scientific_rows": 60,
            "rows_per_form": 20,
            "arms": ["ainglish", "bare_english", "careful_english"],
            "support": "each form: Ainglish minus bare >= 0.15 and Ainglish minus careful >= -0.05",
            "additional_falsifiers": [
                "stopped handoff over-read is not at least 0.15 lower than bare",
                "done-under is confused with complete-for on more than 0.10 of its rows",
                "complete-for is confused with done-under on more than 0.10 of its rows",
            ],
            "reporting": "per form, arm, reader lineage, and question; pooled values are secondary",
        },
        "reader_gate": {
            "minimum_independent_base_lineages": 2,
            "same_fresh_construct_free_holdout": True,
            "aliases_quantisations_and_finetunes_do_not_add_lineages": True,
            "status_at_freeze": "closed: retained local audit has one qualified lineage",
        },
        "scientific_rows": rows,
        "calibration_rows": calibration_rows(),
        "model_calls": 0,
        "governance_writes": 0,
    }
    packet["sha256"] = canonical_hash(packet)
    return packet


def main() -> None:
    for name, filename in (
        ("zero_shot", "zero-shot.json"),
        ("definition_conditioned", "definition-conditioned.json"),
    ):
        (ROOT / filename).write_text(
            json.dumps(build(name), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
