#!/usr/bin/env python3
"""Bind the public carrier, qualified readers, and receipt-preserving SDK."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
QUALIFICATION = REPO / "remote-reader-qualification-wave-v2-2026-09-03"
SLUG = "different-from-ref-by-key-different-across-group-by-key"
REPLICATES_HASH = "15bb5a3cc90f945b71752bdae3d93d2702a4cd67af6ea2859948e65d044f33f4"
SDK_VERSION = "0.2.52"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def clean_sha(value: str, label: str) -> str:
    if len(value) != 40 or any(ch not in "0123456789abcdef" for ch in value):
        raise SystemExit(f"{label} must be a full lowercase Git SHA")
    return value


def qualification(name: str) -> tuple[dict, dict]:
    result = json.loads((QUALIFICATION / f"{name}.result.json").read_text(encoding="utf-8"))
    screen = json.loads((QUALIFICATION / f"{name}.screen.json").read_text(encoding="utf-8"))
    receipt = result["receipt"]
    if result["status"] != "passed" or not receipt["result"]["passed"]:
        raise SystemExit(f"REFUSING: qualification {name} did not pass")
    return screen["reader"], receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--items-commit", required=True)
    parser.add_argument("--sdk-commit", required=True)
    args = parser.parse_args()
    items_commit = clean_sha(args.items_commit, "items commit")
    sdk_commit = clean_sha(args.sdk_commit, "SDK commit")

    artifact = json.loads((ROOT / "items.json").read_text(encoding="utf-8"))
    item_digest = artifact["sha256"]
    pairs = [qualification("local-mistral-small32-24b"), qualification("local-gemma3-12b")]
    panel = [pair[0] for pair in pairs]
    receipts = [pair[1] for pair in pairs]
    roster = [receipt["roster_id"] for receipt in receipts]
    spec = {
        "kind": "dexagon.ainglish.different-comprehension-replication-runspec.v1",
        "construct": "different-from(ref, by=key) / different-across(group, by=key)",
        "slug": SLUG,
        "metric": "comprehension_accuracy_delta",
        "replicates_hash": REPLICATES_HASH,
        "seed": 2026090311,
        "planted_arm": "ainglish",
        "calibration_min_gap": 0.5,
        "panel_neff": 1,
        "panel": panel,
        "models": roster,
        "reader_qualifications": receipts,
        "comparator": {
            "kind": "complete-careful-english-v1",
            "description": "Each compact form is compared only with its full registered meaning, including the relation it does not require; bare ambiguous different enters neither arm.",
        },
        "settlement_strata": [
            {"id": "different-from", "weight": 1},
            {"id": "different-across", "weight": 1},
        ],
        "training_asymmetry": "The readers were trained primarily on ordinary English and are not assumed to have seen Ainglish. This is present zero-shot evidence, not a forecast after Ainglish-aware training.",
        "items_url": (
            "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
            f"{items_commit}/different-comprehension-replication-v1-2026-09-03/items.json"
        ),
        "items_sha256": item_digest,
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "commit": items_commit,
            "path": "different-comprehension-replication-v1-2026-09-03/items.json",
        },
        "concurrency": {
            "max_in_flight": 2,
            "per_reader_max_in_flight": {reader["name"]: 1 for reader in panel},
        },
        "attempt": {
            "proposal_revision": SLUG,
            "estimand": (
                "Fresh-input replication of original manifest " + REPLICATES_HASH + ": the "
                "percentage-point exact allocation-compliance accuracy difference, registered "
                "compact form minus complete careful-English mapping, over 160 frozen operational "
                "items (80 different-from and 80 different-across; twenty domains crossed with all "
                "four reference/across truth profiles). The headline is the equal-weight mean of "
                "the two separately reported form strata."
            ),
            "admissibility_gates": [
                f"authenticated suggestions still offer {REPLICATES_HASH} as a confirmation-capable replication immediately before mint",
                "the proposal remains current at measured stage and its claim-carrier work still names this exact target",
                f"the public 168-item carrier at {items_commit} hashes to {item_digest}",
                "all 160 scientific complete pairs were generated fresh for this replication with new scenario identifiers, values and wording; no prior item is reused or paraphrased",
                "the carrier contains exactly 80 rows per form, twenty domains, and forty rows in each crossed truth profile",
                "repetition is explicitly permitted in the different-from careful-English arm and a reference match is explicitly permitted in the different-across careful-English arm",
                "the equal-weight headline cannot hide either form, and both arms must be observable in both settlement strata",
                "Mistral Small 3.2 24B and Gemma 3 12B passed the same public target-independent screen before this carrier was authored",
                "the two attached qualification receipts are unexpired and match every declared reader roster identity",
                f"the receipt-preserving panel harness is public at ai-nglish/ainglish commit {sdk_commit}",
                "eight construct-free planted controls execute first in both arms for each reader and must recover a gap of at least 0.5",
                "zero transport faults, response-bound truncations, or missing scientific cells are required; a failed gate produces a typed abort and no retry",
                "absolute arms, interval, resolution, per-reader values, agreement, every form stratum, and all normalized cells are retained",
                "every finite supportive, null, adverse, floor-bound, ceiling-bound, or inconclusive outcome is filed exactly once",
            ],
            "planned_sample": {
                "metric": "comprehension_accuracy_delta",
                "comparison": "registered compact form versus complete careful-English mapping",
                "scientific_items": 160,
                "calibration_items": 8,
                "forms": {"different-from": 80, "different-across": 80},
                "truth_profiles": {"both": 40, "reference-only": 40, "across-only": 40, "neither": 40},
                "domains": 20,
                "readers": 2,
                "reader_families": ["Mistral Small 3.2 24B", "Gemma 3 12B"],
                "panel_members": 2,
                "panel_neff": 1,
                "real_cells": 320,
                "calibration_cells": 32,
                "sdk_version": SDK_VERSION,
                "sdk_commit": sdk_commit,
                "items_commit": items_commit,
                "replicates_hash": REPLICATES_HASH,
            },
        },
    }
    encoded = json.dumps(spec, indent=2, ensure_ascii=False).encode() + b"\n"
    (ROOT / "runspec.json").write_bytes(encoded)
    index = {
        "kind": "ainglish.different-comprehension-replication-index.v1",
        "items_commit": items_commit,
        "sdk_commit": sdk_commit,
        "sdk_version": SDK_VERSION,
        "campaigns": {
            "different-comprehension-replication": {
                "runspec": "runspec.json",
                "runspec_sha256": hashlib.sha256(encoded).hexdigest(),
                "receipt_stem": "different-comprehension-replication",
            }
        },
    }
    index["content_sha256"] = hashlib.sha256(canonical(index)).hexdigest()
    (ROOT / "runspec-index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(index, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
