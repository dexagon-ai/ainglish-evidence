#!/usr/bin/env python3
"""Bind the public carrier, released receipt-preserving SDK, and Spark reader."""

from __future__ import annotations

from collections import Counter, defaultdict
import argparse
import hashlib
import json
from pathlib import Path

import ainglish
from ainglish import panel, reader_qualification


ROOT = Path(__file__).resolve().parent
SLUG = "send-snapshot-version-ref-to-recipient-grant-live-view"
ITEMS_COMMIT = "3737485bf7c7f0a8efd60034b189e41809b92126"
ITEMS_SHA256 = "26ec5c7674b5c0a54e3543a1e415e46b534c7647213d060c3d68d388bfcbbfc3"
SEED = 3191947
READER_NAME = "spark-zen-13-minimal"


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def commit(value: str, name: str) -> str:
    if len(value) != 40 or any(char not in "0123456789abcdef" for char in value):
        raise SystemExit(f"{name} must be a full lowercase Git commit")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sdk-commit", required=True)
    args = parser.parse_args()
    sdk_commit = commit(args.sdk_commit, "SDK commit")
    if ainglish.__version__ != "0.2.52":
        raise SystemExit(f"requires released ainglish 0.2.52, got {ainglish.__version__}")

    artifact = json.loads((ROOT / "items.json").read_text(encoding="utf-8"))
    if artifact["sha256"] != ITEMS_SHA256 or hashlib.sha256(canonical(artifact["items"])).hexdigest() != ITEMS_SHA256:
        raise SystemExit("frozen carrier digest mismatch")
    real = [item for item in artifact["items"] if not item.get("calibration")]
    controls = [item for item in artifact["items"] if item.get("calibration")]
    strata = sorted({item["settlement_stratum"] for item in real})
    report_cells = sorted({item["report_cell"] for item in real})
    if len(real) != 144 or len(controls) != 8 or len(strata) != 12 or len(report_cells) != 48:
        raise SystemExit("frozen carrier population mismatch")

    qualified = json.loads((ROOT / "spark-qualification.json").read_text(encoding="utf-8"))
    receipt = reader_qualification.validate(qualified["receipt"])
    reader = {
        "name": READER_NAME,
        "provider": "opencode-zen",
        "base_url": "https://opencode.ai/zen/v1",
        "api": "responses",
        "api_key_env": "OPENCODE_API_KEY",
        "model": "muse-spark-1.3-contributor-free",
        "precision": "provider-served",
        "reasoning_effort": "minimal",
        "max_tokens": 1024,
        "timeout_s": 120,
    }
    exposures: dict[str, Counter[str]] = defaultdict(Counter)
    report_exposures: dict[str, Counter[str]] = defaultdict(Counter)
    for item in real:
        arm = panel.arm_for(SEED, READER_NAME, item["id"])
        exposures[item["settlement_stratum"]][arm] += 1
        report_exposures[item["report_cell"]][arm] += 1
    missing = [ident for ident in strata if set(exposures[ident]) != {"english", "ainglish"}]
    if missing:
        raise SystemExit(f"seed leaves settlement cells without both arms: {missing}")
    missing_reports = [ident for ident in report_cells if set(report_exposures[ident]) != {"english", "ainglish"}]
    if missing_reports:
        raise SystemExit(f"seed leaves reported consequence cells without both arms: {missing_reports}")

    spec = {
        "construct": "send-snapshot / grant-live-view — fixed copy versus changing canonical source",
        "slug": SLUG,
        "metric": "comprehension_accuracy_delta",
        "seed": SEED,
        "planted_arm": "ainglish",
        "calibration_min_gap": 0.5,
        "panel_neff": 1,
        "panel": [reader],
        "models": [receipt["roster_id"]],
        "reader_qualifications": [receipt],
        "comparator": {
            "kind": "complete-careful-english-v1",
            "description": "each compact form versus its complete fixed-copy or revocable-live-view mapping; bare share is excluded from the accuracy estimand",
        },
        "items_url": (
            "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
            f"{ITEMS_COMMIT}/send-snapshot-live-view-comprehension-v1-2026-09-03/items.json"
        ),
        "items_sha256": ITEMS_SHA256,
        "settlement_strata": [{"id": ident, "weight": 1} for ident in strata],
        "concurrency": {"max_in_flight": 1, "per_reader_max_in_flight": {READER_NAME: 1}},
        "training_asymmetry": (
            "The provider-served reader was trained primarily on ordinary English and is not "
            "assumed to have seen Ainglish. This measures present zero-shot comprehension, not "
            "the expected efficiency of a future Ainglish-aware model."
        ),
        "attempt": {
            "proposal_revision": SLUG,
            "estimand": (
                "Original comprehension claim carrier: the equal-weight mean across 12 "
                "form-by-domain strata of exact two-question accuracy in the "
                "registered compact form minus its complete careful-English mapping, over 144 "
                "fresh operational scenarios. All 48 form-by-domain-by-consequence cells plus "
                "implementation and consequence scores remain separately recoverable diagnostics."
            ),
            "admissibility_gates": [
                "authenticated suggestions still request an original comprehension_accuracy_delta measurement immediately before mint",
                "the proposal remains current at measured stage and its evidence contract still lacks comprehension_accuracy_delta",
                f"the public 144+8 carrier at {ITEMS_COMMIT} hashes canonically to {ITEMS_SHA256}",
                "the carrier contains exactly 72 scenarios per form, 12 load-bearing form-by-domain strata, and all 48 required form-by-domain-by-consequence report cells",
                "every scenario exposes two separately recoverable questions and a complete four-way Cartesian answer set",
                "the frozen seed exposes both comparison arms inside every one of the 12 settlement strata for Spark's exact reader identity",
                "the same frozen deal exposes both comparison arms in every one of the 48 separately reported consequence cells",
                f"the receipt-preserving panel harness is the released ainglish 0.2.52 source at commit {sdk_commit}",
                "Spark's exact OpenCode Zen reader and settings passed the public target-independent screen before this target carrier was frozen",
                "the attached qualification receipt remains valid and exactly names the declared roster identity",
                "eight construct-free calibrations execute first in both arms and must recover a gap of at least 0.5",
                "zero transport faults, response-bound truncations, or missing scientific cells are required",
                "absolute arms, replayable interval, all 12 settlement strata, 48 report cells, and every normalized answer are retained",
                "every finite supportive, null, adverse, floor-bound, ceiling-bound, or inconclusive outcome is filed exactly once",
                "bare share is never used as an accuracy comparator against a hidden intended topology",
            ],
            "planned_sample": {
                "metric": "comprehension_accuracy_delta",
                "comparison": "registered compact form versus complete careful-English mapping",
                "scientific_scenarios": 144,
                "calibration_items": 8,
                "forms": {"send-snapshot": 72, "grant-live-view": 72},
                "domains": 6,
                "consequence_events": 4,
                "boundary_probes": 3,
                "settlement_strata": 12,
                "reported_consequence_cells": 48,
                "questions_per_scenario": 2,
                "readers": 1,
                "reader_lineages": ["meta/muse-spark"],
                "panel_members": 1,
                "panel_neff": 1,
                "real_cells": 144,
                "calibration_cells": 16,
                "sdk_version": "0.2.52",
                "sdk_commit": sdk_commit,
                "items_commit": ITEMS_COMMIT,
            },
        },
    }
    reader_qualification.attach({"models": spec["models"]}, spec["reader_qualifications"])
    manifest_bytes = canonical(spec)
    if len(manifest_bytes) > 20_000:
        raise SystemExit(f"runspec exceeds the register manifest cap: {len(manifest_bytes)} bytes")
    encoded = json.dumps(spec, indent=2, ensure_ascii=False) + "\n"
    (ROOT / "runspec.json").write_text(encoded, encoding="utf-8")
    print(json.dumps({
        "runspec": "runspec.json",
        "runspec_file_sha256": hashlib.sha256(encoded.encode()).hexdigest(),
        "manifest_bytes": len(manifest_bytes),
        "items_url": spec["items_url"],
        "items_sha256": ITEMS_SHA256,
        "sdk_commit": sdk_commit,
        "seed": SEED,
        "settlement_strata": len(strata),
        "arm_totals": Counter(
            panel.arm_for(SEED, READER_NAME, item["id"]) for item in real
        ),
        "reader_calls": 0,
        "attempt_mints": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
