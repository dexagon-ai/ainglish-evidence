#!/usr/bin/env python3
"""Build the immutable panel runspec without reader or governance calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ITEMS = ROOT / "items.json"
OUT = ROOT / "runspec-gpu0.json"
SEED = 2026082609
SDK_VERSION = "0.2.35"
ITEMS_COMMIT = "b974b1120dbd4b2c799e77b6d4e72e77400dca1c"
ITEMS_SHA256 = "1f8607906baa30a1a6f2f9ef472c57d8c146dcd22e4d9c92787f0c86d51dc849"
TARGET = "e612f95a65792990066b666186abb7ee08da87f384972f1158067c4a16a103e9"
SLUG = "by-unknown-by-withheld-typed-doer-omission-why-mistakes-were-3"


def main() -> None:
    document = json.loads(ITEMS.read_text())
    items = document["items"]
    digest = hashlib.sha256(json.dumps(
        items, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode()).hexdigest()
    if digest != ITEMS_SHA256 or document.get("sha256") != ITEMS_SHA256:
        raise SystemExit("REFUSING: frozen item digest mismatch")
    real = [item for item in items if not item.get("calibration")]
    calibration = [item for item in items if item.get("calibration")]
    if len(real) != 24 or len(calibration) != 8:
        raise SystemExit("REFUSING: frozen 24+8 sample changed")

    runspec = {
        "construct": "by-withheld",
        "slug": SLUG,
        "metric": "comprehension_accuracy_delta",
        "seed": SEED,
        "planted_arm": "ainglish",
        "calibration_min_gap": 0.5,
        "panel_neff": 2,
        "panel": [
            {
                "name": "mistral-small3.2-24b-route-task-q4_k_m",
                "provider": "ollama",
                "model": "dexagon-mistral-small3.2-24b-pp-task:ctx4k",
                "model_digest": "sha256:6629ee92de51c9a1367e1331cfa9ef6a77058a44a6a3e18ab524b2d0404252de",
                "precision": "q4_k_m",
                "max_tokens": 128,
                "timeout_s": 120,
                "temperature": 0,
                "seed": SEED,
                "api": "openai",
                "base_url": "http://127.0.0.1:11435/v1",
            },
            {
                "name": "gemma3-12b-route-task-q4_k_m",
                "provider": "ollama",
                "model": "dexagon-gemma3-12b-pp-task:ctx4k",
                "model_digest": "sha256:de1f65ea3438dfcc7c3387802b9425a140fb01ecc79edf4924a13fab051eb68f",
                "precision": "q4_k_m",
                "max_tokens": 128,
                "timeout_s": 120,
                "temperature": 0,
                "seed": SEED,
                "api": "openai",
                "base_url": "http://127.0.0.1:11435/v1",
            },
        ],
        "items_url": (
            "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
            f"{ITEMS_COMMIT}/by-withheld-comprehension-replication-2026-08-24/items.json"
        ),
        "items_sha256": ITEMS_SHA256,
        "replicates_hash": TARGET,
        "attempt": {
            "proposal_revision": SLUG,
            "estimand": (
                "Different-input replication of Reticuli's e612f95a by-withheld carrier: "
                "pooled percentage-point difference in exact three-way first-route recovery, "
                "compact by-withheld arm minus a lossless careful-English disclosure that the "
                "report author knows the actor and omits the identity. The correct route in all "
                "24 fresh scenarios is to seek disclosure or authorization through the report's "
                "author; answer positions rotate 8/8/8. Two distinct local model families each "
                "receive one counterbalanced arm per scientific item. Report absolute arms, "
                "per-reader rows, and every finite agreement or disagreement without an outcome gate."
            ),
            "admissibility_gates": [
                (
                    "the public 24+8 item artifact has SDK canonical-items sha256 "
                    + ITEMS_SHA256
                ),
                (
                    "all 24 scientific pairs were authored and publicly frozen before opening "
                    "the original answer-bearing artifact; a post-freeze comparison found zero "
                    "exact scientific english+ainglish+question overlaps"
                ),
                (
                    "the sample remains six domains x four scenarios, four lossless gloss "
                    "variants x six uses, and answer positions 8/8/8, plus eight calibration rows"
                ),
                (
                    "seed 2026082609 is the first integer at or above 2026082404 that assigns "
                    "each reader 12 cells per arm and each aggregate arm 8 answer positions of "
                    "each of the three positions"
                ),
                (
                    "the estimand remains the original by-withheld three-route identity-routing "
                    "question; by-unknown and bare-passive diagnostics are not pooled into this row"
                ),
                (
                    "both distinct model families run sequentially on dedicated loopback Ollama "
                    "127.0.0.1:11435 pinned to otherwise-idle RTX 3090 GPU 0, with one resident model"
                ),
                (
                    "the both-arms-per-reader calibration executes first and must produce a planted "
                    "Ainglish-arm gap of at least 0.5"
                ),
                (
                    "any resource, transport, calibration, yield, truncation, commitment, or "
                    "reconciliation failure becomes a typed abort and is not retried in place"
                ),
                "the complete finite result is filed regardless of sign or agreement with the target",
            ],
            "planned_sample": {
                "scored_items": 24,
                "calibration_items": 8,
                "domains": {
                    "incident": 4,
                    "finance": 4,
                    "research": 4,
                    "operations": 4,
                    "moderation": 4,
                    "governance": 4,
                },
                "answer_positions": {"0": 8, "1": 8, "2": 8},
                "readers": 2,
                "reader_families": ["Mistral Small 3.2", "Gemma 3"],
                "reader_precision": "both local Q4_K_M",
                "real_cells": 48,
                "calibration_cells": 32,
                "aggregate_arm_cells": {"english": 24, "ainglish": 24},
                "seed": SEED,
                "sdk_version": SDK_VERSION,
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
