#!/usr/bin/env python3
"""Bind the fresh some-or-all replication carrier to an immutable public commit."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SLUG = "some-or-all-some-but-not-all-does-some-leave-room-for-all-2"
REPLICATES = "f9768ef4cf14f9cbe73672ee270cca013dad7b83b32d3eeb9a189a85ff22fdde"
SEED = 2026082517


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--items-commit", required=True)
    args = parser.parse_args()
    if len(args.items_commit) != 40 or any(ch not in "0123456789abcdef" for ch in args.items_commit):
        raise SystemExit("items commit must be a full lowercase Git SHA")
    freeze = json.loads((ROOT / "freeze-receipt.json").read_text())
    readers = [
        {
            "name": "mistral-small3.2-24b-some-bound-rep-q4_k_m", "provider": "ollama",
            "model": "dexagon-mistral-small3.2-24b-pp-task:ctx4k",
            "model_digest": "sha256:6629ee92de51c9a1367e1331cfa9ef6a77058a44a6a3e18ab524b2d0404252de",
            "precision": "q4_k_m", "api": "openai", "base_url": "http://127.0.0.1:11435/v1",
            "max_tokens": 32, "timeout_s": 120, "temperature": 0, "seed": SEED,
        },
        {
            "name": "gemma3-12b-some-bound-rep-q4_k_m", "provider": "ollama",
            "model": "dexagon-gemma3-12b-pp-task:ctx4k",
            "model_digest": "sha256:de1f65ea3438dfcc7c3387802b9425a140fb01ecc79edf4924a13fab051eb68f",
            "precision": "q4_k_m", "api": "openai", "base_url": "http://127.0.0.1:11435/v1",
            "max_tokens": 32, "timeout_s": 120, "temperature": 0, "seed": SEED,
        },
    ]
    spec = {
        "construct": "some-or-all form-specific fresh replication",
        "slug": SLUG,
        "metric": "comprehension_accuracy_delta",
        "replicates_hash": REPLICATES,
        "seed": SEED,
        "planted_arm": "ainglish",
        "calibration_min_gap": 0.5,
        "panel_neff": 2,
        "panel": readers,
        "comparator": {
            "kind": "complete-careful-english-v1",
            "description": "At least one bounded-set member satisfies the predicate, and the all-members case remains compatible.",
        },
        "items_url": (
            "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
            f"{args.items_commit}/some-or-all-replication-2026-08-25/items.json"
        ),
        "items_sha256": freeze["items_sha256"],
        "resources": {"minimum_free_mib": 20_000, "expected_gpu_name": "NVIDIA GeForce RTX 3090", "maximum_utilization_percent": 25},
        "attempt": {
            "proposal_revision": SLUG,
            "estimand": (
                "Independent fresh-input replication of Reticuli manifest " + REPLICATES + ": comprehension_accuracy_delta for some-or-all alone versus its complete careful-English mapping, over 48 lower-bound and 48 upper-bound held-out consequence probes. The form is not pooled with some-but-not-all and bare some is absent."
            ),
            "admissibility_gates": [
                f"the public 96+12 carrier has SDK canonical-items sha256 {freeze['items_sha256']}",
                f"the answer-bearing inputs were frozen at public commit {args.items_commit} before mint or reader spend",
                "all 96 complete English/Ainglish pairs are newly authored for this replication and absent from Dexagon's earlier candidate packet",
                "exactly 48 lower-bound and 48 upper-bound probes preserve the original form-specific estimand",
                "every English arm states at least one and explicitly leaves every-member satisfaction possible; bare some is absent",
                "reader artifacts are two model families different from the original Llama 3.1 and Qwen 3.6 roster and match declared digests",
                "construct-free calibration runs first in both arms for every reader and must show a planted-arm gap of at least 0.5",
                "the dedicated GPU-0 endpoint is reachable and GPU 0 has at least 20,000 MiB free before mint",
                "zero response-bound truncations and a passing cell-yield guard are required",
                "supportive, null, adverse, and disagreeing results are filed once without outcome retry",
            ],
            "planned_sample": {
                "form": "some-or-all", "real_items": 96, "lower_bound_probes": 48,
                "upper_bound_probes": 48, "calibration_items": 12, "readers": 2,
                "reader_families": ["Mistral Small 3.2 24B", "Gemma 3 12B"],
                "real_cells": 192, "calibration_cells": 48, "panel_neff": 2,
                "original_reader_families": ["Llama 3.1 8B", "Qwen 3.6 27B"],
            },
        },
    }
    path = ROOT / "runspec.json"
    encoded = (json.dumps(spec, indent=2, ensure_ascii=False) + "\n").encode()
    path.write_bytes(encoded)
    index = {
        "kind": "ainglish.some-or-all-fresh-replication-index.v1",
        "items_commit": args.items_commit,
        "campaigns": {"some-or-all": {
            "runspec": path.name, "runspec_sha256": hashlib.sha256(encoded).hexdigest(),
            "receipt_stem": "some-or-all-fresh-replication", "gpu_index": 0,
        }},
    }
    index["content_sha256"] = hashlib.sha256(canonical(index)).hexdigest()
    (ROOT / "runspec-index.json").write_text(json.dumps(index, indent=2) + "\n")
    print(json.dumps(index, indent=2))


if __name__ == "__main__":
    main()
