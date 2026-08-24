#!/usr/bin/env python3
"""Freeze the untouched v4 qualification holdout without model calls."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OPTIONS = ["yes", "no", "cannot tell"]

ROWS = {
    "quantifier_force": [
        ("At most four of the nine relays activated.", "Did five relays activate?", "no"),
        ("One or more of the archived copies is readable.", "Must exactly one copy be readable?", "cannot tell"),
        ("Every issued badge was logged at reception.", "Was any issued badge left unlogged?", "no"),
        ("Exactly seven of the ten samples were verified.", "Were three samples left unverified?", "yes"),
        ("Fewer than all of the scheduled checks completed.", "Did at least one scheduled check fail to complete?", "yes"),
        ("All eight of the eight records were archived.", "Were all the records archived?", "yes"),
    ],
    "set_membership": [
        ("Tari, the reader of this message, and Mo are assigned to inspect the vault.", "Is the reader assigned to inspect the vault?", "yes"),
        ("The signing group consists only of Inez and Pavel.", "Is Rami in the signing group?", "no"),
        ("Anyone holding a blue badge may enter. The reader holds a blue badge.", "May the reader enter?", "yes"),
        ("Only red-team members may approve. The reader approved the change.", "Is the reader a red-team member?", "yes"),
        ("The note names Ana and Bo as reviewers and says nothing about the reader.", "Is the reader a reviewer?", "cannot tell"),
        ("The permitted regions are west and central, with no others permitted.", "Is east a permitted region?", "no"),
    ],
    "negation_scope": [
        ("The monitor did not report every fault.", "Was at least one fault unreported?", "yes"),
        ("No signed package failed verification.", "Did any signed package fail verification?", "no"),
        ("It is not true that both alarms fired.", "Did both alarms fire?", "no"),
        ("The policy does not forbid exporting logs.", "Does that sentence itself grant permission to export logs?", "no"),
        ("Not one of the three keys opened the cabinet.", "Did any of the three keys open the cabinet?", "no"),
        ("The archive is not inaccessible.", "Is the archive inaccessible?", "no"),
    ],
    "disjunction": [
        ("Select either alpha or beta, but not both.", "May both alpha and beta be selected?", "no"),
        ("The alert may use email, SMS, or both.", "May both channels be used?", "yes"),
        ("At least one of the red or gold flags must be present, and there is no upper limit.", "May both flags be present?", "yes"),
        ("Exactly one of the east or west tunnels will open.", "Will both tunnels open?", "no"),
        ("The backup may be stored in Paris or Berlin, and using both is expressly allowed.", "May the backup be stored in both cities?", "yes"),
        ("The key must be RSA or Ed25519; the note gives no exclusivity rule.", "Does the note establish that using both is forbidden?", "no"),
    ],
    "conditional": [
        ("If the seal is broken, quarantine the case. The seal is broken.", "Should the case be quarantined?", "yes"),
        ("If the scan succeeds, publish the index. The index was published.", "Must the scan have succeeded?", "cannot tell"),
        ("Do not pay the invoice unless it is signed. The invoice is unsigned.", "Should the invoice be paid?", "no"),
        ("A client may connect only if its token is fresh. This token is stale.", "May this client connect?", "no"),
        ("Run the test only when both permits are present. Only one permit is present.", "Should the test run?", "no"),
        ("If an outage or a drill is active, page the coordinator. A drill is active.", "Should the coordinator be paged?", "yes"),
    ],
    "reference_resolution": [
        ("Lea handed Omar the sealed folder. Omar placed it in the safe.", "What did Omar place in the safe?", "the sealed folder"),
        ("Nadia told Priya that she would lead the review.", "Who will lead the review?", "cannot tell"),
        ("The router sent the switch its configuration because the router had restarted.", "What had restarted?", "the router"),
        ("I attached the map to the report. The latter needs a signature.", "What needs a signature?", "the report"),
        ("The red crate sits beside the blue crate. This message says the blue crate is empty.", "Which crate is stated to be empty?", "the blue crate"),
        ("Mina emailed Jo after Mina completed the audit.", "Who completed the audit?", "Mina"),
    ],
}


def choices(answer: str, position: int) -> list[str]:
    pool = list(OPTIONS) if answer in OPTIONS else [answer, "the other named object", "cannot tell"]
    others = [value for value in pool if value != answer]
    out = list(others)
    out.insert(position, answer)
    return out


def main() -> None:
    tuned = json.loads((ROOT / "development-tuned-result.json").read_text())
    items = []
    for axis, rows in ROWS.items():
        for index, (message, question, answer) in enumerate(rows):
            position = index % 3
            items.append({
                "id": f"v4-hold-{axis}-{index + 1:02d}",
                "axis": axis,
                "message": message,
                "question": question,
                "options": choices(answer, position),
                "answer": answer,
            })
    spec = {
        "kind": "ainglish.panel.reader-qualification-holdout.v4",
        "result_kind": "ainglish.panel.reader-qualification-holdout-result.v4",
        "purpose": "Qualify the development-selected Qwen 3.5 9B no-thinking edition once on untouched ordinary-English controls.",
        "evidentiary_status": "instrument qualification only; never proposal evidence",
        "answer_protocol": "opaque-choice-v1",
        "transport": {"adapter": "ollama-native-chat-v1", "think": False},
        "development_result_path": str(ROOT / "development-tuned-result.json"),
        "development_result_sha256": "b6f2b1106b60fe783054c53796426c29d01f77a0f20f36d7ddeceb63e804547d",
        "prior_qualified_reader": {
            "name": "gemma3-12b-literal-q4_k_m",
            "lineage": "Gemma 3 12B",
            "qualification": "reader-qualification-v2-2026-08-24/holdout-result.json",
            "observed": "47/48 exact and correct; at least 7/8 on every axis"
        },
        "combined_roster_rule": "holdout must qualify Qwen 3.5 9B; scientific roster then combines it with the frozen v2-qualified Gemma 3 edition",
        "axes": list(ROWS),
        "items_per_axis": 6,
        "forbidden_construct_terms": [
            "some-or-all", "some-but-not-all", "we-including-you", "we-excluding-you",
            "proposal-by", "decision-by", "or-both", "not-both", "fact-not-known",
            "choice-not-made", "ainglish"
        ],
        "disjoint_from_specs": [
            "/home/dexagon/codex/dexagon/ainglish-evidence/reader-qualification-tournament-2026-08-23/spec.json",
            "/home/dexagon/codex/dexagon/ainglish-evidence/reader-qualification-v2-2026-08-24/development.json",
            "/home/dexagon/codex/dexagon/ainglish-evidence/reader-qualification-v2-2026-08-24/holdout.json",
            "/home/dexagon/codex/dexagon/ainglish-evidence/reader-qualification-v3-2026-08-24/development.json",
            "/home/dexagon/codex/dexagon/ainglish-evidence/reader-qualification-v3-2026-08-24/holdout.json"
        ],
        "gpu_gate": {
            "ollama_base_url": "http://127.0.0.1:11434",
            "ollama_ps": "http://127.0.0.1:11434/api/ps",
            "minimum_total_free_mib": 36000,
            "maximum_utilization_percent": 30
        },
        "selection_rule": {
            "exact_code_cells_required": 36,
            "correct_cells_required": 34,
            "correct_per_axis_required": 5,
            "minimum_distinct_qualified_lineages": 1,
            "roster": "exactly the tuned-development-qualified Qwen 3.5 9B edition",
            "no_roster_action": "If it fails, publish the result and do not mint a scientific comprehension attempt."
        },
        "panel": tuned["fixed_roster"],
        "items": items,
    }
    out = ROOT / "holdout.json"
    out.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"output": str(out), "items": len(items), "reader_calls": 0}, indent=2))


if __name__ == "__main__":
    main()
