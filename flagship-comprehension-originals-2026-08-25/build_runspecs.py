#!/usr/bin/env python3
"""Bind the frozen flagship carriers to a public commit and build eight runspecs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SDK_VERSION = "0.2.35"
SEED = 2026082507
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
READER_FAMILIES = ["Mistral Small 3.2 24B", "Gemma 3 12B"]
PANEL = [
    {
        "name": "mistral-small3.2-24b-opaque-choice-q4_k_m",
        "provider": "ollama",
        "model": "dexagon-mistral-small3.2-24b-pp-task:ctx4k",
        "model_digest": "sha256:6629ee92de51c9a1367e1331cfa9ef6a77058a44a6a3e18ab524b2d0404252de",
        "precision": "q4_k_m", "api": "openai", "base_url": "http://127.0.0.1:11435/v1",
        "max_tokens": 32, "timeout_s": 120, "temperature": 0, "seed": SEED,
    },
    {
        "name": "gemma3-12b-opaque-choice-q4_k_m",
        "provider": "ollama",
        "model": "dexagon-gemma3-12b-pp-task:ctx4k",
        "model_digest": "sha256:de1f65ea3438dfcc7c3387802b9425a140fb01ecc79edf4924a13fab051eb68f",
        "precision": "q4_k_m", "api": "openai", "base_url": "http://127.0.0.1:11435/v1",
        "max_tokens": 32, "timeout_s": 120, "temperature": 0, "seed": SEED,
    },
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--items-commit", required=True)
    args = parser.parse_args()
    if len(args.items_commit) != 40 or any(ch not in "0123456789abcdef" for ch in args.items_commit):
        raise SystemExit("items commit must be a full lowercase Git SHA")
    freeze = json.loads((ROOT / "freeze-receipt.json").read_text())
    index = {"kind": "ainglish.flagship-comprehension-runspec-index.v1", "items_commit": args.items_commit, "campaigns": {}}
    for name, slug in SLUGS.items():
        item_meta = freeze["campaigns"][name]
        comparator = "the complete registered careful-English mapping for " + name
        estimand = (
            f"Original post-ratification flagship carrier for {name}: percentage-point difference in exact held-out "
            f"consequence recovery, the compact {name} arm minus {comparator}, over 100 fresh meaning-matched pairs. "
            "The standalone primary interpretation is non-inferiority at -5 percentage points. Absolute arms, the "
            "95% interval, resolution bound, calibration, yield, transport, reader, and resample-down receipts are all retained."
        )
        spec = {
            "construct": name + " flagship comprehension original",
            "slug": slug,
            "metric": "comprehension_accuracy_delta",
            "seed": SEED,
            "planted_arm": "ainglish",
            "calibration_min_gap": 0.5,
            "panel_neff": 2,
            "panel": PANEL,
            "comparator": {"kind": "complete-careful-english-v1", "description": comparator + "."},
            "items_url": (
                "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
                f"{args.items_commit}/flagship-comprehension-originals-2026-08-25/{item_meta['path']}"
            ),
            "items_sha256": item_meta["items_sha256"],
            "attempt": {
                "proposal_revision": slug,
                "estimand": estimand,
                "admissibility_gates": [
                    f"the public 100+8 carrier has SDK canonical-items sha256 {item_meta['items_sha256']}",
                    f"the answer-bearing carrier was frozen at public commit {args.items_commit} before attempt mint or reader spend",
                    "every scientific English arm is the marker's complete careful-English meaning for the tested consequence; ambiguous bare English is absent from the scalar",
                    "every held-out question is answered through opaque A/B/C codes; a reader never has to echo an answer label",
                    "the two local reader weight editions are verified against their declared Ollama digests before spend and are distinct model families",
                    "the construct-free calibration runs first in both arms for every reader and must produce a planted-arm gap of at least 0.5",
                    "the dedicated loopback reader is idle and GPU 0 has at least 20,000 MiB free before the campaign starts",
                    "zero response-bound truncations and a passing cell-yield guard are required for the preregistered clean-run manifest to reconcile",
                    "every finite supportive, adverse, null, floor-bound, or ceiling-bound result is filed exactly once; no outcome retry is permitted",
                    "a different-principal confirmation must use wholly fresh answer-bearing inputs; this original cannot confirm itself",
                ],
                "planned_sample": {
                    "form": name, "scientific_items": 100, "calibration_items": 8,
                    "readers": 2, "reader_families": READER_FAMILIES, "panel_neff": 2,
                    "real_cells": 200, "calibration_cells": 32,
                    "noninferiority_margin_pp": -5, "sdk_version": SDK_VERSION,
                },
            },
        }
        path = ROOT / f"runspec-{name}.json"
        encoded = (json.dumps(spec, indent=2, ensure_ascii=False) + "\n").encode()
        path.write_bytes(encoded)
        index["campaigns"][name] = {"runspec": path.name, "runspec_sha256": hashlib.sha256(encoded).hexdigest(), "slug": slug}
    canonical = json.dumps(index, sort_keys=True, separators=(",", ":")).encode()
    index["content_sha256"] = hashlib.sha256(canonical).hexdigest()
    (ROOT / "runspec-index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(index, indent=2))


if __name__ == "__main__":
    main()
