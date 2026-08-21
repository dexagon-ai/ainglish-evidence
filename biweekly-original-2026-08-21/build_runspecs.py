#!/usr/bin/env python3
"""Build attempt-backed panel runspecs from a commit-pinned item freeze."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SLUG = "twice-weekly-every-two-weeks-split-biweekly-into-its-two-inc"
BASE_URL = "http://127.0.0.1:11435/v1"
READERS = [
    {
        "name": "qwen3.5-27b-choice-q4_k_m",
        "provider": "ollama",
        "model": "dexagon-qwen3.5-27b-choice:ctx4k",
        "model_digest": "adaeda2ee3194b25537f12b93b6c3ceb31217cba68ab0e593fb2bf90703da116",
        "precision": "q4_k_m",
        "max_tokens": 1024,
        "temperature": 0,
        "seed": 20260821,
        "api": "openai",
        "base_url": BASE_URL,
    },
    {
        "name": "mistral-small3.2-24b-instruct-q4_k_m",
        "provider": "ollama",
        "model": "mistral-small3.2:24b-instruct-2506-q4_K_M",
        "model_digest": "5a408ab55df5c1b5cf46533c368813b30bf9e4d8fc39263bf2a3338cfa3b895b",
        "precision": "q4_k_m",
        "max_tokens": 1024,
        "temperature": 0,
        "seed": 20260821,
        "api": "openai",
        "base_url": BASE_URL,
    },
]


def load_document(form: str) -> dict:
    return json.loads((ROOT / f"{form}-careful-items.json").read_text(encoding="utf-8"))


def build(form: str, freeze_commit: str) -> dict:
    document = load_document(form)
    url = (
        "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
        f"{freeze_commit}/biweekly-original-2026-08-21/{form}-careful-items.json"
    )
    return {
        "construct": "twice-weekly / every-two-weeks",
        "slug": SLUG,
        "metric": "comprehension_accuracy_delta",
        "seed": 2026082101 if form == "twice-weekly" else 2026082102,
        "planted_arm": "ainglish",
        "calibration_min_gap": 0.5,
        "panel_neff": 2,
        "panel": READERS,
        "items_url": url,
        "items_sha256": document["sha256"],
        "attempt": {
            "proposal_revision": SLUG,
            "estimand": (
                f"Comprehension_accuracy_delta in percentage points for {form} versus its complete "
                "careful-English mapping over 100 fixed rows: 70 cadence consequences and 30 "
                "over-reading controls. The form is estimated separately and is not pooled with "
                "the other proposed form."
            ),
            "admissibility_gates": [
                f"the commit-pinned item document hashes to {document['sha256']} and contains exactly 100 scientific rows plus 12 construct-free calibration rows",
                "scientific rows contain exactly 70 cadence-count consequences and 30 predeclared anchor/day/spacing/completion over-reading controls",
                "the English arm is the proposal's complete careful-English mapping; bare biweekly is excluded from the filed carrier",
                "count contexts reveal no weekday, calendar date, or clock-time cue that selects the intended cadence independently of the tested form",
                "the 12 construct-free calibration rows execute first in both arms and must show an explicit-minus-underdetermined accuracy gap of at least 0.5",
                "Qwen 3.5 27B and Mistral Small 3.2 24B execute sequentially at Q4_K_M, temperature 0, fixed seed, and the pinned model digests",
                "both readers remain fully resident on dedicated RTX 3090 GPU 0; CPU fallback, a contested GPU, or a non-empty competing queue aborts",
                "all null, adverse, ceiling-bound, and supportive scientific outcomes are retained; only input, transport, calibration, yield, commitment, or resource-contract failures may abort",
            ],
            "planned_sample": {
                "form": form,
                "real_items": 100,
                "calibration_items": 12,
                "probe_counts": {
                    "cadence_count": 70,
                    "form_specific_scope_controls": 20,
                    "completion_not_supplied": 10,
                },
                "comparison": "marked form versus complete careful-English mapping",
                "noninferiority_margin_pp": -5,
                "readers": 2,
                "reader_families": ["Qwen 3.5 27B", "Mistral Small 3.2 24B"],
                "reader_precision": "both local q4_k_m",
                "real_cells": 200,
                "calibration_cells": 48,
                "execution": "dedicated local RTX 3090 GPU 0; one loaded model and one request at a time; 4,096-token context; no CPU fallback",
            },
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze-commit", required=True)
    args = parser.parse_args()
    if len(args.freeze_commit) != 40 or any(ch not in "0123456789abcdef" for ch in args.freeze_commit):
        raise SystemExit("--freeze-commit must be a full lowercase SHA-1 commit id")
    receipts = {}
    for form in ("twice-weekly", "every-two-weeks"):
        spec = build(form, args.freeze_commit)
        name = f"runspec-{form}.json"
        path = ROOT / name
        path.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        receipts[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    print(json.dumps(receipts, indent=2))


if __name__ == "__main__":
    main()
