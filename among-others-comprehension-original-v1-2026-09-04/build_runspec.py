#!/usr/bin/env python3
"""Build the qualified two-reader list-completeness runspec."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
QUAL_ROOT = ROOT.parent / "reader-qualification-local-v1-2026-09-04"
ITEMS_COMMIT = "67a9265441de3394ae2484712ae4b24172819c1a"
ITEMS_SHA256 = "afa281255ee3dc00f2576bbbab05b282bc66bbe9262aa55c21ed1af0e558f42d"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    screens = [load(QUAL_ROOT / name) for name in ("mistral-screen.json", "gemma-screen.json")]
    receipts = [load(QUAL_ROOT / name)["receipt"] for name in ("mistral-qualification.json", "gemma-qualification.json")]
    models = [receipt["roster_id"] for receipt in receipts]
    spec = {
        "kind": "dexagon.ainglish.among-others-qualified-runspec.v1",
        "construct": "among-others / and-no-others — open versus closed enumeration",
        "public_id": "a-kk2fgztm3cmh859j",
        "slug": "among-others-and-no-others-is-the-list-the-whole-list-2",
        "metric": "comprehension_accuracy_delta",
        "seed": 2026090407,
        "planted_arm": "ainglish",
        "calibration_min_gap": 0.5,
        "panel_neff": 2,
        "panel": [screen["reader"] for screen in screens],
        "models": models,
        "reader_qualifications": receipts,
        "comparator": {
            "kind": "complete-careful-english-v1",
            "description": "each compact list-completeness form versus its complete careful-English mapping; bare enumeration is excluded from the scalar",
        },
        "comparison_identity": {
            "comparator_genre": "complete-careful-English-v1",
            "pair_rendering": "held-out exact operational consequence choice",
            "reader_roster": models,
            "form_strata": ["among-others", "and-no-others"],
        },
        "settlement_strata": [
            {"id": "among-others", "weight": 1},
            {"id": "and-no-others", "weight": 1},
        ],
        "items_url": f"https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{ITEMS_COMMIT}/among-others-comprehension-original-v1-2026-09-04/items.json",
        "items_sha256": ITEMS_SHA256,
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "commit": ITEMS_COMMIT,
            "path": "among-others-comprehension-original-v1-2026-09-04/items.json",
        },
        "concurrency": {
            "max_in_flight": 2,
            "per_reader_max_in_flight": {screen["reader"]["name"]: 1 for screen in screens},
        },
        "training_asymmetry": "Present readers have ordinary-English training and are not assumed to have seen Ainglish. This measures current zero-shot transparency, not future post-training efficiency.",
        "attempt": {
            "proposal_revision": "among-others-and-no-others-is-the-list-the-whole-list-2",
            "estimand": "Percentage-point exact-answer accuracy difference, registered compact form minus its complete careful-English mapping, over 240 frozen items balanced 120 among-others and 120 and-no-others; equal-weight mean of the two separately reported form strata. Retain domains, probes, absolute arms, intervals, calibration, yield, and every finite direction.",
            "admissibility_gates": [
                "authenticated suggestions still request this exact original comprehension_accuracy_delta immediately before mint",
                "the proposal remains current at measured stage and the executing principal is not its proposer",
                f"the published answer-bearing array hashes to {ITEMS_SHA256} and contains exactly 240 scientific plus 8 calibration items",
                "every English arm states the complete careful meaning; bare enumeration does not enter the scalar",
                "the two forms remain separately visible and carry equal weight in the primary estimand",
                "both exact local reader configurations retain passing target-independent qualification receipts at mint time",
                "the reader artifacts still match their declared Ollama sha256 digests",
                "construct-free calibration executes first and each reader must show an explicit-minus-unresolved gap of at least 0.5",
                "no reader receives repository access, retrieval, conversation history, or a register definition beyond the presented cell",
                "zero response-bound truncations and full cell yield are required; transport or format failure produces a typed abort without retry",
                "every finite supportive, adverse, null, or inconclusive outcome is filed exactly once",
                "the separate opposing token prerequisite is not changed or hidden by this comprehension result",
            ],
            "planned_sample": {
                "comparison": "registered compact form versus complete careful-English mapping",
                "scientific_items": 240,
                "calibration_items": 8,
                "readers": 2,
                "reader_lineages": [receipt["lineage"]["key"] for receipt in receipts],
                "panel_neff": 2,
                "real_cells": 480,
                "calibration_cells": 32,
                "settlement_strata": {"among-others": 120, "and-no-others": 120},
                "sdk_version": "0.2.52",
                "sdk_commit": "9bb31166b7b99b5d0a399f0b8001c8fceba7f885",
                "items_commit": ITEMS_COMMIT,
                "qualification_commit": "00226c0",
            },
        },
    }
    encoded = json.dumps(spec, indent=2, ensure_ascii=False).encode() + b"\n"
    (ROOT / "runspec.json").write_bytes(encoded)
    print(json.dumps({"output": "runspec.json", "sha256": hashlib.sha256(encoded).hexdigest()}))


if __name__ == "__main__":
    main()
