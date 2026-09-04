#!/usr/bin/env python3
"""Bind the published settlement carriers to existing qualified readers."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_COMMIT = "c322fef54a77684b40731fba767fa395fde32dee"
SDK_VERSION = "0.2.52"
READERS = [
    {
        "name": "mistral-small3.2-24b-opaque-choice-q4_k_m",
        "provider": "ollama",
        "model": "dexagon-mistral-small3.2-24b-pp-task:ctx4k",
        "model_digest": "sha256:6629ee92de51c9a1367e1331cfa9ef6a77058a44a6a3e18ab524b2d0404252de",
        "precision": "q4_k_m", "api": "openai", "base_url": "http://127.0.0.1:11434/v1",
        "max_tokens": 32, "timeout_s": 120, "temperature": 0,
    },
    {
        "name": "gemma3-12b-opaque-choice-q4_k_m",
        "provider": "ollama",
        "model": "dexagon-gemma3-12b-pp-task:ctx4k",
        "model_digest": "sha256:de1f65ea3438dfcc7c3387802b9425a140fb01ecc79edf4924a13fab051eb68f",
        "precision": "q4_k_m", "api": "openai", "base_url": "http://127.0.0.1:11434/v1",
        "max_tokens": 32, "timeout_s": 120, "temperature": 0,
    },
]


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def main() -> None:
    index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    runspecs = {}
    for offset, (name, meta) in enumerate(index["campaigns"].items(), 1):
        seed = 2026090410 + offset
        readers = [{**reader, "seed": seed} for reader in READERS]
        comparator_kind = meta["comparator"]["kind"]
        spec = {
            "kind": "dexagon.ainglish.dispute-settlement-runspec.v1",
            "construct": meta["construct"],
            "public_id": meta["public_id"],
            "slug": meta["slug"],
            "metric": "comprehension_accuracy_delta",
            "replicates_hash": meta["replicates_hash"],
            "seed": seed,
            "planted_arm": "ainglish",
            "calibration_min_gap": 0.5,
            "panel_neff": 2,
            "panel": readers,
            "comparator": meta["comparator"],
            "comparison_identity": {
                "comparator_genre": comparator_kind,
                "pair_rendering": "held-out exact consequence question",
                "reader_roster": [reader["name"] for reader in readers],
                "filing_shape": "aggregate-only legacy replication",
            },
            "training_asymmetry": index["training_asymmetry"],
            "items_url": f"https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{SOURCE_COMMIT}/dispute-settlement-wave-v1-2026-09-04/{meta['file']}",
            "items_sha256": meta["items_sha256"],
            "source": {
                "repository": "dexagon-ai/ainglish-evidence", "commit": SOURCE_COMMIT,
                "path": f"dispute-settlement-wave-v1-2026-09-04/{meta['file']}",
            },
            "attempt": {
                "proposal_revision": meta["slug"],
                "estimand": (
                    f"Independent aggregate-only replication of {meta['replicates_hash']} for {meta['construct']}: "
                    f"percentage-point exact-answer accuracy difference, marked form minus {comparator_kind}, "
                    f"over {meta['scientific_items']} wholly fresh frozen items and two existing qualified reader lineages. "
                    "Form and probe balance remain visible in the public carrier but are not attached as settlement strata "
                    "because the named legacy target declares no manifest-bound stratum contract."
                ),
                "admissibility_gates": [
                    "fresh authenticated personalised suggestions still offer this exact target hash to Dexagon immediately before mint",
                    "a fresh authenticated proposal read still names the exact target in an unresolved evidence work item",
                    "the executing principal is disjoint from the target measurer and has not already completed a measurement against this exact target",
                    f"the published answer-bearing array hashes to {meta['items_sha256']} and contains exactly {meta['scientific_items']} scientific plus {meta['calibration_items']} calibration items",
                    "all scientific message pairs are newly written and differ from the target's metric inputs",
                    f"the comparator remains {comparator_kind}; it is not replaced after inspecting outcomes",
                    "no settlement_strata, settlement_item_field, or settlement_rule is attached to this aggregate-only legacy replication",
                    "both local reader artifacts match their declared digests and run statelessly at temperature 0 with the frozen seed",
                    "construct-free calibration executes first and must recover an explicit-minus-unresolved gap of at least 0.5 for each reader",
                    "no reader receives repository access, retrieval, conversation history, or a register definition beyond the presented cell",
                    "zero response-bound truncations and full cell yield are required; transport or format failure is a typed abort without retry",
                    "every finite supportive, adverse, or null result is filed exactly once",
                ],
                "planned_sample": {
                    "metric": "comprehension_accuracy_delta", "replicates_hash": meta["replicates_hash"],
                    "scientific_items": meta["scientific_items"], "calibration_items": meta["calibration_items"],
                    "forms": meta["forms"], "probes": meta["probes"], "readers": 2,
                    "reader_families": ["Mistral Small 3.2 24B", "Gemma 3 12B"],
                    "panel_neff": 2, "real_cells": meta["scientific_items"] * 2,
                    "calibration_cells": meta["calibration_items"] * 2 * 2,
                    "source_commit": SOURCE_COMMIT, "sdk_version": SDK_VERSION,
                },
            },
        }
        spec["content_sha256"] = sha256(canonical(spec)).hexdigest()
        path = ROOT / f"runspec-{name}.json"
        path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        runspecs[name] = {"file": path.name, "content_sha256": spec["content_sha256"]}
    output = {"kind": "dexagon.ainglish.dispute-settlement-runspec-index.v1", "source_commit": SOURCE_COMMIT, "sdk_version": SDK_VERSION, "runspecs": runspecs, "model_calls": 0}
    output["content_sha256"] = sha256(canonical(output)).hexdigest()
    (ROOT / "runspec-index.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
