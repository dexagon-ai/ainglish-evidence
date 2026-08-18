#!/usr/bin/env python3
"""Build immutable-input SDK 0.2.32 runspecs before reader calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FREEZE_COMMIT = "73eff3cbfdd63e2c5a193c0583e2b7b0ca1643c9"
FREEZE_RELEASE = "will-force-freeze-20260817"
SLUG = "will-as-promise-will-as-plan-will-as-forecast-mark-whether-a-2"
MODEL = "dexagon-qwen3.5-27b-choice:ctx4k"
MODEL_DIGEST = "adaeda2ee3194b25537f12b93b6c3ceb31217cba68ab0e593fb2bf90703da116"
MODELFILE = ROOT / "Modelfile.qwen35-choice-ctx4k"
BASE_URL = "http://127.0.0.1:11435/v1"


def load_document(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def reader() -> dict:
    return {
        "name": "qwen3.5-27b-choice-q4_k_m",
        "provider": "ollama",
        "model": MODEL,
        "model_digest": MODEL_DIGEST,
        "precision": "q4_k_m",
        "max_tokens": 1024,
        "temperature": 0,
        "seed": 20260817,
        "api": "openai",
        "base_url": BASE_URL,
    }


def item_url(name: str) -> str:
    return (
        "https://github.com/dexagon-ai/ainglish-evidence/releases/download/"
        f"{FREEZE_RELEASE}/{name}"
    )


def commit_item_url(name: str) -> str:
    return (
        "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
        f"{FREEZE_COMMIT}/will-force-original-2026-08-17/{name}"
    )


def comprehension() -> dict:
    document = load_document("comprehension-careful-items.json")
    return {
        "construct": "will-as-promise / will-as-plan / will-as-forecast",
        "slug": SLUG,
        "metric": "comprehension_accuracy_delta",
        "seed": 20260817,
        "planted_arm": "ainglish",
        "calibration_min_gap": 0.5,
        "panel_neff": 1,
        "panel": [reader()],
        "items_url": commit_item_url("comprehension-careful-items.json"),
        "items_sha256": document["sha256"],
        "attempt": {
            "proposal_revision": SLUG,
            "estimand": (
                "Comprehension accuracy difference in percentage points between three marked "
                "future-force forms and their complete careful-English mappings on 36 held-out "
                "force-identification items, equally weighted across promise, plan and forecast. "
                "The score tests recognition of outcome responsibility, present intention, or "
                "expectation only. It does not score agreement with the separate will-as-plan "
                "notice-duty convention; marked-versus-bare performance is a separate diagnostic."
            ),
            "admissibility_gates": [
                (
                    "the commit-pinned content-addressed item array hashes to " + document["sha256"]
                    + "; it contains 36 scientific rows and 12 calibration rows"
                ),
                (
                    "scientific rows contain exactly 12 examples per form and 12 answers per "
                    "force class; option order is deterministically rotated; forecast rows name "
                    "events the speaker does not control"
                ),
                (
                    "the marked arm is compared only with its complete careful-English mapping; "
                    "untyped bare will is excluded from the filed carrier so a large bare-arm gain "
                    "cannot conceal inferiority to careful English"
                ),
                (
                    "the 12 construct-free calibration rows execute first in both arms and must "
                    "show an explicit-minus-untyped accuracy gap of at least 0.5"
                ),
                (
                    "force identification is the scored semantic claim; the will-as-plan duty to "
                    "notify on revision remains separately published as a non-scoring diagnostic"
                ),
                (
                    "one Qwen 3.5 27B Q4_K_M reader executes at temperature 0 and fixed seed on a "
                    "dedicated GPU-0 Ollama endpoint with a 4,096-token context"
                ),
                (
                    "the reader model must be fully resident on one RTX 3090 before attempt mint; "
                    "CPU fallback and a contested GPU are prohibited"
                ),
                (
                    "all null, adverse and supportive scientific outcomes are retained; only input, "
                    "transport, calibration, yield, commitment or GPU-contract failures may abort"
                ),
            ],
            "planned_sample": {
                "real_items": 36,
                "calibration_items": 12,
                "forms": {
                    "will-as-promise": 12,
                    "will-as-plan": 12,
                    "will-as-forecast": 12,
                },
                "comparison": "marked forms versus complete careful-English mappings",
                "noninferiority_margin_pp_per_form": -5,
                "force_answers": {
                    "outcome_responsibility": 12,
                    "present_intention": 12,
                    "expectation_only": 12,
                },
                "reader": "Qwen 3.5 27B Q4_K_M",
                "panel_neff": 1,
                "model_file_sha256": hashlib.sha256(MODELFILE.read_bytes()).hexdigest(),
                "execution": "dedicated local RTX 3090 GPU 0; full GPU residency; no CPU fallback",
            },
        },
    }


def robustness() -> dict:
    document = load_document("robustness-items.json")
    calibration = load_document("robustness-calibration.json")["items"]
    corruption = load_document("corruption-freeze-receipt.json")
    return {
        "construct": "will-as-promise / will-as-plan / will-as-forecast",
        "slug": SLUG,
        "metric": "robustness_delta",
        "seed": corruption["seed"],
        "planted_arm": "ainglish",
        "calibration_min_gap": 0.5,
        "panel_neff": 1,
        "panel": [reader()],
        "items_url": item_url("robustness-items.json"),
        "items_sha256": document["sha256"],
        "calibration_items": calibration,
        "corruption": {"channel": "corrupt_char"},
        "attempt": {
            "proposal_revision": SLUG,
            "estimand": (
                "SDK robustness_delta v4 for force recognition under one deterministic character "
                "corruption per arm: marked will-as-* minus its complete careful-English mapping. "
                "The frozen deal is an exposure-enriched carrier stress test, not an estimate of "
                "ambient error prevalence; censored and uncensored differentials both travel."
            ),
            "admissibility_gates": [
                (
                    "the 24-row content-addressed item array hashes to " + document["sha256"]
                    + " and remains balanced at eight rows per form"
                ),
                (
                    "the deterministic corrupt_char seed is " + str(corruption["seed"])
                    + "; its public zero-reader receipt records 13 English carrier hits, "
                    "14 marked-form carrier hits and 6 paired hits across all three forms"
                ),
                (
                    "each English arm spells out the form's complete accountability mapping; "
                    "this comparison does not use ambiguous bare will as a robustness baseline"
                ),
                (
                    "the 12 construct-free calibration rows execute first in both arms and must "
                    "show an explicit-minus-untyped accuracy gap of at least 0.5"
                ),
                (
                    "SDK v4 complete-quartet scoring, per-item chance-floor censoring, the "
                    "uncensored twin and resample-down diagnostics remain unchanged"
                ),
                (
                    "one Qwen 3.5 27B Q4_K_M reader executes at temperature 0 and fixed seed on a "
                    "dedicated GPU-0 Ollama endpoint with a 4,096-token context"
                ),
                (
                    "the reader model must be fully resident on one RTX 3090 before attempt mint; "
                    "CPU fallback and a contested GPU are prohibited"
                ),
                (
                    "all null, adverse and supportive scientific outcomes are retained; only input, "
                    "transport, calibration, yield, commitment or GPU-contract failures may abort"
                ),
            ],
            "planned_sample": {
                "real_items": 24,
                "calibration_items": 12,
                "forms": {
                    "will-as-promise": 8,
                    "will-as-plan": 8,
                    "will-as-forecast": 8,
                },
                "real_cells": 96,
                "calibration_cells": 24,
                "reader": "Qwen 3.5 27B Q4_K_M",
                "panel_neff": 1,
                "channel": "corrupt_char",
                "carrier_hits": corruption["counts"],
                "model_file_sha256": hashlib.sha256(MODELFILE.read_bytes()).hexdigest(),
                "execution": "dedicated local RTX 3090 GPU 0; full GPU residency; no CPU fallback",
            },
        },
    }


def main() -> None:
    outputs = {
        "runspec-comprehension.json": comprehension(),
        "runspec-robustness.json": robustness(),
    }
    receipts = {}
    for name, spec in outputs.items():
        path = ROOT / name
        path.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        receipts[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    print(json.dumps(receipts, indent=2))


if __name__ == "__main__":
    main()
