#!/usr/bin/env python3
"""Bind the published approx robustness carrier to existing qualified readers."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_COMMIT = "4ed3a3a2937c5b90d9d414d440e36fd2ba83e636"
TARGET = "79caba68e4ee77f5caeb9bbabdf349819b60195b91c2e43cbae3352172ca9f28"
READERS = [
    {
        "name": "mistral-small3.2-24b-opaque-choice-q4_k_m", "provider": "ollama",
        "model": "dexagon-mistral-small3.2-24b-pp-task:ctx4k",
        "model_digest": "sha256:6629ee92de51c9a1367e1331cfa9ef6a77058a44a6a3e18ab524b2d0404252de",
        "precision": "q4_k_m", "api": "openai", "base_url": "http://127.0.0.1:11434/v1",
        "max_tokens": 32, "timeout_s": 120, "temperature": 0, "seed": 2026090415,
    },
    {
        "name": "gemma3-12b-opaque-choice-q4_k_m", "provider": "ollama",
        "model": "dexagon-gemma3-12b-pp-task:ctx4k",
        "model_digest": "sha256:de1f65ea3438dfcc7c3387802b9425a140fb01ecc79edf4924a13fab051eb68f",
        "precision": "q4_k_m", "api": "openai", "base_url": "http://127.0.0.1:11434/v1",
        "max_tokens": 32, "timeout_s": 120, "temperature": 0, "seed": 2026090415,
    },
]


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def main() -> None:
    index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    controls = json.loads((ROOT / "calibration.json").read_text(encoding="utf-8"))["items"]
    assert sha256(canonical(controls)).hexdigest() == index["calibration_sha256"]
    spec = {
        "kind": "dexagon.ainglish.approx-robustness-settlement-runspec.v2",
        "construct": "approx(<N>)",
        "public_id": "a-vkjb699gk6m14rar",
        "slug": "approx-n-approximation-marker-parenthesized-d-1-robust-5",
        "metric": "robustness_delta",
        "replicates_hash": TARGET,
        "seed": 2026090415,
        "corruption": {"channel": "drop_char"},
        "planted_arm": "ainglish",
        "calibration_min_gap": 0.5,
        "panel_neff": 2,
        "panel": READERS,
        "comparator": {
            "kind": "careful-english-approximately-n-v1",
            "description": "The target's preregistered comparator: careful English 'approximately N'.",
        },
        "comparison_identity": {
            "comparator_genre": "careful-english-approximately-n-v1",
            "corruption_channel": "drop_char",
            "pair_rendering": "cold-read four-way commitment consequence",
            "reader_roster": [reader["name"] for reader in READERS],
            "filing_shape": "aggregate-only legacy replication",
        },
        "items_url": f"https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{SOURCE_COMMIT}/approx-robustness-settlement-v2-2026-09-04/items.json",
        "items_sha256": index["items_sha256"],
        "calibration_items": controls,
        "training_asymmetry": "Present readers have ordinary-English training and are not assumed to have seen Ainglish.",
        "source": {"repository": "dexagon-ai/ainglish-evidence", "commit": SOURCE_COMMIT, "path": "approx-robustness-settlement-v2-2026-09-04/items.json"},
        "attempt": {
            "proposal_revision": "approx-n-approximation-marker-parenthesized-d-1-robust-5",
            "estimand": (
                "Independent aggregate-only replication of robustness_delta original 79caba68...: formula-v4 "
                "differential degradation in percentage points for approx(N) minus careful English approximately N "
                "under one deterministic drop_char event per arm, over 48 wholly fresh cold-read items, two existing "
                "qualified reader lineages, four balanced commitment classes, and eight separately frozen calibration items."
            ),
            "admissibility_gates": [
                "fresh authenticated personalised suggestions still offer target 79caba68... to Dexagon immediately before mint",
                "a fresh authenticated proposal read still names the exact target in an unresolved evidence work item",
                "Dexagon is disjoint from the target measurer and has not already completed a row against this target",
                f"the 48 answer-bearing scientific items hash to {index['items_sha256']} and have zero exact complete-pair overlap with the target's 48 items",
                f"the eight calibration items hash to {index['calibration_sha256']} and execute before scientific cells",
                "metric, comparator, corruption channel, and aggregate-only filing shape preserve the target estimand",
                "all four commitment classes and all four answer positions contain exactly 12 scientific items",
                "both local reader artifacts match their declared digests and run statelessly at temperature 0 with the frozen seed",
                "each reader has a live answer for both arms of every calibration item and the panel gap is at least 0.5",
                "every corruption is precomputed and must change its source text before inference",
                "zero response-bound truncations and full quartet yield are required; any gate failure is an honest typed abort without retry",
                "every finite supportive, adverse, null, floor-censored, or uncensored result is filed exactly once",
            ],
            "planned_sample": {
                "metric": "robustness_delta", "replicates_hash": TARGET, "scientific_items": 48,
                "calibration_items": 8, "commitment_classes": index["classes"], "corruption_channel": "drop_char",
                "readers": 2, "reader_families": ["Mistral Small 3.2 24B", "Gemma 3 12B"],
                "panel_neff": 2, "real_cells": 384, "calibration_cells": 32,
                "source_commit": SOURCE_COMMIT, "sdk_version": "0.2.52",
            },
        },
    }
    spec["content_sha256"] = sha256(canonical(spec)).hexdigest()
    (ROOT / "runspec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"runspec": "runspec.json", "content_sha256": spec["content_sha256"], "model_calls": 0}, indent=2))


if __name__ == "__main__":
    main()

