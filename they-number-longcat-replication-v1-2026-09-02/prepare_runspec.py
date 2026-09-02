#!/usr/bin/env python3
"""Bind the fresh they-number carrier to four exact local readers."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_COMMIT = "40e9996b55f608be54ed36db257906aefda097fa"
ORIGINAL = "261b02c6af43cebe30a2b25993a39912715910ab9d0decba323bc40449b7a92e"
READERS = [
    ("mistral-small3.2-24b-opaque-choice-q4_k_m", "dexagon-mistral-small3.2-24b-pp-task:ctx4k", "6629ee92de51c9a1367e1331cfa9ef6a77058a44a6a3e18ab524b2d0404252de", "Mistral Small 3.2 24B"),
    ("gemma3-12b-opaque-choice-q4_k_m", "dexagon-gemma3-12b-pp-task:ctx4k", "de1f65ea3438dfcc7c3387802b9425a140fb01ecc79edf4924a13fab051eb68f", "Gemma 3 12B"),
    ("phi4-14b-qualification-v5-q4_k_m", "dexagon-phi4-14b-qualification-v5:ctx4k", "d17fda064ee4320e183d31c9edf1bf395ff8cd0603f1ece2cfb0d5cfb44b7c44", "Phi-4 14B"),
    ("granite3.3-8b-qualification-v5-q4_k_m", "dexagon-granite3.3-8b-qualification-v5:ctx4k", "7c831da13fb0ca084c4c90846a123853d586ecc09a264586752c37057a273ffd", "Granite 3.3 8B"),
]


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def main() -> None:
    index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    seed = 2026090213
    panel = [{
        "name": name,
        "provider": "ollama",
        "model": model,
        "model_digest": f"sha256:{model_digest}",
        "precision": "q4_k_m",
        "api": "openai",
        "base_url": "http://127.0.0.1:11434/v1",
        "max_tokens": 32,
        "timeout_s": 120,
        "temperature": 0,
        "seed": seed,
    } for name, model, model_digest, _family in READERS]
    spec = {
        "kind": "dexagon.ainglish.they-number-longcat-replication-runspec.v1",
        "construct": "they-one / they-many",
        "slug": "they-one-they-many",
        "metric": "comprehension_accuracy_delta",
        "replicates_hash": ORIGINAL,
        "seed": seed,
        "planted_arm": "ainglish",
        "calibration_min_gap": 0.5,
        "panel_neff": 4,
        "panel": panel,
        "comparator": {
            "kind": "complete-careful-english-v1",
            "description": "Every number marker is compared with its complete careful-English meaning, including the material nonclaims.",
        },
        "comparison_identity": {
            "comparator_genre": "complete-careful-English-v1",
            "pair_rendering": "held-out operational number-consequence probes",
            "reader_roster": [reader["name"] for reader in panel],
            "aggregation": "one pooled aggregate preserving the legacy original's unstratified contract",
        },
        "training_asymmetry": (
            "The four reader lineages were trained primarily on ordinary English and are not assumed to have seen "
            "Ainglish. This is present zero-shot transparency evidence, not a forecast after future Ainglish-aware training."
        ),
        "items_url": (
            f"https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{SOURCE_COMMIT}/"
            "they-number-longcat-replication-v1-2026-09-02/items.json"
        ),
        "items_sha256": index["items_sha256"],
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "commit": SOURCE_COMMIT,
            "path": "they-number-longcat-replication-v1-2026-09-02/items.json",
        },
        "attempt": {
            "proposal_revision": "they-one-they-many",
            "estimand": (
                "Replication of comprehension_accuracy_delta formula v2 for they-one / they-many versus complete "
                "careful English on 128 wholly fresh operational consequence items. The two forms contribute 64 "
                "items each, and referent number, lower bound, one-actor sufficiency, and all-members nonclaim "
                "contribute 32 each. One pooled aggregate preserves the legacy original's unstratified contract; "
                "absolute arms use four local reader lineages at temperature 0."
            ),
            "admissibility_gates": [
                "the live proposal remains current at measured stage and the named original remains awaiting immediately before mint",
                f"the published answer-bearing item array hashes to {index['items_sha256']} and contains exactly 128 scientific plus 24 calibration items",
                "all 128 complete message pairs are wholly fresh relative to the original, with zero exact pair overlap audited before mint",
                "the carrier contains exactly 64 items per form and 32 items per semantic seam",
                "each compact arm is paired only with its complete careful-English mapping; the aggregate preserves the legacy original's unstratified contract",
                "all four named local reader artifacts match their declared Ollama digests and run statelessly at temperature 0 with the frozen seed and opaque-choice output",
                "the construct-free planted-effect calibration executes first in both arms for each reader and must show an explicit-minus-unresolved accuracy gap of at least 0.5",
                "no reader receives repository access, retrieval, conversation history, or a register definition beyond the presented cell",
                "zero response-bound truncations and a passing full-cell-yield guard are required; transport or format failure produces a typed abort and no retry",
                "every finite agreement, disagreement, supportive, adverse, null, floor-bound, or ceiling-bound result is filed exactly once",
            ],
            "planned_sample": {
                "metric": "comprehension_accuracy_delta",
                "replicates_hash": ORIGINAL,
                "scientific_items": 128,
                "calibration_items": 24,
                "forms": {"they-one": 64, "they-many": 64},
                "semantic_seams": {
                    "referent-number": 32,
                    "lower-bound": 32,
                    "single-sufficiency": 32,
                    "all-members-nonclaim": 32,
                },
                "readers": 4,
                "reader_families": [family for _name, _model, _digest, family in READERS],
                "panel_neff": 4,
                "real_cells": 512,
                "calibration_cells": 192,
                "source_commit": SOURCE_COMMIT,
                "sdk_version": "0.2.50",
            },
        },
    }
    spec["content_sha256"] = sha256(canonical(spec)).hexdigest()
    (ROOT / "runspec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"runspec": "runspec.json", "content_sha256": spec["content_sha256"], "model_calls": 0}, indent=2))


if __name__ == "__main__":
    main()

