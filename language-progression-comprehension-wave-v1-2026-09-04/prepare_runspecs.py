#!/usr/bin/env python3
"""Bind the published carriers to the existing qualified reader artifacts."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_COMMIT = "bef3db880b651417da575ea9190a51e8029d0ebd"
SDK_VERSION = "0.2.52"
READERS = [
    {
        "name": "mistral-small3.2-24b-opaque-choice-q4_k_m",
        "provider": "ollama",
        "model": "dexagon-mistral-small3.2-24b-pp-task:ctx4k",
        "model_digest": "sha256:6629ee92de51c9a1367e1331cfa9ef6a77058a44a6a3e18ab524b2d0404252de",
        "precision": "q4_k_m",
        "api": "openai",
        "base_url": "http://127.0.0.1:11434/v1",
        "max_tokens": 32,
        "timeout_s": 120,
        "temperature": 0,
    },
    {
        "name": "gemma3-12b-opaque-choice-q4_k_m",
        "provider": "ollama",
        "model": "dexagon-gemma3-12b-pp-task:ctx4k",
        "model_digest": "sha256:de1f65ea3438dfcc7c3387802b9425a140fb01ecc79edf4924a13fab051eb68f",
        "precision": "q4_k_m",
        "api": "openai",
        "base_url": "http://127.0.0.1:11434/v1",
        "max_tokens": 32,
        "timeout_s": 120,
        "temperature": 0,
    },
]


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def main() -> None:
    index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    runspecs = {}
    for offset, (name, meta) in enumerate(index["campaigns"].items(), 1):
        seed = 2026090400 + offset
        readers = [{**reader, "seed": seed} for reader in READERS]
        strata = meta["settlement_strata"]
        spec = {
            "kind": "dexagon.ainglish.language-progression-comprehension-runspec.v1",
            "construct": meta["construct"],
            "public_id": meta["public_id"],
            "slug": meta["slug"],
            "metric": "comprehension_accuracy_delta",
            "seed": seed,
            "planted_arm": "ainglish",
            "calibration_min_gap": 0.5,
            "panel_neff": 2,
            "panel": readers,
            "comparator": {
                "kind": "complete-careful-english-v1",
                "description": "Each compact form is compared with its complete careful-English meaning; bare ambiguity is absent from the scalar.",
            },
            "comparison_identity": {
                "comparator_genre": "complete-careful-English-v1",
                "pair_rendering": "held-out exact consequence question",
                "reader_roster": [reader["name"] for reader in readers],
                "form_strata": [row["id"] for row in strata],
            },
            "settlement_strata": strata,
            "training_asymmetry": index["training_asymmetry"],
            "items_url": f"https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{SOURCE_COMMIT}/language-progression-comprehension-wave-v1-2026-09-04/{meta['file']}",
            "items_sha256": meta["items_sha256"],
            "source": {
                "repository": "dexagon-ai/ainglish-evidence",
                "commit": SOURCE_COMMIT,
                "path": f"language-progression-comprehension-wave-v1-2026-09-04/{meta['file']}",
            },
            "attempt": {
                "proposal_revision": meta["slug"],
                "estimand": f"Percentage-point exact-answer accuracy difference, registered compact form minus complete careful-English mapping, over {meta['scientific_items']} frozen items for {meta['construct']}; equal-weight mean of the separately reported strata ({', '.join(row['id'] for row in strata)}). Interpret non-inferiority at -5 percentage points; retain absolute arms, per-reader results, intervals, calibration, yield and every stratum.",
                "admissibility_gates": [
                    "authenticated suggestions and a fresh proposal read still request this exact original comprehension_accuracy_delta immediately before mint",
                    "the executing principal is not the proposal's proposer and has not already filed this original",
                    f"the published answer-bearing array hashes to {meta['items_sha256']} and contains exactly {meta['scientific_items']} scientific plus {meta['calibration_items']} calibration items",
                    "every English arm states the complete careful meaning; bare ambiguous English does not enter the scalar",
                    "both local reader artifacts match the declared Ollama digests and run statelessly at temperature 0 with the frozen seed",
                    "construct-free calibration executes first and must show an explicit-minus-unresolved gap of at least 0.5 for each reader",
                    "every form stratum remains separately visible and carries equal weight in the primary estimand",
                    "no reader receives repository access, retrieval, conversation history or a register definition beyond the presented cell",
                    "zero response-bound truncations and full cell yield are required; transport or format failure produces a typed abort without retry",
                    "every finite supportive, adverse or null result is filed exactly once",
                    "a settlement-bearing replication requires a different principal and wholly fresh complete items",
                ],
                "planned_sample": {
                    "comparison": "registered compact form versus complete careful-English mapping",
                    "scientific_items": meta["scientific_items"],
                    "calibration_items": meta["calibration_items"],
                    "readers": len(readers),
                    "reader_families": ["Mistral Small 3.2 24B", "Gemma 3 12B"],
                    "panel_neff": 2,
                    "real_cells": meta["scientific_items"] * len(readers),
                    "calibration_cells": meta["calibration_items"] * len(readers) * 2,
                    "settlement_strata": meta["stratum_counts"],
                    "noninferiority_margin_pp": -5,
                    "sdk_version": SDK_VERSION,
                    "source_commit": SOURCE_COMMIT,
                },
            },
        }
        spec["content_sha256"] = sha256(canonical(spec)).hexdigest()
        path = ROOT / f"runspec-{name}.json"
        path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        runspecs[name] = {"file": path.name, "content_sha256": spec["content_sha256"]}
    output = {
        "kind": "dexagon.ainglish.language-progression-comprehension-runspec-index.v1",
        "source_commit": SOURCE_COMMIT,
        "sdk_version": SDK_VERSION,
        "runspecs": runspecs,
        "model_calls": 0,
    }
    output["content_sha256"] = sha256(canonical(output)).hexdigest()
    (ROOT / "runspec-index.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
