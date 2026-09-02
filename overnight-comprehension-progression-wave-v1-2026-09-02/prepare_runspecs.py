#!/usr/bin/env python3
"""Bind the published overnight carriers to exact readers and attempt contracts."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_COMMIT = "cd20c022bda8bdde2d047d4afa119a78d925714a"
SDK_VERSION = "0.2.50"
READERS = [
    {
        "name": "mistral-small3.2-24b-opaque-choice-q4_k_m",
        "provider": "ollama",
        "model": "dexagon-mistral-small3.2-24b-pp-task:ctx4k",
        "model_digest": "sha256:6629ee92de51c9a1367e1331cfa9ef6a77058a44a6a3e18ab524b2d0404252de",
        "precision": "q4_k_m",
        "api": "openai",
        "base_url": "http://127.0.0.1:11434/v1",
        "max_tokens": 32,
        "timeout_s": 120,
        "temperature": 0,
    },
    {
        "name": "gemma3-12b-opaque-choice-q4_k_m",
        "provider": "ollama",
        "model": "dexagon-gemma3-12b-pp-task:ctx4k",
        "model_digest": "sha256:de1f65ea3438dfcc7c3387802b9425a140fb01ecc79edf4924a13fab051eb68f",
        "precision": "q4_k_m",
        "api": "openai",
        "base_url": "http://127.0.0.1:11434/v1",
        "max_tokens": 32,
        "timeout_s": 120,
        "temperature": 0,
    },
]


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def main() -> None:
    index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    interpretations = {
        "acknowledgement-type": (
            "Careful-English strata estimate non-inferiority at -5 percentage points; balanced bare-acknowledged "
            "strata estimate recovery of the otherwise hidden receipt/agreement bit."
        ),
        "why-relation": (
            "Careful-English strata estimate non-inferiority at -5 percentage points; balanced bare-why strata "
            "estimate recovery of the otherwise hidden causal-versus-normative relation."
        ),
        "typed-missing-value": (
            "All four strata compare the compact semantic meta-value with its complete careful-English mapping; "
            "primary interpretation is non-inferiority at -5 percentage points with each form visible."
        ),
    }
    runspecs = {}
    for offset, (name, meta) in enumerate(index["campaigns"].items(), start=1):
        seed = 2026090208 + offset
        readers = [{**reader, "seed": seed} for reader in READERS]
        strata = meta["settlement_strata"]
        spec = {
            "kind": "dexagon.ainglish.overnight-comprehension-runspec.v1",
            "construct": meta["construct"],
            "slug": meta["slug"],
            "metric": "comprehension_accuracy_delta",
            "seed": seed,
            "planted_arm": "ainglish",
            "calibration_min_gap": 0.5,
            "panel_neff": 2,
            "panel": readers,
            "comparator": {
                "kind": "committed-per-item-comparator-v1",
                "description": interpretations[name],
            },
            "comparison_identity": {
                "comparator_genre": "committed-per-item-comparator-v1",
                "pair_rendering": "held-out exact semantic consequence question",
                "reader_roster": [reader["name"] for reader in readers],
                "form_strata": [row["id"] for row in strata],
            },
            "settlement_strata": strata,
            "training_asymmetry": (
                "The named readers were trained primarily on ordinary English and are not assumed to have seen "
                "Ainglish. This is present zero-shot transparency evidence, not a forecast of performance after "
                "future Ainglish-aware training."
            ),
            "items_url": (
                f"https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{SOURCE_COMMIT}/"
                f"overnight-comprehension-progression-wave-v1-2026-09-02/{meta['file']}"
            ),
            "items_sha256": meta["items_sha256"],
            "source": {
                "repository": "dexagon-ai/ainglish-evidence",
                "commit": SOURCE_COMMIT,
                "path": f"overnight-comprehension-progression-wave-v1-2026-09-02/{meta['file']}",
            },
            "attempt": {
                "proposal_revision": meta["slug"],
                "estimand": (
                    "Percentage-point exact-answer accuracy difference, registered compact form minus its committed "
                    f"per-item comparator, over {meta['scientific_items']} frozen fresh items for {meta['construct']}; "
                    f"equal-weight mean of separately reported strata ({', '.join(row['id'] for row in strata)}). "
                    f"{interpretations[name]} Absolute arms, per-reader results, intervals, calibration, yield, and "
                    "every stratum remain visible."
                ),
                "admissibility_gates": [
                    "the live proposal remains current at measured stage and still names submit_original for comprehension_accuracy_delta immediately before mint",
                    f"the published answer-bearing item array hashes to {meta['items_sha256']} and contains exactly 160 scientific plus 16 calibration items",
                    "all scientific questions are held-out exact semantic-consequence questions and contain none of the target marker strings",
                    "each careful-English comparator states the complete target meaning; each bare comparator is balanced across opposed hidden intentions and is never presented as a complete mapping",
                    "both named local reader artifacts match their declared Ollama digests and run statelessly at temperature 0 with the frozen seed and opaque-choice output",
                    "the construct-free planted-effect calibration executes first in both arms for each reader and must show an explicit-minus-unresolved accuracy gap of at least 0.5",
                    "each real item names one committed equal-weight settlement stratum, and every form and comparator class remains separately visible",
                    "no reader receives repository access, retrieval, conversation history, or a register definition beyond the presented cell",
                    "zero response-bound truncations and a passing full-cell-yield guard are required; transport or format failure produces a typed abort and no retry",
                    "every finite supportive, adverse, null, floor-bound, or ceiling-bound outcome is filed exactly once",
                    "the filing principal is distinct from the proposal's original proposer",
                    "a settlement-bearing replication must come from a different principal with a wholly fresh complete item manifest",
                ],
                "planned_sample": {
                    "comparison": "registered compact form versus committed per-item comparator",
                    "scientific_items": 160,
                    "calibration_items": 16,
                    "readers": len(readers),
                    "reader_families": ["Mistral Small 3.2 24B", "Gemma 3 12B"],
                    "panel_neff": 2,
                    "real_cells": 320,
                    "calibration_cells": 64,
                    "settlement_strata": meta["stratum_counts"],
                    "noninferiority_margin_pp": -5,
                    "sdk_version": SDK_VERSION,
                    "source_commit": SOURCE_COMMIT,
                },
            },
        }
        spec["content_sha256"] = sha256(canonical(spec)).hexdigest()
        path = ROOT / f"runspec-{name}.json"
        path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        runspecs[name] = {"file": path.name, "content_sha256": spec["content_sha256"]}
    output = {
        "kind": "dexagon.ainglish.overnight-comprehension-runspec-index.v1",
        "source_commit": SOURCE_COMMIT,
        "sdk_version": SDK_VERSION,
        "runspecs": runspecs,
        "model_calls": 0,
    }
    output["content_sha256"] = sha256(canonical(output)).hexdigest()
    (ROOT / "runspec-index.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
