#!/usr/bin/env python3
"""Bind the published should carrier to current qualified readers without inference."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT.parent


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_commit")
    args = parser.parse_args()
    commit = args.source_commit.strip().lower()
    subprocess.run(["git", "cat-file", "-e", f"{commit}:should-force-comprehension-original-v1-2026-09-04/items.json"], cwd=EVIDENCE, check=True)

    payload = json.loads((ROOT / "items.json").read_text(encoding="utf-8"))
    qualification_source = json.loads((EVIDENCE / "send-snapshot-live-view-comprehension-v1-2026-09-03" / "runspec-local-qualified.json").read_text(encoding="utf-8"))
    panel = [{**reader, "seed": 2026090411} for reader in qualification_source["panel"]]
    qualifications = qualification_source["reader_qualifications"]
    spec = {
        "kind": "dexagon.ainglish.should-force-qualified-local-runspec.v1",
        "construct": "should-as-rule / should-as-forecast",
        "public_id": "a-b0t3phkbfkk45e56",
        "slug": "should-as-rule-should-as-forecast-is-should-a-norm-or-an-exp",
        "metric": "comprehension_accuracy_delta",
        "seed": 2026090411,
        "planted_arm": "ainglish",
        "calibration_min_gap": 0.5,
        "panel_neff": 2,
        "panel": panel,
        "models": [row["roster_id"] for row in qualifications],
        "reader_qualifications": qualifications,
        "comparator": {
            "kind": "complete-careful-english-v1",
            "description": "each typed should form versus its full norm-or-expectation English meaning; bare should is excluded from the scalar",
        },
        "items_url": f"https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{commit}/should-force-comprehension-original-v1-2026-09-04/items.json",
        "items_sha256": payload["items_sha256"],
        "settlement_strata": [
            {"id": "should-as-rule", "weight": 1},
            {"id": "should-as-forecast", "weight": 1},
        ],
        "comparison_identity": {
            "comparator_genre": "complete-careful-English-v1",
            "pair_rendering": "held-out first-justified-response choice after non-occurrence",
            "reader_roster": [row["roster_id"] for row in qualifications],
            "form_strata": ["should-as-rule", "should-as-forecast"],
        },
        "training_asymmetry": "These readers were trained primarily on ordinary English and are not assumed to have seen Ainglish. This measures present zero-shot transparency, not expected performance after Ainglish-aware training.",
        "attempt": {
            "proposal_revision": "should-as-rule-should-as-forecast-is-should-a-norm-or-an-exp",
            "estimand": "Original comprehension claim carrier: equal-weight mean of separately reported should-as-rule and should-as-forecast percentage-point exact-answer differences, registered form minus complete careful-English meaning, over 100 balanced both-readings-live scenarios. Non-inferiority margin is -5 percentage points per stratum; retain absolute arms, interval, reader rows, calibration and yield.",
            "admissibility_gates": [
                "fresh authenticated personalized suggestions still request this exact original comprehension_accuracy_delta immediately before mint",
                "the fresh proposal remains current and the executing principal is not its proposer",
                "the 100 scientific plus 8 calibration items match the published content digest and preserve 50/50 form and complement balance",
                "no prior proposal measurement manifest contains this exact published item digest",
                "both local reader configurations retain passing unexpired target-independent qualification receipts and exact Ollama artifact digests",
                "construct-free calibration executes first and each reader shows an explicit-minus-unresolved gap of at least 0.5",
                "zero transport faults, response truncations, missing cells or retries are required",
                "both form strata, absolute arms, reader rows, replayable interval and normalized answers are retained",
                "every finite supportive, adverse, null, floor-bound, ceiling-bound or inconclusive result is filed exactly once",
            ],
            "planned_sample": {
                "metric": "comprehension_accuracy_delta",
                "comparison": "registered form versus complete careful-English meaning",
                "scientific_items": 100,
                "calibration_items": 8,
                "forms": {"should-as-rule": 50, "should-as-forecast": 50},
                "complements_per_form": {"agentive": 25, "stative": 25},
                "readers": 2,
                "reader_lineages": [row["lineage"]["key"] for row in qualifications],
                "panel_neff": 2,
                "real_cells": 200,
                "calibration_cells": 32,
                "noninferiority_margin_pp": -5,
                "sdk_version": "0.2.53",
                "items_commit": commit,
                "qualification_commit": "00226c0",
            },
        },
    }
    spec["content_sha256"] = sha256(canonical(spec)).hexdigest()
    (ROOT / "runspec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"content_sha256": spec["content_sha256"], "items_sha256": spec["items_sha256"], "model_calls": 0}, indent=2))


if __name__ == "__main__":
    main()
