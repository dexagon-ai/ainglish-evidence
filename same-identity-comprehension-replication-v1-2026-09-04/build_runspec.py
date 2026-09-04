#!/usr/bin/env python3
"""Build the frozen two-reader replication specification."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
QUAL_ROOT = ROOT.parent / "reader-qualification-local-v1-2026-09-04"
ITEMS_COMMIT = "91dab58bed8e5ced2674b27d23a1d82faedbff66"
ITEMS_SHA256 = "bf4a734db3a4074a10f0ad732ffb7e3a4af9b60aa482dfb1b6dccbf5b91d6b34"
TARGET = "bacb9d4ab57a95aae9fb6d9d4764ef930a3dabaac94f5c9fbf0f5e9f4a1c3621"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    screens = [load(QUAL_ROOT / name) for name in ("mistral-screen.json", "gemma-screen.json")]
    receipts = [
        load(QUAL_ROOT / name)["receipt"]
        for name in ("mistral-qualification.json", "gemma-qualification.json")
    ]
    models = [receipt["roster_id"] for receipt in receipts]
    spec = {
        "kind": "dexagon.ainglish.same-identity-qualified-replication-runspec.v1",
        "construct": "same-one / same-kind / same-name — numerical identity vs verified equality vs name only",
        "public_id": "a-ptwhg57dq4w4fas4",
        "slug": "same-one-same-kind-same-name",
        "metric": "comprehension_accuracy_delta",
        "replicates_hash": TARGET,
        "seed": 2026090411,
        "planted_arm": "ainglish",
        "calibration_min_gap": 0.5,
        "panel_neff": 2,
        "panel": [screen["reader"] for screen in screens],
        "models": models,
        "reader_qualifications": receipts,
        "comparator": {
            "kind": "complete-careful-english-v1",
            "description": "Each marked identity form versus a complete careful-English statement of the same operational consequence.",
        },
        "comparison_identity": {
            "comparator_genre": "complete-careful-English-v1",
            "pair_rendering": "fresh held-out binary operational-consequence choice",
            "reader_roster": models,
            "form_balance": {"same-one": 16, "same-kind": 16, "same-name": 16},
            "target_estimand": "aggregate marked-minus-careful exact-answer accuracy",
        },
        "items_url": f"https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{ITEMS_COMMIT}/same-identity-comprehension-replication-v1-2026-09-04/items.json",
        "items_sha256": ITEMS_SHA256,
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "commit": ITEMS_COMMIT,
            "path": "same-identity-comprehension-replication-v1-2026-09-04/items.json",
        },
        "concurrency": {
            "max_in_flight": 2,
            "per_reader_max_in_flight": {screen["reader"]["name"]: 1 for screen in screens},
        },
        "training_asymmetry": "Present readers have ordinary-English training and are not assumed to have seen Ainglish. This measures current zero-shot transparency, not future performance after Ainglish corpus or tokenizer exposure.",
        "attempt": {
            "proposal_revision": "same-one-same-kind-same-name",
            "estimand": "Percentage-point exact-answer accuracy difference, registered marked form minus its complete careful-English mapping, over 48 wholly fresh items balanced 16 same-one, 16 same-kind and 16 same-name; aggregate exact accuracy, matching the target original's aggregate estimand. Retain absolute arms, interval, calibration, yield and every finite direction.",
            "admissibility_gates": [
                f"fresh proposal state still requests an independent comprehension_accuracy_delta replication of {TARGET} immediately before mint",
                "fresh personalised suggestions are consulted; omission from the rotating top-20 list does not override the proposal's explicit current work item",
                "the proposal remains current at measured stage and the executing principal is neither proposer nor target measurer",
                f"the published answer-bearing array hashes to {ITEMS_SHA256} and contains exactly 48 scientific plus 8 target-independent calibration items",
                "all 48 complete English/Ainglish pairs are absent from every prior measurement manifest on this proposal",
                "the three forms contribute 16 items each; every same-kind carrier names both its equality check and observation time",
                "the primary scalar preserves the target original's aggregate marked-minus-complete-careful-English estimand; no new settlement stratum is introduced",
                "both exact local reader configurations retain passing target-independent qualification receipts at mint time",
                "the reader artifacts still match their declared Ollama sha256 digests",
                "construct-free calibration executes first and each reader must show an explicit-minus-unresolved gap of at least 0.5",
                "no reader receives repository access, retrieval, conversation history or a register definition beyond the presented cell",
                "zero response-bound truncations and full cell yield are required; transport or format failure produces a typed abort without retry",
                "every finite supportive, adverse, null or inconclusive outcome is filed exactly once",
                "the already confirmed token prerequisite is not changed or hidden by this comprehension result",
            ],
            "planned_sample": {
                "comparison": "registered marked form versus complete careful-English mapping",
                "scientific_items": 48,
                "calibration_items": 8,
                "forms": {"same-one": 16, "same-kind": 16, "same-name": 16},
                "readers": 2,
                "reader_lineages": [receipt["lineage"]["key"] for receipt in receipts],
                "panel_neff": 2,
                "real_cells": 96,
                "calibration_cells": 32,
                "sdk_version": "0.2.53",
                "items_commit": ITEMS_COMMIT,
                "qualification_commit": "00226c070cff75587a31ab2bd7da5d77660798ba",
            },
        },
    }
    encoded = json.dumps(spec, indent=2, ensure_ascii=False).encode() + b"\n"
    (ROOT / "runspec.json").write_bytes(encoded)
    print(json.dumps({"output": "runspec.json", "sha256": hashlib.sha256(encoded).hexdigest()}))


if __name__ == "__main__":
    main()
