#!/usr/bin/env python3
"""Bind the published carrier to two existing qualified local readers."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_COMMIT = "cd3d53e91f54f3a045dea9a3bfb3bf6963ba2e55"
SDK_VERSION = "0.2.52"
TARGET = "f68f899dd4a737c36733f3d9aaac2a9558f6727ed0c920280ad23974c7d721ed"


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def main() -> None:
    index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    seed = 2026090417
    readers = [
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
            "seed": seed,
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
            "seed": seed,
        },
    ]
    spec = {
        "kind": "dexagon.ainglish.verdict-fail-comprehension-runspec.v1",
        "construct": "verdict-fail / no-verdict",
        "public_id": "a-6974j2deetg3rcb5",
        "slug": "verdict-fail-no-verdict",
        "metric": "comprehension_accuracy_delta",
        "replicates_hash": TARGET,
        "seed": seed,
        "planted_arm": "ainglish",
        "calibration_min_gap": 0.5,
        "panel_neff": 2,
        "panel": readers,
        "comparator": {"kind": "complete-careful-english-v1"},
        "comparison_identity": {
            "comparator_genre": "complete-careful-english-v1",
            "pair_rendering": "held-out exact consequence question",
            "reader_roster": [reader["name"] for reader in readers],
            "filing_shape": "aggregate-only legacy replication",
        },
        "training_asymmetry": index["training_asymmetry"],
        "items_url": f"https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{SOURCE_COMMIT}/verdict-fail-comprehension-replication-v1-2026-09-04/items.json",
        "items_sha256": index["items_sha256"],
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "commit": SOURCE_COMMIT,
            "path": "verdict-fail-comprehension-replication-v1-2026-09-04/items.json",
        },
        "attempt": {
            "proposal_revision": "verdict-fail-no-verdict",
            "estimand": (
                f"Independent aggregate-only replication of {TARGET}: percentage-point exact-answer accuracy "
                "difference, verdict-fail/no-verdict marked report minus complete careful English carrying the same "
                "answer-bearing facts, over 96 wholly fresh balanced items and two existing qualified reader lineages"
            ),
            "admissibility_gates": [
                "fresh authenticated personalised suggestions offer this exact target immediately before mint",
                "fresh authenticated proposal read still names the target in an unresolved evidence work item",
                "Dexagon is disjoint from the source measurer and has not already measured this target",
                f"the published answer-bearing array hashes to {index['items_sha256']} and contains 96 scientific plus 16 calibration items",
                "all 96 scientific complete-message pairs have zero exact overlap with every filed proposal manifest",
                "the comparator remains complete-careful-english-v1 and carries the same answer-bearing facts",
                "no settlement strata are attached because the named legacy source is aggregate-only",
                "both local model artifacts match their declared digests and run at temperature zero",
                "construct-free calibration runs first and each reader recovers at least a 0.5 planted-arm gap",
                "no reader receives repository access, retrieval, conversation history, or an Ainglish definition",
                "zero response-bound truncations and full cell yield are required; any failure is a typed abort without retry",
                "every finite supportive, adverse, or null result is filed exactly once",
            ],
            "planned_sample": {
                "metric": "comprehension_accuracy_delta",
                "replicates_hash": TARGET,
                "scientific_items": 96,
                "calibration_items": 16,
                "forms": {"verdict-fail": 48, "no-verdict": 48},
                "readers": 2,
                "reader_families": ["Mistral Small 3.2 24B", "Gemma 3 12B"],
                "panel_neff": 2,
                "real_cells": 192,
                "calibration_cells": 64,
                "source_commit": SOURCE_COMMIT,
                "sdk_version": SDK_VERSION,
            },
        },
    }
    spec["content_sha256"] = sha256(canonical(spec)).hexdigest()
    (ROOT / "runspec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"content_sha256": spec["content_sha256"], "items_sha256": spec["items_sha256"], "model_calls": 0}, indent=2))


if __name__ == "__main__":
    main()
