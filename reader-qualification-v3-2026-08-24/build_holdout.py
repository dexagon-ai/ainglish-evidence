#!/usr/bin/env python3
"""Freeze the untouched v3 holdout after development selection is final."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "holdout.json"
AXES = [
    "quantifier_force", "set_membership", "negation_scope",
    "disjunction", "conditional", "reference_resolution",
]


RAW = [
    ("quantifier_force", "At least two of the six samples were retained.", "Must exactly two samples have been retained?", "no", ["yes", "cannot tell"]),
    ("quantifier_force", "No courier delivered a parcel before dawn.", "Did any courier deliver a parcel before dawn?", "no", ["yes", "cannot tell"]),
    ("quantifier_force", "All but one of the nine monitors responded.", "Did exactly eight monitors respond?", "yes", ["no", "cannot tell"]),
    ("quantifier_force", "Fewer than four alerts remain open.", "Could exactly three alerts remain open?", "yes", ["no", "cannot tell"]),
    ("quantifier_force", "Some, but not all, of the delegates signed.", "Did every delegate sign?", "no", ["yes", "cannot tell"]),
    ("quantifier_force", "Each of the three backups completed successfully.", "Did all three backups complete successfully?", "yes", ["no", "cannot tell"]),
    ("set_membership", "Jules, the reader, and Mei form the audit group.", "Is the reader in the audit group?", "yes", ["no", "cannot tell"]),
    ("set_membership", "The reviewers are Inez and Bo. You received a copy for information only.", "Is the reader one of the reviewers?", "no", ["yes", "cannot tell"]),
    ("set_membership", "Whoever holds the brass token must open the cabinet. The token holder is not identified.", "Must the reader open the cabinet?", "cannot tell", ["yes", "no"]),
    ("set_membership", "Everyone physically in the room must sign. You joined remotely and were not in the room.", "Must the reader sign under this rule?", "no", ["yes", "cannot tell"]),
    ("set_membership", "The response team consists only of Ana, you, and Chen.", "Is the reader on the response team?", "yes", ["no", "cannot tell"]),
    ("set_membership", "Contractors may enter the lab. You are an employee, not a contractor.", "Does this sentence grant the reader entry?", "no", ["yes", "cannot tell"]),
    ("negation_scope", "The two requests were not both approved.", "Were both requests approved?", "no", ["yes", "cannot tell"]),
    ("negation_scope", "Neither checksum failed validation.", "Did the first checksum fail validation?", "no", ["yes", "cannot tell"]),
    ("negation_scope", "Using the fallback is not prohibited by this notice.", "Does this notice prohibit using the fallback?", "no", ["yes", "cannot tell"]),
    ("negation_scope", "It is not true that none of the sensors recovered.", "Did at least one sensor recover?", "yes", ["no", "cannot tell"]),
    ("negation_scope", "Except for file C, do not delete any file.", "Is file C covered by the deletion prohibition?", "no", ["yes", "cannot tell"]),
    ("negation_scope", "The batch contains not fewer than three records.", "Does the batch contain at least three records?", "yes", ["no", "cannot tell"]),
    ("disjunction", "Notify the owner or the operator, and you may notify both.", "Would notifying both comply?", "yes", ["no", "cannot tell"]),
    ("disjunction", "Use either the paper form or the web form, exclusively.", "Would using both forms comply?", "no", ["yes", "cannot tell"]),
    ("disjunction", "Submit the receipt, the invoice, or both.", "Must at least one document be submitted?", "yes", ["no", "cannot tell"]),
    ("disjunction", "Select one or more available mirrors.", "Must exactly one mirror be selected?", "no", ["yes", "cannot tell"]),
    ("disjunction", "Choose either route X or route Y. If you choose X, do not choose Y.", "May both routes be chosen?", "no", ["yes", "cannot tell"]),
    ("disjunction", "Use the north route or the south route. The message gives no exclusivity rule.", "May both routes be used?", "cannot tell", ["yes", "no"]),
    ("conditional", "If the battery is low, shut the unit down. The battery is low.", "Must the unit be shut down?", "yes", ["no", "cannot tell"]),
    ("conditional", "Publish the notice only if Mina has signed it. Mina has not signed it.", "May the notice be published?", "no", ["yes", "cannot tell"]),
    ("conditional", "Unless the chair vetoes the motion, archive it. The message does not state whether there was a veto.", "Must the motion be archived?", "cannot tell", ["yes", "no"]),
    ("conditional", "The gate opens only if the badge is valid. The gate opened.", "Was the badge valid?", "yes", ["no", "cannot tell"]),
    ("conditional", "If the cache is stale, refresh it. The cache is not stale.", "Does this rule tell us whether a refresh happened?", "no", ["yes", "cannot tell"]),
    ("conditional", "Provided the receipt is verified, issue the refund. The receipt is verified.", "Should the refund be issued?", "yes", ["no", "cannot tell"]),
    ("reference_resolution", "Tariq handed the folder to Uma. Uma locked the folder away.", "Who locked the folder away?", "Uma", ["Tariq", "cannot tell"]),
    ("reference_resolution", "The cedar crate and the steel crate arrived. The former was damaged.", "Which crate was damaged?", "the cedar crate", ["the steel crate", "cannot tell"]),
    ("reference_resolution", "Lea told Marta that her account was suspended.", "Whose account was suspended?", "cannot tell", ["Lea's", "Marta's"]),
    ("reference_resolution", "Ravi gave Omar his spare key.", "Whose spare key was it?", "cannot tell", ["Ravi's", "Omar's"]),
    ("reference_resolution", "The box was placed beside the crate, and it was sealed.", "Which object was sealed?", "cannot tell", ["the box", "the crate"]),
    ("reference_resolution", "First inspect the intake valve; second inspect the outlet valve. The second one leaked.", "Which valve leaked?", "the outlet valve", ["the intake valve", "cannot tell"]),
]


def items() -> list[dict]:
    out = []
    for index, (axis, message, question, answer, distractors) in enumerate(RAW):
        options = list(distractors)
        options.insert(index % 3, answer)
        out.append({
            "id": f"v3-hold-{axis}-{index + 1:02d}", "axis": axis,
            "message": message, "question": question, "options": options, "answer": answer,
        })
    return out


def main() -> None:
    if OUT.exists():
        raise SystemExit("REFUSING: holdout.json already exists")
    rows = items()
    positions = [row["options"].index(row["answer"]) for row in rows]
    if {position: positions.count(position) for position in range(3)} != {0: 12, 1: 12, 2: 12}:
        raise SystemExit("REFUSING: answer positions are not balanced")
    spec = {
        "kind": "ainglish.panel.reader-qualification-holdout.v3",
        "result_kind": "ainglish.panel.reader-qualification-holdout-result.v3",
        "purpose": "Qualify the development-selected additional Qwen lineage once on untouched ordinary-English controls.",
        "evidentiary_status": "instrument qualification only; never proposal evidence",
        "sdk_version": "0.2.34",
        "sdk_commit": "aac3ea50d48d76ce41b96c9f762d5c05dc53b4b5",
        "sdk_panel_path": "/home/dexagon/codex/dexagon/worktrees/sdk-attempt-manifest-v2-20260823/src/ainglish/panel.py",
        "answer_protocol": "opaque-choice-v1",
        "development_result_path": "/home/dexagon/codex/dexagon/ainglish-evidence/reader-qualification-v3-2026-08-24/development-tuned-result.json",
        "development_result_sha256": "576d99a1a4296b9ae905b7016d19b891e0f7f01ac9b9148722b9c9f205f8ea10",
        "prior_qualified_reader": {
            "name": "gemma3-12b-literal-q4_k_m", "lineage": "Gemma 3 12B",
            "qualification": "reader-qualification-v2-2026-08-24/holdout-result.json",
            "observed": "47/48 exact and correct; at least 7/8 on every axis",
        },
        "combined_roster_rule": "holdout must qualify Qwen 3.8; scientific roster then combines it with the frozen v2-qualified Gemma 3 edition",
        "axes": AXES, "items_per_axis": 6,
        "forbidden_construct_terms": [
            "some-or-all", "some-but-not-all", "we-including-you", "we-excluding-you",
            "proposal-by", "decision-by", "or-both", "not-both", "fact-not-known",
            "choice-not-made", "ainglish",
        ],
        "disjoint_from_specs": [
            "/home/dexagon/codex/dexagon/ainglish-evidence/reader-qualification-tournament-2026-08-23/spec.json",
            "/home/dexagon/codex/dexagon/ainglish-evidence/reader-qualification-v2-2026-08-24/development.json",
            "/home/dexagon/codex/dexagon/ainglish-evidence/reader-qualification-v2-2026-08-24/holdout.json",
            "/home/dexagon/codex/dexagon/ainglish-evidence/reader-qualification-v3-2026-08-24/development.json",
        ],
        "gpu_gate": {
            "ollama_base_url": "http://127.0.0.1:11434", "ollama_ps": "http://127.0.0.1:11434/api/ps",
            "minimum_total_free_mib": 36000, "maximum_utilization_percent": 30,
        },
        "selection_rule": {
            "exact_code_cells_required": 36, "correct_cells_required": 34,
            "correct_per_axis_required": 5, "minimum_distinct_qualified_lineages": 1,
            "roster": "all qualified development-selected editions; here exactly Qwen 3.8",
            "no_roster_action": "If Qwen 3.8 fails, publish the result and do not mint a scientific comprehension attempt.",
        },
        "panel": [
            {
                "name": "qwen3.8-27b-screen-bound1024-q4_k_m", "lineage": "Qwen 3.8 27B", "provider": "ollama",
                "model": "dexagon-qwen3.8-27b-screen:ctx4k",
                "model_digest": "sha256:97a12d32a43050d86486d7d3a4253036603e5209ae717da488f95b46c704df47",
                "precision": "q4_k_m", "max_tokens": 1024, "timeout_s": 120,
                "temperature": 0, "seed": 2026082403, "api": "openai", "base_url": "http://127.0.0.1:11434/v1",
            },
        ],
        "items": rows,
    }
    OUT.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"path": str(OUT), "items": len(rows), "answer_positions": {str(i): positions.count(i) for i in range(3)}}))


if __name__ == "__main__":
    main()
