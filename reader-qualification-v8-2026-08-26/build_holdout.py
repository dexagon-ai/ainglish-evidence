#!/usr/bin/env python3
"""Build a fresh balanced ordinary-English holdout and bind the two eligible readers."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from build_development_plans import canonical, checked


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
LABELS = ("entailed", "contradicted", "not determined")


def cases() -> dict[str, list[tuple[str, str, str]]]:
    return {
        "quantifier_force": [
            ("Exactly eleven of the eighteen quartz records were retained.", "Exactly seven quartz records were not retained.", "entailed"),
            ("At least seven of the twelve violet relays responded.", "Exactly seven violet relays responded.", "not determined"),
            ("At most four of the fifteen copper permits expired.", "Exactly six copper permits expired.", "contradicted"),
            ("Every one of the nine lilac probes completed its check.", "At least one lilac probe failed to complete its check.", "contradicted"),
            ("Some but not all of the fourteen sable channels are active.", "At least one sable channel is active.", "entailed"),
            ("Exactly five of the sixteen ivory submissions were rejected.", "Exactly eleven ivory submissions were not rejected.", "entailed"),
            ("No more than three of the ten ochre steps were skipped.", "Exactly two ochre steps were skipped.", "not determined"),
            ("No umber candidate received fewer than four reviews.", "An umber candidate received exactly three reviews.", "contradicted"),
        ],
        "set_membership": [
            ("Every amber seal is tamper-evident. The east seal is amber.", "The east seal is tamper-evident.", "entailed"),
            ("Every cobalt token is logged. Niko's token is logged.", "Niko's token is cobalt.", "not determined"),
            ("No ceramic key is magnetic. Key R is ceramic.", "Key R is magnetic.", "contradicted"),
            ("Only blue labels expire on Friday. Label K expires on Friday.", "Label K is blue.", "entailed"),
            ("All bronze permits are signed. Permit T is unsigned.", "Permit T is bronze.", "contradicted"),
            ("Some delta badges are active. Daro's badge is a delta badge.", "Daro's badge is active.", "not determined"),
            ("Each archive in group Rowan is encrypted. Archive P is in group Rowan.", "Archive P is encrypted.", "entailed"),
            ("No member of set Saffron is writable. Item V is writable.", "Item V is a member of set Saffron.", "contradicted"),
        ],
        "negation_scope": [
            ("Not every one of the eight coral tests passed.", "At least one coral test did not pass.", "entailed"),
            ("None of the indigo relays failed.", "At least one indigo relay failed.", "contradicted"),
            ("The maroon gate is not unlocked.", "The maroon gate is unlocked.", "contradicted"),
            ("It is not true that no silver beacon responded.", "At least one silver beacon responded.", "entailed"),
            ("Exactly one of the two topaz locks is not engaged.", "Both topaz locks are engaged.", "contradicted"),
            ("No claim was made that the teal archive is complete.", "The teal archive is incomplete.", "not determined"),
            ("Luma did not inspect every vermilion folder.", "Luma inspected no vermilion folders.", "not determined"),
            ("The policy does not prohibit exporting the jade report.", "The policy permits exporting the jade report.", "not determined"),
        ],
        "disjunction": [
            ("The red channel or the blue channel is active, possibly both.", "At least one of the red and blue channels is active.", "entailed"),
            ("Exactly one of route Alder and route Birch was selected.", "Both route Alder and route Birch were selected.", "contradicted"),
            ("Either latch C or latch D is closed, but not both. Latch C is closed.", "Latch D is closed.", "contradicted"),
            ("One or both of mirror E and mirror F is online. Mirror E is online.", "Mirror F is online.", "not determined"),
            ("Both alpha permission and beta permission apply.", "Alpha permission or beta permission applies.", "entailed"),
            ("Neither the east hatch nor the west hatch is open.", "At least one of the east and west hatches is open.", "contradicted"),
            ("At least one of jobs J, K, and L succeeded.", "Job J succeeded.", "not determined"),
            ("One or both of signatures P and Q is present.", "Neither signature P nor signature Q is present.", "contradicted"),
        ],
        "conditional": [
            ("If the orchid checksum matches, the orchid release proceeds. The checksum matches.", "The orchid release proceeds.", "entailed"),
            ("If the navy warning appears, the navy process stops. The process stopped.", "The navy warning appeared.", "not determined"),
            ("If token Z is valid, access Z is granted. Access Z was not granted.", "Token Z is not valid.", "entailed"),
            ("If the plum archive is present, it is indexed. The plum archive is absent.", "The plum archive is not indexed.", "not determined"),
            ("The white indicator is on if and only if circuit W has power. The indicator is on.", "Circuit W has power.", "entailed"),
            ("The black indicator is on if and only if circuit B has power. Circuit B has no power.", "The black indicator is on.", "contradicted"),
            ("If both maple approvals arrive, the maple deployment occurs. Only one approval arrived.", "The maple deployment did not occur.", "not determined"),
            ("The cyan deployment occurs only if the cyan audit passes. The audit failed.", "The cyan deployment occurred.", "contradicted"),
        ],
        "reference_resolution": [
            ("Nora compared the cedar report with the silver report. The former had twelve pages and the latter had nine.", "The cedar report had twelve pages.", "entailed"),
            ("Pavel compared the bronze file with the ivory file. The former had six sections and the latter had ten.", "The ivory file had six sections.", "contradicted"),
            ("Tariq placed the red key inside the box, sealed the box, and left the key itself unsealed.", "Tariq sealed the red key.", "contradicted"),
            ("Uma told Vela that she had been promoted.", "Uma had been promoted.", "not determined"),
            ("Rina and Sol submitted forms. The latter person's form was invalid.", "Sol's form was invalid.", "entailed"),
            ("A module sent a log to a monitor. It was encrypted.", "The log was encrypted.", "not determined"),
            ("Ravi handed Sol a red badge and kept a blue badge. That red badge expired.", "The badge handed to Sol expired.", "entailed"),
            ("Iris spoke to June after the auditor arrived. She left early.", "June left early.", "not determined"),
        ],
        "temporal_order": [
            ("The olive scan finished at 10:00, before the olive export at 12:00.", "The olive scan finished before the olive export.", "entailed"),
            ("The pearl review preceded the pearl vote, and the vote preceded publication.", "The pearl review preceded publication.", "entailed"),
            ("The mauve delivery was required no later than Tuesday. It arrived on Wednesday.", "The mauve delivery met its deadline.", "contradicted"),
            ("The lime migration was not permitted before Thursday. It occurred on Wednesday.", "The lime migration complied with the timing rule.", "contradicted"),
            ("The coral audit occurred sometime on Monday.", "The coral audit occurred before noon on Monday.", "not determined"),
            ("The amber backup completed after the amber index rebuild.", "The amber index rebuild completed after the amber backup.", "contradicted"),
            ("The violet window begins after the backup and before the audit.", "The backup occurs before the audit.", "entailed"),
            ("The indigo report was due by Friday and was delivered on Thursday.", "The indigo report was delivered exactly on Friday.", "contradicted"),
        ],
        "authority_and_permission": [
            ("Only the owner can approve a quartz release. Mira is the owner and approved it.", "Mira was authorized to approve the quartz release.", "entailed"),
            ("A reviewer may recommend a cedar change, but only the owner decides. The reviewer recommended it.", "The reviewer's recommendation was a binding decision.", "contradicted"),
            ("Operator S is permitted to restart the silver service.", "Operator S is allowed to restart the silver service.", "entailed"),
            ("An observer may inspect the bronze record but may not modify it.", "The observer is allowed to modify the bronze record.", "contradicted"),
            ("The delegate can propose an ivory option, while the principal retains the final decision.", "The delegate's chosen ivory option is binding by itself.", "contradicted"),
            ("Either of the two jade administrators may sign the release. Administrator A signed it.", "Administrator A was authorized to sign the jade release.", "entailed"),
            ("Kai is a team member. Only team leads may release the plum package.", "Kai may release the plum package.", "not determined"),
            ("The auditor was asked to advise on the cyan change. Nothing states who may compel a change.", "The auditor may compel the cyan change.", "not determined"),
        ],
    }


def main() -> None:
    rows = []
    answer_positions = [0, 0, 0]
    for axis_index, (axis, axis_cases) in enumerate(cases().items()):
        if len(axis_cases) != 8:
            raise SystemExit("REFUSING: every axis must have eight items")
        for item_index, (premise, hypothesis, answer) in enumerate(axis_cases):
            global_index = axis_index * 8 + item_index
            answer_position = global_index % 3
            others = [label for label in LABELS if label != answer]
            options = others[:]
            options.insert(answer_position, answer)
            answer_positions[answer_position] += 1
            rows.append({
                "id": f"v8-hold-{axis[:2]}-{item_index + 1:02d}",
                "axis": axis,
                "premise": premise,
                "hypothesis": hypothesis,
                "options": options,
                "answer": answer,
            })
    packet = {
        "kind": "ainglish.panel.reader-qualification-holdout.v8",
        "evidentiary_status": "instrument qualification only; never proposal evidence",
        "answer_protocol": "opaque-entailment-choice-v1",
        "task_contract": "Given only the premise, classify the hypothesis as entailed, contradicted, or not determined.",
        "axes": list(cases()),
        "labels": list(LABELS),
        "items_per_axis": 8,
        "answer_positions": answer_positions,
        "model_calls": 0,
        "items": rows,
    }
    packet["content_sha256"] = hashlib.sha256(canonical(packet)).hexdigest()
    holdout_path = ROOT / "holdout.json"
    if holdout_path.exists():
        if checked(holdout_path) != packet:
            raise SystemExit("REFUSING: frozen holdout drift")
    else:
        holdout_path.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    outputs = []
    for short, source_name in (("phi", "development-phi-plan.json"), ("qwen", "development-qwen35-reserve-plan.json")):
        source = checked(ROOT / source_name)
        plan = copy.deepcopy(source)
        plan.pop("content_sha256")
        plan["kind"] = "ainglish.panel.reader-qualification-plan.v8"
        plan["result_kind"] = "ainglish.panel.reader-qualification-result.v8"
        plan["evidentiary_status"] = "instrument qualification only; never proposal evidence"
        plan["phase"] = f"holdout-{short}"
        plan["freeze_rule"] = "Commit and push this fresh holdout, both reader plans, and the static novelty audit before either reader call."
        plan["semantic_stage"]["packet"] = {"file": "reader-qualification-v8-2026-08-26/holdout.json", "content_sha256": packet["content_sha256"]}
        plan["semantic_stage"]["gate"] = {
            "valid_json_cells_required": 64,
            "schema_exact_cells_required": 64,
            "correct_cells_required": 60,
            "correct_per_axis_required": 7,
            "correct_per_label_required": 0,
            "thinking_bytes_required": 0,
            "fault_cells_required": 0,
        }
        plan["semantic_stage"]["pass_meaning"] = "Qualified ordinary-English reader lineage for prospectively frozen scientific Ainglish panels."
        plan["result_file"] = f"holdout-{short}-result.json"
        plan["journal_file"] = f"holdout-{short}-attempt-journal.jsonl"
        plan["content_sha256"] = hashlib.sha256(canonical(plan)).hexdigest()
        target = ROOT / f"holdout-{short}-plan.json"
        if target.exists():
            if checked(target) != plan:
                raise SystemExit(f"REFUSING: frozen plan drift in {target.name}")
        else:
            target.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        outputs.append({"file": target.name, "lineage": plan["candidate"]["lineage"], "content_sha256": plan["content_sha256"]})
    index = {
        "kind": "ainglish.panel.reader-qualification-index.v8",
        "holdout": {"file": holdout_path.name, "content_sha256": packet["content_sha256"]},
        "plans": outputs,
        "selection_rule": {"minimum_qualified_lineages": 2, "correct_cells_required": 60, "correct_per_axis_required": 7, "exact_schema_cells_required": 64, "thinking_bytes_required": 0, "fault_cells_required": 0},
        "no_roster_action": "Publish both results and expose no scientific target carrier if fewer than two lineages qualify.",
        "model_calls": 0,
    }
    index["content_sha256"] = hashlib.sha256(canonical(index)).hexdigest()
    index_path = ROOT / "holdout-index.json"
    if index_path.exists():
        if checked(index_path) != index:
            raise SystemExit("REFUSING: frozen holdout index drift")
    else:
        index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(index, indent=2))


if __name__ == "__main__":
    main()

