#!/usr/bin/env python3
"""Bind the fresh approx(N) carrier and reader instruments to an immutable runspec."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SLUG = "approx-n-approximation-marker-parenthesized-d-1-robust-5"
REPLICATES = "7d6674a29876f97c9fd0c99c16c74ad73619003675dda4a546cbc7bfe0120b1e"
SEED = 2026082602


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--items-commit", required=True)
    args = parser.parse_args()
    if len(args.items_commit) != 40 or any(ch not in "0123456789abcdef" for ch in args.items_commit):
        raise SystemExit("items commit must be a full lowercase Git SHA")

    freeze = json.loads((ROOT / "freeze-receipt.json").read_text())
    readers = [
        {
            "name": "mistral-small3.2-24b-approx-fresh-q4_k_m",
            "provider": "ollama",
            "model": "dexagon-mistral-small3.2-24b-approx-fresh:ctx4k",
            "model_digest": "sha256:6462c4a5d37fa0b295cf83fce0b547aa7759939424f3ca87e8274131ac55f9a3",
            "precision": "q4_k_m",
            "api": "openai",
            "base_url": "http://127.0.0.1:11434/v1",
            "max_tokens": 64,
            "timeout_s": 120,
            "temperature": 0,
            "seed": SEED,
            "reasoning_effort": "none",
        },
        {
            "name": "phi4-14b-approx-fresh-q4_k_m",
            "provider": "ollama",
            "model": "dexagon-phi4-14b-approx-fresh:ctx4k",
            "model_digest": "sha256:a8fee446b99032dc47170edebda0176b93e37a3f6c28dc856401f9f0269d0db2",
            "precision": "q4_k_m",
            "api": "openai",
            "base_url": "http://127.0.0.1:11434/v1",
            "max_tokens": 64,
            "timeout_s": 120,
            "temperature": 0,
            "seed": SEED,
            "reasoning_effort": "none",
        },
        {
            "name": "falcon3-10b-approx-fresh-q4_k_m",
            "provider": "ollama",
            "model": "dexagon-falcon3-10b-approx-fresh:ctx4k",
            "model_digest": "sha256:415826b4c312e08529051152d75adc6430cfc38dcdc51d08d78e957023b8af74",
            "precision": "q4_k_m",
            "api": "openai",
            "base_url": "http://127.0.0.1:11434/v1",
            "max_tokens": 64,
            "timeout_s": 120,
            "temperature": 0,
            "seed": SEED,
            "reasoning_effort": "none",
        },
    ]
    spec = {
        "construct": "approx(N) cold-read fresh-input replication",
        "slug": SLUG,
        "metric": "comprehension_accuracy_delta",
        "replicates_hash": REPLICATES,
        "seed": SEED,
        "planted_arm": "ainglish",
        "calibration_min_gap": 0.5,
        "panel_neff": 3,
        "panel": readers,
        "comparator": {
            "kind": "careful-english-approximately-n-v1",
            "description": "Careful English 'approximately N'; the superseded ~N form is absent.",
        },
        "items_url": (
            "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
            f"{args.items_commit}/approx-n-comprehension-replication-2026-08-26/items.json"
        ),
        "items_sha256": freeze["items_sha256"],
        "resources": {
            "minimum_free_mib": 20_000,
            "expected_gpu_name": "NVIDIA GeForce RTX 3090",
            "maximum_utilization_percent": 25,
        },
        "attempt": {
            "proposal_revision": SLUG,
            "estimand": (
                "Independent fresh-input replication of Reticuli manifest " + REPLICATES +
                ": comprehension_accuracy_delta formula v2 for approx(N) versus careful English "
                "'approximately N' in the cold-read stratum only. Exact four-way classification "
                "of the writer's commitment (approximate, exact, unspecified, cannot tell) is "
                "asked through a held-out consequence over 48 items, 12 per class, with "
                "counterbalanced arms and three disjoint local reader families at temperature 0. "
                "Both absolute arm accuracies and per-class rates are retained; no glossed stratum "
                "is run or pooled."
            ),
            "admissibility_gates": [
                f"the public 48+8 carrier has SDK canonical-items sha256 {freeze['items_sha256']}",
                f"the answer-bearing inputs were frozen at public commit {args.items_commit} before mint or reader spend",
                "the original answer-bearing carrier was not fetched or opened; all complete pairs are newly authored",
                "exactly 12 items occupy each of approximate, exact, unspecified, and cannot-tell, and each answer position occurs 12 times",
                "only the approximate class differs by arm: careful English approximately N versus approx(N); all negative-control pairs are byte-identical",
                "the original cold-read metric, formula, class population, counterbalancing, and no-pooling rule are preserved",
                "the Mistral, Phi, and Falcon reader families are disjoint from the original Qwen, Gemma, and Ornith roster and match declared digests",
                "construct-free calibration runs first in both arms for every reader and must show a planted-arm gap of at least 0.5",
                "the local Ollama endpoint is reachable and at least one RTX 3090 has 20,000 MiB free before mint",
                "zero response-bound truncations and a passing cell-yield guard are required",
                "supportive, null, adverse, disagreeing, and calibration-failed outcomes are filed once without outcome retry",
            ],
            "planned_sample": {
                "stratum": "cold-read",
                "real_items": 48,
                "per_class": 12,
                "classes": ["approximate", "exact", "unspecified", "cannot tell"],
                "calibration_items": 8,
                "readers": 3,
                "reader_families": ["Mistral Small 3.2 24B", "Phi 4 14B", "Falcon 3 10B"],
                "original_reader_families": ["Qwen 3.8 27B", "Gemma 4 31B", "Ornith 35B"],
                "real_cells": 144,
                "calibration_cells": 48,
                "panel_neff": 3,
            },
        },
    }

    path = ROOT / "runspec.json"
    encoded = (json.dumps(spec, indent=2, ensure_ascii=False) + "\n").encode()
    path.write_bytes(encoded)
    index = {
        "kind": "ainglish.approx-n-fresh-comprehension-replication-index.v1",
        "items_commit": args.items_commit,
        "campaigns": {
            "approx-n-cold-read": {
                "runspec": path.name,
                "runspec_sha256": hashlib.sha256(encoded).hexdigest(),
                "receipt_stem": "approx-n-fresh-cold-read-replication",
                "gpu_index": 0,
            }
        },
    }
    index["content_sha256"] = hashlib.sha256(canonical(index)).hexdigest()
    (ROOT / "runspec-index.json").write_text(json.dumps(index, indent=2) + "\n")
    print(json.dumps(index, indent=2))


if __name__ == "__main__":
    main()
