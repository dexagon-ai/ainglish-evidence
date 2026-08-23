#!/usr/bin/env python3
"""Build the attempt-backed runspec after the fresh items are commit-pinned."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SLUG = "twice-weekly-every-two-weeks-split-biweekly-into-its-two-inc"
TARGET_HASH = "ac6fb637c65705f149d2daa2034c72dd40322ce2ac430e736c1d9837d6e78181"
BASE_URL = "http://127.0.0.1:11435/v1"
OUTPUT = ROOT / "runspec-every-two-weeks-fresh.json"

READERS = [
    {
        "name": "gemma3-12b-pp-task-q4_k_m",
        "provider": "ollama",
        "model": "dexagon-gemma3-12b-pp-task:ctx4k",
        "model_digest": "de1f65ea3438dfcc7c3387802b9425a140fb01ecc79edf4924a13fab051eb68f",
        "precision": "q4_k_m",
        "max_tokens": 1024,
        "temperature": 0,
        "seed": 20260823,
        "api": "openai",
        "base_url": BASE_URL,
    },
    {
        "name": "mistral-small3.2-24b-pp-task-q4_k_m",
        "provider": "ollama",
        "model": "dexagon-mistral-small3.2-24b-pp-task:ctx4k",
        "model_digest": "6629ee92de51c9a1367e1331cfa9ef6a77058a44a6a3e18ab524b2d0404252de",
        "precision": "q4_k_m",
        "max_tokens": 1024,
        "temperature": 0,
        "seed": 20260823,
        "api": "openai",
        "base_url": BASE_URL,
    },
]


def build(freeze_commit: str) -> dict:
    document = json.loads((ROOT / "every-two-weeks-fresh-items.json").read_text(encoding="utf-8"))
    return {
        "construct": "every-two-weeks",
        "slug": SLUG,
        "metric": "comprehension_accuracy_delta",
        "replicates_hash": TARGET_HASH,
        "seed": 2026082304,
        "planted_arm": "ainglish",
        "calibration_min_gap": 0.5,
        "instrument_revision": "fresh-every-two-weeks-v1-family-floor-policy",
        "panel": READERS,
        "items_url": (
            "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
            f"{freeze_commit}/biweekly-every-two-weeks-replication-2026-08-23/"
            "every-two-weeks-fresh-items.json"
        ),
        "items_sha256": document["sha256"],
        "input_disjointness_receipt": {
            "value": 1.0,
            "comparison": "exact complete (english, ainglish) pairs",
            "original_items_sha256": document["original_items_sha256"],
            "fresh_items_sha256": document["sha256"],
            "shared_complete_pairs": 0,
            "original_complete_pairs": 100,
            "fresh_complete_pairs": 100,
        },
        "decision_policy": {
            "aggregate_noninferiority_margin_pp": -5,
            "flagship_family_floor_pp": -5,
            "rule": (
                "Flagship support requires the aggregate eligible interval lower bound to be at "
                "least -5 percentage points and no preregistered reader-family point estimate "
                "below -5 percentage points. A failing family is exposed, never averaged away."
            ),
        },
        "attempt": {
            "proposal_revision": SLUG,
            "estimand": (
                "Replication of ac6fb637c657...: comprehension_accuracy_delta in percentage "
                "points for every-two-weeks versus its complete careful-English mapping over 100 "
                "wholly fresh rows: 70 cadence-count consequences and 30 anchor, clock, and "
                "completion over-reading controls. Reader-family values remain separate; every "
                "finite result files regardless of direction."
            ),
            "admissibility_gates": [
                f"the commit-pinned item document hashes to {document['sha256']} and contains exactly 100 scientific rows plus 12 construct-free calibration rows",
                "the fresh document shares zero exact complete (english, ainglish) pairs with original item digest c16a3608ec7139fe1b4a7ac6f290c703cb1052c6b8a108adc50c04256fb71584",
                "scientific rows contain exactly 70 cadence-count consequences and 10 each anchor, clock, and completion over-reading controls",
                "the English arm is the proposal's complete careful-English mapping; bare biweekly appears in neither scientific arm",
                "count rows bind an external included anchor and half-open window without leaking a calendar date, weekday, or clock time",
                "the 12 construct-free calibration rows execute first in both arms and must show an explicit-minus-underdetermined accuracy gap of at least 0.5",
                "Gemma 3 12B and Mistral Small 3.2 24B execute sequentially at Q4_K_M, temperature 0, fixed seeds, and the pinned model digests",
                "both readers remain fully GPU-resident on a dedicated local RTX 3090; CPU fallback, a contested GPU, or a non-empty competing queue aborts",
                "all null, adverse, supportive, fault, and truncation outcomes are retained; only input, transport, calibration, yield, commitment, or resource-contract failures may abort",
                "the registered aggregate and both reader-family point estimates are reported; the prospective -5 pp family floor is not changed after seeing results",
            ],
            "planned_sample": {
                "form": "every-two-weeks",
                "replicates_hash": TARGET_HASH,
                "real_items": 100,
                "calibration_items": 12,
                "probe_counts": {
                    "cadence_count": 70,
                    "anchor_not_supplied": 10,
                    "clock_not_supplied": 10,
                    "completion_not_supplied": 10,
                },
                "comparison": "marked form versus complete careful-English mapping",
                "aggregate_noninferiority_margin_pp": -5,
                "flagship_family_floor_pp": -5,
                "readers": 2,
                "reader_families": ["Gemma 3 12B", "Mistral Small 3.2 24B"],
                "reader_precision": "both local q4_k_m",
                "real_cells": 200,
                "calibration_cells": 48,
                "execution": (
                    "dedicated local RTX 3090; readers sequential; 4,096-token context; no CPU "
                    "fallback; shared and dedicated queues empty at mint"
                ),
            },
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze-commit", required=True)
    args = parser.parse_args()
    if len(args.freeze_commit) != 40 or any(ch not in "0123456789abcdef" for ch in args.freeze_commit):
        raise SystemExit("--freeze-commit must be a full lowercase SHA-1 commit id")
    spec = build(args.freeze_commit)
    OUTPUT.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": OUTPUT.name,
        "file_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
        "items_sha256": spec["items_sha256"],
        "replicates_hash": spec["replicates_hash"],
    }, indent=2))


if __name__ == "__main__":
    main()
