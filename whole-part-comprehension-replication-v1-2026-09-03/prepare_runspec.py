#!/usr/bin/env python3
"""Bind the frozen whole/part carrier to the installed qualified Qwen reader."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE_COMMIT = "fc8a1f201f620dcec28ef017b428af71c0ebfa59"
TARGET = "b82c72bdd55e65280aa65a9085197c2a389658c3ef99d44567ba47f01c4ccb8b"
SLUG = "whole-s-part-s-declare-whether-a-reported-set-is-the-complet"
SDK_VERSION = "0.2.50"
SEED = 2026090337
READER = {
    "name": "qwen3.6-35b-qualified-general-q4_k_m",
    "provider": "ollama",
    "model": "qwen3.6:35b",
    "model_digest": "sha256:07d35212591fc27746f0a317c975a6d68754fb38e9053d82e25f06057af28522",
    "precision": "q4_k_m",
    "api": "openai",
    "base_url": "http://127.0.0.1:11434/v1",
    "max_tokens": 32,
    "timeout_s": 180,
    "temperature": 0,
    "seed": SEED,
}


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def main() -> None:
    index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    audit = json.loads((ROOT / "audit.json").read_text(encoding="utf-8"))
    assert audit["passed"] and audit["items_sha256"] == index["items_sha256"]
    spec = {
        "kind": "dexagon.ainglish.whole-part-comprehension-replication-runspec.v1",
        "construct": "whole(<S>) / part(<S>)",
        "slug": SLUG,
        "metric": "comprehension_accuracy_delta",
        "replicates_hash": TARGET,
        "seed": SEED,
        "planted_arm": "ainglish",
        "calibration_min_gap": 0.5,
        "panel_neff": 1,
        "panel": [READER],
        "comparator": {
            "kind": "complete-careful-english-v1",
            "description": (
                "Every part arm states that the inspected set is a subset with unseen in-scope "
                "members; every whole arm states that it is the entire in-scope population."
            ),
        },
        "training_asymmetry": (
            "The reader was trained primarily on ordinary English and is not assumed to have "
            "seen Ainglish. This is present zero-shot evidence for this exact reader, not a "
            "forecast of comprehension after future Ainglish-aware training."
        ),
        "reader_qualification": {
            "artifact": "reader-qualification-v8-2026-08-26/selected-result.json",
            "holdout_result": "61/64 overall with every axis at least 7/8, exact schema 64/64",
            "scope": (
                "The Qwen lineage individually passed the frozen general reader gates. A second "
                "lineage did not, so this run declares panel_neff=1 and makes no cross-lineage claim."
            ),
        },
        "items_url": (
            "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
            f"{SOURCE_COMMIT}/whole-part-comprehension-replication-v1-2026-09-03/items.json"
        ),
        "items_sha256": index["items_sha256"],
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "commit": SOURCE_COMMIT,
            "path": "whole-part-comprehension-replication-v1-2026-09-03/items.json",
        },
        "attempt": {
            "proposal_revision": SLUG,
            "estimand": (
                "Fresh-input replication of the percentage-point exact consequence accuracy "
                "difference, registered whole(S)/part(S) population-coverage marker minus its "
                "complete careful-English mapping, over 48 frozen matched items: 24 per form "
                "and 16 per coverage probe. The unstratified headline preserves the target's "
                "measurement contract; per-form labels remain descriptive diagnostics."
            ),
            "admissibility_gates": [
                f"authenticated suggestions still offer {TARGET} as executable and confirmation-capable immediately before mint",
                "the proposal remains current and its progression action still names comprehension replication",
                f"the published 56-item array hashes to {index['items_sha256']}",
                "the carrier contains exactly 24 part and 24 whole scientific items plus 8 construct-free calibration items",
                "every complete pair is unique and overlaps none of the target's 124 served pairs",
                "each scientific English arm states the proposal's complete careful-English population mapping",
                "the installed Qwen artifact matches its declared Ollama digest and receives no register, repository, retrieval or conversation context",
                "the single reader previously passed the frozen general qualification gates; panel_neff is honestly one",
                "construct-free calibration runs in both arms before scientific exposure and must clear a 0.5 accuracy gap",
                "zero transport loss or truncation and complete reader-cell yield are required; no automatic retries are allowed",
                "every finite supportive, null, adverse, floor-bound, ceiling-bound or disputing result is filed exactly once",
            ],
            "planned_sample": {
                "metric": "comprehension_accuracy_delta",
                "scientific_items": 48,
                "calibration_items": 8,
                "forms": {"part": 24, "whole": 24},
                "coverage_probes": {"coverage-1": 16, "coverage-2": 16, "coverage-3": 16},
                "readers": 1,
                "reader_families": ["Qwen 3.6 35B"],
                "panel_neff": 1,
                "real_cells": 48,
                "calibration_cells": 16,
                "sdk_version": SDK_VERSION,
                "source_commit": SOURCE_COMMIT,
                "replicates_hash": TARGET,
            },
        },
    }
    spec["content_sha256"] = sha256(canonical(spec)).hexdigest()
    (ROOT / "runspec.json").write_text(
        json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"kind": spec["kind"], "content_sha256": spec["content_sha256"], "model_calls": 0}, indent=2))


if __name__ == "__main__":
    main()
