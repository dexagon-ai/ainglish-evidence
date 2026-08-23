#!/usr/bin/env python3
"""Build the two unpooled claim-carrier run specifications."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SLUG = "some-or-all-some-but-not-all-does-some-leave-room-for-all-2"
READERS = [
    {
        "name": "mistral-small3.2-24b-pp-task-q4_k_m",
        "provider": "ollama",
        "model": "dexagon-mistral-small3.2-24b-pp-task:ctx4k",
        "model_digest": "sha256:6629ee92de51c9a1367e1331cfa9ef6a77058a44a6a3e18ab524b2d0404252de",
        "precision": "q4_k_m",
        "api": "openai",
        "base_url": "http://127.0.0.1:11434/v1",
        "max_tokens": 1024,
        "timeout_s": 120,
        "temperature": 0,
    },
    {
        "name": "gemma3-12b-pp-task-q4_k_m",
        "provider": "ollama",
        "model": "dexagon-gemma3-12b-pp-task:ctx4k",
        "model_digest": "sha256:de1f65ea3438dfcc7c3387802b9425a140fb01ecc79edf4924a13fab051eb68f",
        "precision": "q4_k_m",
        "api": "openai",
        "base_url": "http://127.0.0.1:11434/v1",
        "max_tokens": 1024,
        "timeout_s": 120,
        "temperature": 0,
    },
    {
        "name": "qwen3.5-27b-choice-q4_k_m",
        "provider": "ollama",
        "model": "dexagon-qwen3.5-27b-choice:ctx4k",
        "model_digest": "sha256:adaeda2ee3194b25537f12b93b6c3ceb31217cba68ab0e593fb2bf90703da116",
        "precision": "q4_k_m",
        "api": "openai",
        "base_url": "http://127.0.0.1:11434/v1",
        "max_tokens": 1024,
        "timeout_s": 120,
        "temperature": 0,
    },
]

CONFIG = {
    "some-or-all": {
        "seed": 2026112074,
        "items": "some_or_all-careful-items.json",
        "digest": "6e373343efe1070538575246efbad5dcdd3756cfb9048be2dd9a0a382d68da20",
        "vector": "zero is impossible and the full named set remains possible",
    },
    "some-but-not-all": {
        "seed": 2026140203,
        "items": "some_but_not_all-careful-items.json",
        "digest": "f785ef085fde9589f34fbe96f9c11dd7908a6bc04f72cd1cbfe1298092d47c38",
        "vector": "zero is impossible and the full named set is impossible",
    },
}


def run_spec(form: str) -> dict:
    config = CONFIG[form]
    return {
        "construct": "some-or-all / some-but-not-all",
        "slug": SLUG,
        "metric": "comprehension_accuracy_delta",
        "seed": config["seed"],
        "planted_arm": "ainglish",
        "calibration_min_gap": 0.5,
        "panel_neff": 3,
        "panel": [dict(reader, seed=config["seed"]) for reader in READERS],
        "items_url": str(ROOT / config["items"]),
        "items_sha256": config["digest"],
        "attempt": {
            "proposal_revision": SLUG,
            "estimand": (
                f"For {form} alone, the percentage-point difference in exact joint lower- and "
                "upper-bound recovery between the marked form and its complete careful-English "
                "mapping over 100 held-out, meaning-matched scenarios. The keyed vector says "
                f"{config['vector']}. This estimand is not pooled with the other form and does "
                "not use bare some as its confirmatory English arm."
            ),
            "admissibility_gates": [
                f"the frozen item array hashes to {config['digest']}; it contains exactly 100 real rows and 16 calibration rows",
                f"all real rows test {form} against its complete careful-English mapping; no bare-some comparator enters the claim carrier",
                "the answer requires exact joint recovery of independent lower and upper boundaries; question wording does not repeat the marker or its careful-English quantifiers",
                "the ten declared domains contribute exactly ten real rows each; endpoint and requirement question polarities contribute fifty each; each answer position occurs twenty-five times",
                "each of the three distinct reader lineages receives exactly fifty marked and fifty careful-English real cells under the frozen assignment seed; every domain supplies between three and seven marked cells per reader",
                "all three Q4_K_M reader artifacts must match their declared Ollama digests before attempt mint; temperature and reader seed are fixed and each model's 4,096-token context is baked into its digest-pinned Modelfile",
                "the construct-free calibration block executes first in both arms for every reader and must show an explicit-minus-unresolved accuracy gap of at least 0.5",
                "all null, adverse and supportive real outcomes are retained; only frozen-input, instrument-binding, calibration, cell-yield, transport, manifest-commitment, or GPU-contract failures may abort",
            ],
            "planned_sample": {
                "form": form,
                "comparison": "marked form versus complete careful-English mapping",
                "real_items": 100,
                "calibration_items": 16,
                "real_reader_cells": 300,
                "calibration_reader_cells": 96,
                "domains": 10,
                "question_polarities": {"endpoint": 50, "requirement": 50},
                "answer_positions": {"0": 25, "1": 25, "2": 25, "3": 25},
                "readers": [reader["name"] for reader in READERS],
                "reader_lineages": ["Mistral Small 3.2 24B", "Gemma 3 12B", "Qwen 3.5 27B"],
                "panel_neff": 3,
                "noninferiority_margin_pp": -5,
            },
        },
    }


def main() -> None:
    for form in CONFIG:
        path = ROOT / f"runspec-{form}.json"
        path.write_text(json.dumps(run_spec(form), indent=2) + "\n", encoding="utf-8")
        print(path)


if __name__ == "__main__":
    main()
