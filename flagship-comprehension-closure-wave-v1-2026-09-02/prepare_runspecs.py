#!/usr/bin/env python3
"""Bind the published carriers to exact readers and preregistration contracts."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_COMMIT = "d3545ec78b4c7658f3296ced80ff47a22c722529"
SDK_VERSION = "0.2.48"
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
    for offset, (name, meta) in enumerate(index["campaigns"].items(), start=1):
        seed = 2026090200 + offset
        readers = [{**reader, "seed": seed} for reader in READERS]
        strata = meta["settlement_strata"]
        is_handoff = name == "retention-policy"
        spec = {
            "kind": "dexagon.ainglish.flagship-comprehension-closure-runspec.v1",
            "construct": meta["construct"],
            "slug": meta["slug"],
            "metric": "comprehension_accuracy_delta",
            "seed": seed,
            "planted_arm": "ainglish",
            "calibration_min_gap": 0.5,
            "panel_neff": 2,
            "panel": readers,
            "comparator": {
                "kind": "complete-careful-english-v1",
                "description": "Every scientific compact form is compared with its complete registered careful-English meaning; ambiguous bare English is absent from the scalar.",
            },
            "comparison_identity": {
                "comparator_genre": "complete-careful-English-v1",
                "pair_rendering": "held-out exact consequence question",
                "reader_roster": [reader["name"] for reader in readers],
                "form_strata": [row["id"] for row in strata],
            },
            "settlement_strata": strata,
            "training_asymmetry": "The named readers were trained primarily on ordinary English and are not assumed to have seen Ainglish. This is present zero-shot transparency evidence, not a forecast of performance after future Ainglish-aware training.",
            "items_url": f"https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{SOURCE_COMMIT}/flagship-comprehension-closure-wave-v1-2026-09-02/{meta['file']}",
            "items_sha256": meta["items_sha256"],
            "source": {
                "repository": "dexagon-ai/ainglish-evidence",
                "commit": SOURCE_COMMIT,
                "path": f"flagship-comprehension-closure-wave-v1-2026-09-02/{meta['file']}",
            },
            "attempt": {
                "proposal_revision": meta["slug"],
                "estimand": f"Percentage-point exact-answer accuracy difference, registered compact form minus complete careful-English mapping, over {meta['scientific_items']} frozen fresh items for {meta['construct']}; equal-weight mean of the separately reported form strata ({', '.join(row['id'] for row in strata)}). Primary interpretation is non-inferiority at -5 percentage points; absolute arms, per-reader results, intervals, calibration, yield, and every stratum remain visible.",
                "admissibility_gates": [
                    f"the live proposal remains current at measured stage and still names an original comprehension_accuracy_delta as its primary evidence-completion action immediately before mint",
                    f"the published answer-bearing item array hashes to {meta['items_sha256']} and contains exactly {meta['scientific_items']} scientific plus {meta['calibration_items']} calibration items",
                    "every scientific English arm states the complete registered careful-English meaning; no bare ambiguous comparator enters the scalar",
                    "both named local reader artifacts match their declared Ollama digests and run statelessly at temperature 0 with the frozen seed and opaque-choice output",
                    "the construct-free planted-effect calibration executes first in both arms for each reader and must show an explicit-minus-unresolved accuracy gap of at least 0.5",
                    "each real item names one committed equal-weight settlement stratum, and every form remains separately visible",
                    "no reader receives repository access, retrieval, conversation history, or a register definition beyond the presented cell",
                    "zero response-bound truncations and a passing full-cell-yield guard are required; transport or format failure produces a typed abort and no retry",
                    "every finite supportive, adverse, null, floor-bound, or ceiling-bound outcome is filed exactly once",
                    "a settlement-bearing replication must come from a different principal with a wholly fresh complete item manifest",
                ] + (["the filing principal is not the proposal's original proposer; this Dexagon-authored package is handoff-only"] if is_handoff else []),
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
                    "handoff_only": is_handoff,
                },
            },
        }
        spec["content_sha256"] = sha256(canonical(spec)).hexdigest()
        path = ROOT / f"runspec-{name}.json"
        path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        runspecs[name] = {"file": path.name, "content_sha256": spec["content_sha256"], "handoff_only": is_handoff}
    output = {"kind": "dexagon.ainglish.flagship-comprehension-closure-runspec-index.v1", "source_commit": SOURCE_COMMIT, "sdk_version": SDK_VERSION, "runspecs": runspecs, "model_calls": 0}
    output["content_sha256"] = sha256(canonical(output)).hexdigest()
    (ROOT / "runspec-index.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
