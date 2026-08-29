#!/usr/bin/env python3
"""Build disjoint zero-shot and definition-conditioned clusivity carriers."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SLUG = "we-including-you-we-excluding-you-clusivity-mark-whether-we--4"
REFERENCE = (
    "Reference: `we-including-you` means that the first-person plural group includes you, the addressee, "
    "so the stated group predicate applies to you. `we-excluding-you` means that the first-person plural "
    "group excludes you, so the stated group predicate does not apply to you through that group. Neither "
    "marker says whether people outside the group independently have the same duty, permission, action, or status."
)
FORMS = {
    "we-including-you": {
        "membership": "included in the we-group",
        "consequence": "yes",
        "careful": "Our group includes you, the addressee; we {predicate}, so the predicate applies to you as a member of that group.",
    },
    "we-excluding-you": {
        "membership": "excluded from the we-group",
        "consequence": "no",
        "careful": "Our group does not include you, the addressee; we {predicate}, so this sentence does not apply that predicate to you.",
    },
}
MEMBERSHIP_OPTIONS = ["included in the we-group", "excluded from the we-group", "not stated"]
TERNARY_OPTIONS = ["yes", "no", "not stated"]


DOMAINS = [
    ("harbour anchor ledger", "berth plan H7", "Friday noon"),
    ("wildfire route map", "closure set C", "the 16:00 briefing"),
    ("museum loan register", "insurance schedule 12", "Monday morning"),
    ("satellite pointing table", "orbit profile K", "the next pass"),
    ("accessibility checklist", "reader profile A4", "the release review"),
    ("water-quality dashboard", "sensor set Q", "tomorrow's handover"),
    ("cold-chain log", "shipment batch L9", "the pharmacy cutoff"),
    ("ferry inspection record", "vessel class M", "Tuesday evening"),
    ("court index bundle", "redaction rule 5", "the filing deadline"),
    ("crop quarantine certificate", "sample set P3", "the port meeting"),
    ("grid restoration schedule", "island simulation R", "the 09:30 switch"),
    ("shelter occupancy roster", "duplicate rule E", "the evening briefing"),
    ("telescope calibration sheet", "mount profile V", "the night shift"),
    ("trial codebook extract", "parser revision 14", "the analysis lock"),
    ("seed-vault inventory", "scanner firmware 8", "the monthly audit"),
    ("aircraft load sheet", "balance table Z", "the dispatch window"),
    ("floodgate maintenance plan", "low-tide cycle G", "Thursday dawn"),
    ("radio licence dossier", "spectrum plan S", "the panel hearing"),
    ("archaeology coordinate map", "sector scan D", "the field meeting"),
    ("fisheries quota table", "fleet register F", "the policy cutoff"),
]


FRAMES = [
    ("future_commitment", "will verify the {thing} against {detail} before {when}", "Is the addressee among those committed by this sentence to perform the verification?"),
    ("obligation_routing", "must sign the {thing} after checking {detail}", "Does this sentence assign the signing obligation to the addressee through the we-group?"),
    ("permission_routing", "may access the {thing} during {when}", "Does this sentence grant the addressee access as a member of the we-group?"),
    ("completed_action", "compared the {thing} with {detail} yesterday", "Does this sentence say the addressee was among those who performed the comparison?"),
    ("current_activity", "are monitoring the {thing} for changes in {detail}", "Does this sentence say the addressee is among those currently monitoring?"),
    ("ownership", "own the rollback path for the {thing} under {detail}", "Does this sentence assign the addressee ownership through membership in the we-group?"),
    ("recommendation", "should review the {thing} before {when}", "Does this sentence direct the addressee, as a group member, to take part in the review?"),
    ("notification_membership", "received the {thing} alert concerning {detail}", "Does this sentence say the addressee was among the alert recipients?"),
]


CALIBRATION = [
    ("Gate North is closed.", "Is Gate North open?", "no"),
    ("Mina may use Desk One.", "Is Mina permitted to use Desk One?", "yes"),
    ("The note names no reviewer.", "Can the reviewer be identified from the note?", "no"),
    ("Every amber valve was checked.", "Were all amber valves checked?", "yes"),
    ("The parcel may arrive Tuesday or Wednesday.", "Is Tuesday confirmed?", "no"),
    ("Ravi opened the first crate but not the second.", "Did Ravi open both crates?", "no"),
    ("At least one coral test passed.", "Did no coral tests pass?", "no"),
    ("Exactly four bronze records remain.", "Do at least three bronze records remain?", "yes"),
    ("The policy is silent about export.", "Does the policy explicitly allow export?", "no"),
    ("No lilac signal failed.", "Did a lilac signal fail?", "no"),
    ("Neri submitted the report before Sol.", "Did Neri submit first?", "yes"),
    ("Either path Cedar or path Elm is open.", "Is at least one of those paths open?", "yes"),
    ("Gate South is open.", "Is Gate South closed?", "no"),
    ("Ari is forbidden from using Desk Two.", "May Ari use Desk Two?", "no"),
    ("The memo names Reviewer Jo.", "Can the reviewer be identified from the memo?", "yes"),
    ("One violet valve was not checked.", "Were all violet valves checked?", "no"),
    ("The train arrives Thursday, not Friday.", "Is Friday the arrival day?", "no"),
    ("Sela opened both the blue and green crates.", "Did Sela open the green crate?", "yes"),
    ("None of the silver tests passed.", "Did at least one silver test pass?", "no"),
    ("Exactly two ochre records remain.", "Do fewer than three ochre records remain?", "yes"),
    ("The rule expressly permits local export.", "Does the rule allow local export?", "yes"),
    ("One maroon signal failed.", "Did a maroon signal fail?", "yes"),
    ("Sol submitted the brief after Neri.", "Did Sol submit first?", "no"),
    ("Neither route Pine nor route Ash is open.", "Is either route open?", "no"),
]


def canonical_hash(value: dict) -> str:
    material = copy.deepcopy(value)
    material.pop("sha256", None)
    return hashlib.sha256(json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def place(options: list[str], answer: str, position: int) -> list[str]:
    result = [value for value in options if value != answer]
    result.insert(position % 3, answer)
    return result


def calibration_rows(offset: int) -> list[dict]:
    rows = []
    for index, (message, question, answer) in enumerate(CALIBRATION[offset:offset + 12]):
        rows.append({
            "id": f"calibration-{offset + index + 1:02d}",
            "message": message,
            "question": question,
            "options": place(TERNARY_OPTIONS, answer, index),
            "answer": answer,
        })
    return rows


def build(condition: str, domains: list[tuple[str, str, str]], calibration_offset: int) -> dict:
    rows = []
    for domain_index, (thing, detail, when) in enumerate(domains):
        for frame_index, (frame, predicate_template, consequence_question) in enumerate(FRAMES):
            predicate = predicate_template.format(thing=thing, detail=detail, when=when)
            context_index = domain_index * len(FRAMES) + frame_index
            context_id = f"{condition}-clusivity-{context_index + 1:03d}"
            bare = f"We {predicate}."
            for form_index, (form, spec) in enumerate(FORMS.items()):
                row_index = context_index * 2 + form_index
                marked = f"{form} {predicate}."
                careful = spec["careful"].format(predicate=predicate)
                if condition == "definition_conditioned":
                    marked = f"{REFERENCE}\nMessage: {marked}"
                    bare_arm = f"{REFERENCE}\nMessage: {bare}"
                    careful = f"{REFERENCE}\nMessage: {careful}"
                else:
                    bare_arm = bare
                rows.append({
                    "id": f"{condition}-{form}-{context_index + 1:03d}",
                    "context_id": context_id,
                    "form": form,
                    "arms": {"ainglish": marked, "bare_english": bare_arm, "careful_english": careful},
                    "questions": [
                        {
                            "id": "addressee_membership",
                            "question": "Is the addressee part of the particular group the sender means by the subject?",
                            "options": place(MEMBERSHIP_OPTIONS, spec["membership"], row_index),
                            "answer": spec["membership"],
                        },
                        {
                            "id": "routed_consequence",
                            "question": consequence_question,
                            "options": place(TERNARY_OPTIONS, spec["consequence"], row_index + 1),
                            "answer": spec["consequence"],
                        },
                        {
                            "id": "outsider_overread",
                            "question": "Does this sentence rule out a person outside the we-group independently having the same duty, permission, action, or status?",
                            "options": place(TERNARY_OPTIONS, "not stated", row_index + 2),
                            "answer": "not stated",
                        },
                    ],
                    "strata": {
                        "condition": condition,
                        "frame": frame,
                        "domain": thing,
                        "form": form,
                        "latent_addressee_membership": spec["membership"],
                    },
                })
    packet = {
        "kind": "dexagon.ainglish.clusivity-recertification-items.v1",
        "proposal_slug": SLUG,
        "condition": condition,
        "reference_card": REFERENCE if condition == "definition_conditioned" else None,
        "contract": {
            "metric": "comprehension_accuracy_delta",
            "primary_unit": "exact joint correctness on membership, routed consequence, and outsider-overread for one isolated arm",
            "scientific_rows": 160,
            "rows_per_form": 80,
            "contexts": 80,
            "arms": ["ainglish", "bare_english", "careful_english"],
            "support": "each form separately: Ainglish joint accuracy minus paired bare >= 0.20, Ainglish minus careful >= -0.05, and Ainglish absolute joint accuracy >= 0.85",
            "additional_falsifiers": [
                "either form's addressee-membership or routed-consequence accuracy is below 0.90",
                "either form's outsider-overread error exceeds 0.05",
                "any frame falls more than 0.10 below careful English",
                "the two forms collapse into the same inclusion answer on more than 0.10 of matched contexts",
            ],
            "reporting": "per condition, form, arm, reader lineage, frame, and question; pooled values are secondary",
        },
        "interpretation": {
            "zero_shot": "current surface transparency to a model not assumed to have Ainglish in training",
            "definition_conditioned": "one-card learnability diagnostic on disjoint inputs; cannot overwrite an adverse zero-shot result and is not evidence of future pretraining",
            "training_caveat": "current tokenization and zero-shot behavior may disadvantage Ainglish because English, unlike Ainglish, was in the readers' training data; future-trained efficiency and comprehension remain prospective claims",
        },
        "reader_gate": {
            "minimum_independent_base_lineages": 2,
            "same_fresh_construct_free_holdout": True,
            "aliases_quantisations_and_finetunes_do_not_add_lineages": True,
            "status_at_freeze": "closed: Qwen failed the fresh v10-general reference-resolution axis; Seed seat pending; no two-lineage panel",
        },
        "scientific_rows": rows,
        "calibration_rows": calibration_rows(calibration_offset),
        "model_calls": 0,
        "governance_writes": 0,
    }
    packet["sha256"] = canonical_hash(packet)
    return packet


def write_frozen(path: Path, value: dict) -> None:
    rendered = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != rendered:
        raise SystemExit(f"REFUSING: frozen carrier drift: {path.name}")
    if not path.exists():
        path.write_text(rendered, encoding="utf-8")


def main() -> None:
    write_frozen(ROOT / "zero-shot.json", build("zero_shot", DOMAINS[:10], 0))
    write_frozen(ROOT / "definition-conditioned.json", build("definition_conditioned", DOMAINS[10:], 12))


if __name__ == "__main__":
    main()
