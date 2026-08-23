#!/usr/bin/env python3
"""Build the immutable panel runspec without reader calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "runspec-dedicated-gpu1.json"


def main() -> None:
    runspec = {
        "construct": "percentage points, not bare percent",
        "slug": "percentage-points-not-bare-percent-a-change-to-a-percentage-",
        "metric": "comprehension_accuracy_delta",
        "seed": 1231190656,
        "planted_arm": "ainglish",
        "calibration_min_gap": 0.5,
        "panel_neff": 2,
        "panel": [
            {
                "name": "mistral-small3.2-24b-pp-task-q4_k_m",
                "provider": "ollama",
                "model": "dexagon-mistral-small3.2-24b-pp-task:ctx4k",
                "model_digest": "sha256:6629ee92de51c9a1367e1331cfa9ef6a77058a44a6a3e18ab524b2d0404252de",
                "precision": "q4_k_m",
                "max_tokens": 128,
                "timeout_s": 120,
                "temperature": 0,
                "seed": 1231190656,
                "api": "openai",
                "base_url": "http://127.0.0.1:11435/v1",
            },
            {
                "name": "gemma3-12b-pp-task-q4_k_m",
                "provider": "ollama",
                "model": "dexagon-gemma3-12b-pp-task:ctx4k",
                "model_digest": "sha256:de1f65ea3438dfcc7c3387802b9425a140fb01ecc79edf4924a13fab051eb68f",
                "precision": "q4_k_m",
                "max_tokens": 128,
                "timeout_s": 120,
                "temperature": 0,
                "seed": 1231190656,
                "api": "openai",
                "base_url": "http://127.0.0.1:11435/v1",
            },
        ],
        "items_url": (
            "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/819ad68/"
            "percentage-points-opener-replication-2026-08-21/items.json"
        ),
        "items_sha256": "4962794f1223a00dd5603b27c05339f65a621ed8654f005d5a650469659b92ca",
        "replicates_hash": "f9e78cc01f6725961fc0b9b119ae6f5d09f74d2858b92d81f2f1d8a08fa75c5b",
        "attempt": {
            "proposal_revision": "percentage-points-not-bare-percent-a-change-to-a-percentage-",
            "estimand": (
                "Different-input replication of Reticuli's f9e78cc0 endpoints-absent correctness "
                "original: pooled percentage-point difference in exact intended-final-rate "
                "accuracy, explicit percentage-points/%-relative arm minus bare-% arm. Thirty-two "
                "fresh scenarios are balanced 16 additive/16 relative and 16 rise/16 fall; every "
                "message carries an approximate per-1,000 headcount anchor that pins intent while "
                "withholding the final percentage. Two independently configured non-Qwen reader "
                "families each receive one counterbalanced arm per item. Report absolute arms, "
                "per-reader and per-intent cells; file agreement or disagreement without an "
                "outcome gate. This estimates correctness only, not endpoint detectability."
            ),
            "admissibility_gates": [
                (
                    "the anonymously fetched 40-item artifact has exact sha256 "
                    "141d17b8824cd4980e304ad138838687fb04031285c6ed8d30cfaef9fa17b55e "
                    "and SDK canonical-items sha256 "
                    "4962794f1223a00dd5603b27c05339f65a621ed8654f005d5a650469659b92ca"
                ),
                (
                    "the replication's scientific items were independently authored and frozen "
                    "without opening Reticuli's answer-bearing block; no computed pair-overlap "
                    "value is claimed, and settlement eligibility remains the register's decision"
                ),
                (
                    "the artifact retains 32 fresh scored rows split 16 additive/16 relative and "
                    "16 rise/16 fall, plus 8 genuine both-arm calibration rows"
                ),
                (
                    "every scored pair is endpoints-absent and differs only in bare percent versus "
                    "percentage points or percent-relative; the approximate headcount anchor is "
                    "identical across arms and pins the intended reading"
                ),
                (
                    "seed 1231190656 is the first digest-prefix-increment deal satisfying the "
                    "frozen balance rule: pooled arms 32/32, intent and direction 14..18 per arm, "
                    "reader arms 14..18, cross-strata 2..6, option positions 12/10/10 per arm"
                ),
                (
                    "both reader configurations expose distinct non-Qwen model digests and the "
                    "both-arms-per-reader calibration-first gap is at least 0.5"
                ),
                (
                    "both readers execute sequentially on dedicated loopback Ollama 127.0.0.1:11435 "
                    "pinned to RTX 3090 GPU 1 with one loaded model and one request; CPU fallback is prohibited"
                ),
                (
                    "any resource, transport, calibration, cell-yield, truncation, commitment, "
                    "or reconciliation failure becomes a typed abort and is not retried in place"
                ),
                "the panel harness emits a measurement whose filed manifest matches the preregistered commitment",
            ],
            "planned_sample": {
                "scored_items": 32,
                "calibration_items": 8,
                "readers": 2,
                "reader_families": ["Mistral Small 3.2", "Gemma 3"],
                "reader_precision": "both local Q4_K_M",
                "real_cells": 64,
                "calibration_cells": 32,
                "intents": {"additive": 16, "relative": 16},
                "directions": {"rose": 16, "fell": 16},
                "aggregate_arm_cells": {"english": 32, "ainglish": 32},
                "seed": 1231190656,
                "sdk_version": "0.2.33",
                "execution": (
                    "dedicated local RTX 3090 GPU 1; one loaded model and one request at a time; "
                    "4096-token context; no CPU fallback"
                ),
            },
        },
    }
    encoded = (json.dumps(runspec, indent=2, ensure_ascii=False) + "\n").encode()
    OUT.write_bytes(encoded)
    print(json.dumps({
        "output": str(OUT),
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "reader_calls": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
