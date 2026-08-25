#!/usr/bin/env python3
"""Bind frozen reference-loaded carriers to an immutable public commit."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SDK_VERSION = "0.2.35"
SEED = 2026082513
SLUGS = {
    "we-including-you": "we-including-you-we-excluding-you-clusivity-mark-whether-we--4",
    "we-excluding-you": "we-including-you-we-excluding-you-clusivity-mark-whether-we--4",
    "you-one": "you-one-you-all-say-whether-you-addresses-one-recipient-or-t",
    "you-all": "you-one-you-all-say-whether-you-addresses-one-recipient-or-t",
    "fact-not-known": "fact-not-known-choice-not-made-distinguish-missing-evidence-",
    "choice-not-made": "fact-not-known-choice-not-made-distinguish-missing-evidence-",
    "no-delegation": "no-delegation-one-hop-delegation-allowed-state-whether-a-tas",
    "one-hop-delegation-allowed": "no-delegation-one-hop-delegation-allowed-state-whether-a-tas",
}
PANEL = [
    {
        "name": "mistral-small3.2-24b-reference-loaded-q4_k_m",
        "provider": "ollama", "model": "dexagon-mistral-small3.2-24b-pp-task:ctx4k",
        "model_digest": "sha256:6629ee92de51c9a1367e1331cfa9ef6a77058a44a6a3e18ab524b2d0404252de",
        "precision": "q4_k_m", "api": "openai", "base_url": "http://127.0.0.1:11435/v1",
        "max_tokens": 32, "timeout_s": 120, "temperature": 0, "seed": SEED,
    },
    {
        "name": "gemma3-12b-reference-loaded-q4_k_m",
        "provider": "ollama", "model": "dexagon-gemma3-12b-pp-task:ctx4k",
        "model_digest": "sha256:de1f65ea3438dfcc7c3387802b9425a140fb01ecc79edf4924a13fab051eb68f",
        "precision": "q4_k_m", "api": "openai", "base_url": "http://127.0.0.1:11435/v1",
        "max_tokens": 32, "timeout_s": 120, "temperature": 0, "seed": SEED,
    },
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--items-commit", required=True)
    args = parser.parse_args()
    if len(args.items_commit) != 40 or any(ch not in "0123456789abcdef" for ch in args.items_commit):
        raise SystemExit("items commit must be a full lowercase Git SHA")
    freeze = json.loads((ROOT / "freeze-receipt.json").read_text())
    index = {
        "kind": "ainglish.flagship-reference-loaded-runspec-index.v1",
        "items_commit": args.items_commit,
        "campaigns": {},
    }
    for position, (form, slug) in enumerate(SLUGS.items()):
        meta = freeze["campaigns"][form]
        comparator = "the marker's complete registered careful-English meaning"
        spec = {
            "construct": f"{form} one-shot reference-loaded comprehension",
            "slug": slug,
            "metric": "comprehension_accuracy_delta",
            "seed": SEED + position,
            "planted_arm": "ainglish",
            "calibration_min_gap": 0.5,
            "panel_neff": 2,
            "panel": [dict(reader, seed=SEED + position) for reader in PANEL],
            "comparator": {
                "kind": "reference-loaded-careful-english-v1",
                "description": "Both arms receive the same one-shot pair-definition reference card; the compact marker is compared with its complete careful-English mapping.",
            },
            "items_url": (
                "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
                f"{args.items_commit}/flagship-reference-loaded-2026-08-25/{meta['path']}"
            ),
            "items_sha256": meta["items_sha256"],
            "resources": {
                "minimum_free_mib": 20_000,
                "expected_gpu_name": "NVIDIA GeForce RTX 3090",
                "maximum_utilization_percent": 25,
            },
            "attempt": {
                "proposal_revision": slug,
                "estimand": (
                    f"Post-ratification deployment diagnostic for {form}: percentage-point difference in exact held-out consequence recovery, compact {form} minus {comparator}, over 64 fresh meaning-matched pairs after both arms receive the same one-shot pair-definition reference card. This estimates reference-loaded use and does not overwrite or reinterpret the earlier cold standalone result."
                ),
                "admissibility_gates": [
                    f"the public 64+8 item array has SDK canonical-items sha256 {meta['items_sha256']}",
                    f"the answer-bearing carrier was frozen at public commit {args.items_commit} before attempt mint or reader spend",
                    "both scientific arms carry byte-identical one-shot pair-definition reference cards before their differing messages",
                    "every English message is the tested marker's complete registered careful-English meaning; ambiguous bare English is absent",
                    "all questions use opaque answer binding and test consequences not copied verbatim from the definition card",
                    "the two reader artifacts match their declared digests and are distinct model families; two readers remain one Dexagon evidence principal",
                    "construct-free calibration runs first in both arms for every reader and must produce a planted-arm gap of at least 0.5",
                    "the dedicated loopback reader is reachable and its assigned GPU has at least 20,000 MiB free before mint",
                    "zero response-bound truncations and a passing cell-yield guard are required",
                    "every finite supportive, adverse, null, floor-bound, or ceiling-bound result is filed once; no outcome retry is permitted",
                ],
                "planned_sample": {
                    "form": form,
                    "deployment_condition": "one-shot pair-definition reference card in both arms",
                    "scientific_items": 64,
                    "calibration_items": 8,
                    "readers": 2,
                    "reader_families": ["Mistral Small 3.2 24B", "Gemma 3 12B"],
                    "panel_neff": 2,
                    "real_cells": 128,
                    "calibration_cells": 32,
                    "noninferiority_margin_pp": -5,
                    "sdk_version": SDK_VERSION,
                },
            },
        }
        path = ROOT / f"runspec-{form}.json"
        encoded = (json.dumps(spec, indent=2, ensure_ascii=False) + "\n").encode()
        path.write_bytes(encoded)
        index["campaigns"][form] = {
            "runspec": path.name,
            "runspec_sha256": hashlib.sha256(encoded).hexdigest(),
            "receipt_stem": f"reference-loaded-{form}",
            "gpu_index": 0,
        }
    index["content_sha256"] = hashlib.sha256(canonical(index)).hexdigest()
    (ROOT / "runspec-index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(index, indent=2))


if __name__ == "__main__":
    main()
