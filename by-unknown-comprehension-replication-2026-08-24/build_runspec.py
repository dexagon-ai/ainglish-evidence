#!/usr/bin/env python3
"""Build the immutable panel runspec without reader or governance calls."""

from __future__ import annotations

import collections
import hashlib
import json
from pathlib import Path

from ainglish.panel import arm_for


ROOT = Path(__file__).resolve().parent
ITEMS = ROOT / "items.json"
OUT = ROOT / "runspec-gpu0.json"
BASE_SEED = 2026082417
SEED = 2026083103
SDK_VERSION = "0.2.35"
ITEMS_COMMIT = "4882a6bf7fede7c1019b09313c80e0dac4222085"
ITEMS_SHA256 = "21396eaa6dd0593c767b79f0da4c6f8f2063303229d87a4bacbdcf2d01abd5cb"
ORIGINAL_ITEMS_SHA256 = "4865276dd1616fc4464c008fb23f728431da283b931f9a7834d3f63b0e8ac2cf"
TARGET = "655d6a115d0d37abd110cd65ac0c251d9c56cc51f7de8775694f20fa0f8fa05e"
SLUG = "by-unknown-by-withheld-typed-doer-omission-why-mistakes-were-3"
READERS = [
    "mistral-small3.2-24b-route-task-q4_k_m-v2",
    "gemma3-12b-route-task-q4_k_m-v2",
]


def first_balanced_seed(real: list[dict]) -> int:
    for seed in range(BASE_SEED, SEED + 1):
        per_reader = {
            reader: collections.Counter(arm_for(seed, reader, item["id"]) for item in real)
            for reader in READERS
        }
        positions = collections.Counter(
            (arm_for(seed, reader, item["id"]), item["options"].index(item["answer"]))
            for reader in READERS
            for item in real
        )
        if all(
            counts == collections.Counter({"english": 12, "ainglish": 12})
            for counts in per_reader.values()
        ) and all(
            positions[(arm, position)] == 8
            for arm in ("english", "ainglish")
            for position in range(3)
        ):
            return seed
    raise SystemExit("REFUSING: no balanced assignment seed found")


def main() -> None:
    document = json.loads(ITEMS.read_text())
    rows = document["items"]
    digest = hashlib.sha256(json.dumps(
        rows, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode()).hexdigest()
    if digest != ITEMS_SHA256 or document.get("sha256") != ITEMS_SHA256:
        raise SystemExit("REFUSING: frozen item digest mismatch")
    real = [item for item in rows if not item.get("calibration")]
    calibration = [item for item in rows if item.get("calibration")]
    if len(real) != 24 or len(calibration) != 8:
        raise SystemExit("REFUSING: frozen 24+8 sample changed")
    if first_balanced_seed(real) != SEED:
        raise SystemExit("REFUSING: declared assignment seed is not the first balanced seed")

    runspec = {
        "construct": "by-unknown",
        "slug": SLUG,
        "metric": "comprehension_accuracy_delta",
        "seed": SEED,
        "planted_arm": "ainglish",
        "calibration_min_gap": 0.5,
        "panel_neff": 2,
        "panel": [
            {
                "name": READERS[0],
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
                "name": READERS[1],
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
            f"{ITEMS_COMMIT}/by-unknown-comprehension-replication-2026-08-24/items.json"
        ),
        "items_sha256": ITEMS_SHA256,
        "replicates_hash": TARGET,
        "attempt": {
            "proposal_revision": SLUG,
            "estimand": (
                "Different-input replication of Reticuli's 655d6a11 by-unknown carrier: "
                "pooled percentage-point difference in exact three-way first-route recovery, "
                "compact by-unknown arm minus a lossless careful-English disclosure that the "
                "report author cannot identify the actor and that independent records or traces "
                "are the first route. The correct route in all 24 fresh scenarios is to search "
                "records or traces independently of the report's author; answer positions rotate "
                "8/8/8. Two distinct local model families each receive one counterbalanced arm "
                "per scientific item. Report absolute arms, per-reader rows, and every finite "
                "agreement or disagreement without an outcome gate."
            ),
            "admissibility_gates": [
                (
                    "the public 24+8 item artifact has SDK canonical-items sha256 "
                    + ITEMS_SHA256
                ),
                (
                    "all 24 scientific pairs were authored and publicly frozen at commit "
                    + ITEMS_COMMIT
                    + " before the original answer-bearing carrier was downloaded"
                ),
                (
                    "the post-freeze audit pins original canonical-items sha256 "
                    + ORIGINAL_ITEMS_SHA256
                    + " and finds zero exact scientific triples, arm pairs, or item IDs"
                ),
                (
                    "the sample remains six domains x four scenarios, four lossless gloss "
                    "variants x six uses, and answer positions 8/8/8, plus eight calibration rows"
                ),
                (
                    "seed 2026083103 is the first integer at or above 2026082417 that assigns "
                    "each reader 12 cells per arm and each aggregate arm 8 answer positions of "
                    "each of the three positions"
                ),
                (
                    "the estimand remains the original by-unknown three-route identity-routing "
                    "question; by-withheld and bare-passive diagnostics are not pooled into this row"
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
                    "cybersecurity": 4,
                    "health-operations": 4,
                    "civic-services": 4,
                    "inventory": 4,
                    "education": 4,
                    "energy": 4,
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
