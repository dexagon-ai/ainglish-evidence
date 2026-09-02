#!/usr/bin/env python3
"""Bind the published carrier to readers and a mint-before-spend contract."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_COMMIT = "a69aa92076b6b48c56bca84afb8967d1c50dceac"
TARGET = "7200b1736f5a760108c5f5305109d2a53f5c5b3415e3ff96bfa87ea389b5ff51"
SLUG = "go-unless-no-t-hold-until-yes-say-what-the-addressee-s-silen"
SDK_VERSION = "0.2.48"
SEED = 2026090229
READERS = [
    {
        "name": "mistral-small3.2-24b-opaque-choice-q4_k_m",
        "provider": "ollama",
        "model": "dexagon-mistral-small3.2-24b-pp-task:ctx4k",
        "model_digest": "sha256:6629ee92de51c9a1367e1331cfa9ef6a77058a44a6a3e18ab524b2d0404252de",
        "precision": "q4_k_m", "api": "openai", "base_url": "http://127.0.0.1:11434/v1",
        "max_tokens": 32, "timeout_s": 120, "temperature": 0, "seed": SEED,
    },
    {
        "name": "gemma3-12b-opaque-choice-q4_k_m",
        "provider": "ollama",
        "model": "dexagon-gemma3-12b-pp-task:ctx4k",
        "model_digest": "sha256:de1f65ea3438dfcc7c3387802b9425a140fb01ecc79edf4924a13fab051eb68f",
        "precision": "q4_k_m", "api": "openai", "base_url": "http://127.0.0.1:11434/v1",
        "max_tokens": 32, "timeout_s": 120, "temperature": 0, "seed": SEED,
    },
]


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def main() -> None:
    index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    audit = json.loads((ROOT / "audit.json").read_text(encoding="utf-8"))
    assert audit["items_sha256"] == index["items_sha256"] and audit["exact_pair_overlaps"] == 0
    spec = {
        "kind": "dexagon.ainglish.go-hold-dispute-runspec.v1",
        "construct": "go-unless-no(<t>) / hold-until-yes",
        "slug": SLUG,
        "metric": "comprehension_accuracy_delta",
        "replicates_hash": TARGET,
        "seed": SEED,
        "planted_arm": "ainglish",
        "calibration_min_gap": 0.5,
        "panel_neff": 2,
        "panel": READERS,
        "comparator": {
            "kind": "complete-careful-english-v1",
            "description": "Each marker is compared only with the proposal's complete silence-rule mapping; no bare ambiguous closing enters the scalar.",
        },
        "settlement_strata": [
            {"id": "go-unless-no", "weight": 1},
            {"id": "hold-until-yes", "weight": 1},
        ],
        "training_asymmetry": "The readers were trained primarily on ordinary English and are not assumed to have seen Ainglish. This is present zero-shot evidence, not a forecast after Ainglish-aware training.",
        "items_url": f"https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{SOURCE_COMMIT}/dispute-settlement-go-hold-v1-2026-09-02/items.json",
        "items_sha256": index["items_sha256"],
        "source": {
            "repository": "dexagon-ai/ainglish-evidence", "commit": SOURCE_COMMIT,
            "path": "dispute-settlement-go-hold-v1-2026-09-02/items.json",
        },
        "attempt": {
            "proposal_revision": SLUG,
            "estimand": "Fresh-input replication of the original percentage-point exact consequence accuracy difference, registered go-unless-no(<t>) / hold-until-yes form minus its complete careful-English mapping, over 48 frozen items: 24 per form and, within each form, 12 silent and 12 replying exchanges. The headline is the equal-weight mean of the two separately reported form strata.",
            "admissibility_gates": [
                f"authenticated suggestions still offer {TARGET} as a confirmation-capable replication immediately before mint",
                "the proposal remains current at measured stage and its claim-carrier work still names this exact target",
                f"the published 60-item array hashes to {index['items_sha256']}",
                "the scientific carrier contains exactly 24 items per form and exactly 12 silent plus 12 replying cases within each form",
                "all 60 complete pairs are unique and overlap none of the 58 exact prior served pairs audited at freeze time",
                "every scientific English arm states the complete registered careful-English mapping and answer vocabulary is absent from both arms",
                "both named reader artifacts match their declared Ollama digests and receive no repository, register, retrieval, or conversation context",
                "construct-free planted calibration runs in both arms for each reader before scientific exposure and must clear a 0.5 accuracy gap",
                "zero transport loss or truncation and complete reader-cell yield are required; no automatic retries are allowed",
                "every finite supportive, null, adverse, floor-bound, ceiling-bound, or further-disputing result is filed exactly once",
            ],
            "planned_sample": {
                "metric": "comprehension_accuracy_delta", "scientific_items": 48,
                "calibration_items": 12, "forms": {"go-unless-no": 24, "hold-until-yes": 24},
                "response_kind_within_each_form": {"silent": 12, "replying": 12},
                "readers": 2, "reader_families": ["Mistral Small 3.2 24B", "Gemma 3 12B"],
                "panel_neff": 2, "real_cells": 96, "calibration_cells": 48,
                "sdk_version": SDK_VERSION, "source_commit": SOURCE_COMMIT,
                "replicates_hash": TARGET,
            },
        },
    }
    spec["content_sha256"] = sha256(canonical(spec)).hexdigest()
    (ROOT / "runspec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"kind": spec["kind"], "content_sha256": spec["content_sha256"], "model_calls": 0}, indent=2))


if __name__ == "__main__":
    main()
