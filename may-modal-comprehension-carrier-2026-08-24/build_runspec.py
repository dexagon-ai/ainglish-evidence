#!/usr/bin/env python3
"""Build the exact panel manifest after an independent qualified carrier is supplied."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parent
SLUG = "may-as-permission-may-as-possibility-does-may-authorize-an-a"
SEED = 2026082442


def canonical_sha(value: object) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode()).hexdigest()


def load_document(name: str) -> dict:
    value = json.loads((ROOT / name).read_text(encoding="utf-8"))
    if canonical_sha(value["items"]) != value["sha256"]:
        raise SystemExit(f"REFUSING: {name} item digest drift")
    return value


def load_carrier() -> dict:
    path = ROOT / "carrier-block.json"
    if not path.exists():
        raise SystemExit(
            "REFUSING: carrier-block.json is absent. Dexagon's local v2 reader holdout qualified "
            "only one lineage; do not weaken or retune that burned gate. An independent carrier "
            "must publish a fresh construct-blind qualification receipt for at least two lineages."
        )
    value = json.loads(path.read_text(encoding="utf-8"))
    panel = value.get("panel")
    qualification = value.get("qualification")
    if not isinstance(panel, list) or len(panel) < 2:
        raise SystemExit("REFUSING: independent carrier needs at least two reader entries")
    if len({row.get("lineage") for row in panel}) < 2:
        raise SystemExit("REFUSING: independent carrier reader lineages are not distinct")
    if not isinstance(qualification, dict) or qualification.get("roster_ready") is not True:
        raise SystemExit("REFUSING: carrier qualification does not attest roster_ready=true")
    required = ("development_sha256", "holdout_sha256", "result_sha256", "answer_protocol")
    if any(not qualification.get(key) for key in required):
        raise SystemExit("REFUSING: carrier qualification receipt is incomplete")
    if qualification["answer_protocol"] != "opaque-choice-v1":
        raise SystemExit("REFUSING: carrier did not qualify with opaque-choice-v1")
    return value


def source_commit() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT.parent, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    ).stdout.strip()


def build() -> dict:
    claim = load_document("claim-items.json")
    bare = load_document("bare-items.json")
    allowed = load_document("allowed-to-items.json")
    gate = json.loads((ROOT / "admissibility-gate.json").read_text(encoding="utf-8"))
    if canonical_sha(gate["items"]) != gate["sha256"] or gate.get("retained") != 120:
        raise SystemExit("REFUSING: admissibility gate drift or fewer than 120 retained items")
    carrier = load_carrier()
    panel = [{**entry, "seed": SEED} for entry in carrier["panel"]]
    commit = source_commit()
    return {
        "construct": "may-as-permission / may-as-possibility",
        "slug": SLUG,
        "metric": "comprehension_accuracy_delta",
        "formula_version": 2,
        "seed": SEED,
        "planted_arm": "ainglish",
        "calibration_min_gap": 0.5,
        "panel_neff": carrier.get("panel_neff", 1),
        "panel": panel,
        "items": claim["items"],
        "items_sha256": claim["sha256"],
        "items_url": (
            "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
            f"{commit}/may-modal-comprehension-carrier-2026-08-24/claim-items.json"
        ),
        "comparator": {
            "kind": "complete-careful-english-v1",
            "description": (
                "Permission rows use is permitted to; epistemic-possibility rows use might. "
                "Both are the proposal's declared shortest adequate controls."
            ),
        },
        "diagnostics_frozen_but_not_filed_in_claim_scalar": {
            "bare_may": {"items_sha256": bare["sha256"], "real_items": 120},
            "allowed_to": {"items_sha256": allowed["sha256"], "real_items": 60},
        },
        "admissibility_gate": {"sha256": gate["sha256"], "retained": 120, "rejected": 0},
        "carrier_qualification": carrier["qualification"],
        "scoring": (
            "Pooled marked-minus-careful-English exact consequence accuracy, reported with both "
            "absolute arms, and separately by force, reader, question kind, voice, cross-cell, "
            "domain, and severity from the exact cell receipt. Permission and possibility must "
            "each be non-inferior within 5pp; pooling cannot rescue either force."
        ),
        "scope_limit": (
            "This panel tests routing to authority versus contemporaneous-evidence consequences. "
            "It does not establish technical capability, eventual occurrence, or extra practical "
            "value over allowed-to until the separately frozen diagnostic is carried."
        ),
        "attempt": {
            "proposal_revision": SLUG,
            "estimand": (
                "The percentage-point difference in exact held-out consequence accuracy, marked "
                "may-as-* minus the shortest adequate careful-English control, over 120 unique "
                "operational messages balanced 60 permission and 60 epistemic-possibility rows. "
                "Report the two forces separately; the pooled scalar is descriptive if their "
                "non-inferiority conclusions differ."
            ),
            "admissibility_gates": [
                f"the claim item array hashes to {claim['sha256']} and contains exactly 120 real plus 16 construct-free calibration rows",
                f"the construct-blind admissibility ledger hashes to {gate['sha256']} and retains all 120 unique affirmative bare-may messages",
                "permission and possibility each contribute 60 rows; active/passive voice and high/low severity each contribute 60; ten domains contribute 12 rows each",
                "each of four consequence-question kinds contributes 30 rows and each answer position occurs 30 times; neither questions nor choices contain either marker",
                "authority, objective capability/outcome, and speaker-evidence state are frozen as separate item fields; objective state is balanced within each force",
                "the load-bearing permitted-but-impossible cell contributes 30 rows and forbidden-but-possible contributes 15 rows; no capability fact keys an epistemic answer",
                "an independent carrier receipt qualifies at least two distinct model lineages on untouched construct-blind controls under opaque-choice-v1 before mint",
                "the construct-free calibration executes before scientific cells for every reader and must show an explicit-minus-unresolved gap of at least 0.5",
                "the token prerequisite must be confirmed by a strict settlement majority and its scope mismatch against the 120 comprehension items must be resolved on-thread before reader spend",
                "every finite supportive, null, adverse, and force-divergent outcome is filed; only frozen-input, qualification, calibration, transport, yield, manifest, or declared resource failures may abort",
            ],
            "planned_sample": {
                "metric": "comprehension_accuracy_delta",
                "real_items": 120,
                "calibration_items": 16,
                "forces": {"permission": 60, "possibility": 60},
                "real_reader_cells": 120 * len(panel),
                "calibration_reader_cells": 32 * len(panel),
                "readers": [entry["name"] for entry in panel],
                "reader_lineages": [entry["lineage"] for entry in panel],
                "panel_neff": carrier.get("panel_neff", 1),
                "noninferiority_margin_pp": -5,
                "marked_minus_bare_prediction_pp": 20,
                "max_false_cross_inference": 0.05,
                "frozen_inputs": {
                    "claim": {
                        "url": (
                            "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
                            f"{commit}/may-modal-comprehension-carrier-2026-08-24/claim-items.json"
                        ),
                        "sha256": claim["sha256"],
                    },
                    "bare_may_diagnostic": {
                        "url": (
                            "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
                            f"{commit}/may-modal-comprehension-carrier-2026-08-24/bare-items.json"
                        ),
                        "sha256": bare["sha256"],
                    },
                    "allowed_to_diagnostic": {
                        "url": (
                            "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
                            f"{commit}/may-modal-comprehension-carrier-2026-08-24/allowed-to-items.json"
                        ),
                        "sha256": allowed["sha256"],
                    },
                    "admissibility_gate": {
                        "url": (
                            "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
                            f"{commit}/may-modal-comprehension-carrier-2026-08-24/admissibility-gate.json"
                        ),
                        "sha256": gate["sha256"],
                    },
                },
                "seed": SEED,
            },
        },
    }


def main() -> None:
    spec = build()
    (ROOT / "runspec.json").write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(ROOT / "runspec.json")


if __name__ == "__main__":
    main()
