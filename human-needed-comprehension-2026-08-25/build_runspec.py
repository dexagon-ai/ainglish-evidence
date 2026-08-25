#!/usr/bin/env python3
"""Bind the frozen human_needed carrier to its immutable public commit."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from ainglish.panel import arm_for


ROOT = Path(__file__).resolve().parent
ITEMS = ROOT / "items.json"
ITEMS_SHA256 = "ebe65906e980140cdb1c47ddf4ee681d92e980f5a5698a662fb9b72ebc814038"
SLUG = "human-needed-why-the-escalation-pin-when-a-human-must-decide-2"
BASE_SEED = 2026082518
READERS = ["mistral-small3.2-24b-human-needed-q4_k_m", "gemma3-12b-human-needed-q4_k_m"]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def balanced_seed(rows: list[dict]) -> tuple[int, Counter, Counter]:
    for seed in range(BASE_SEED, BASE_SEED + 100_000):
        arms = {
            reader: Counter(arm_for(seed, reader, row["id"]) for row in rows)
            for reader in READERS
        }
        if any(counts != Counter({"english": 32, "ainglish": 32}) for counts in arms.values()):
            continue
        strata = Counter(
            (arm_for(seed, reader, row["id"]), row["question_type"])
            for reader in READERS
            for row in rows
        )
        if any(not 13 <= strata[(arm, kind)] <= 19 for arm in ("english", "ainglish") for kind in ("decider", "scope", "status", "reason")):
            continue
        answer_positions = Counter(
            (arm_for(seed, reader, row["id"]), row["options"].index(row["answer"]))
            for reader in READERS
            for row in rows
        )
        if any(not 18 <= answer_positions[(arm, pos)] <= 25 for arm in ("english", "ainglish") for pos in range(3)):
            continue
        return seed, strata, answer_positions
    raise SystemExit("REFUSING: no fully balanced assignment seed found")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--items-commit", required=True)
    args = parser.parse_args()
    if len(args.items_commit) != 40 or any(ch not in "0123456789abcdef" for ch in args.items_commit):
        raise SystemExit("items commit must be a full lowercase Git SHA")
    document = json.loads(ITEMS.read_text(encoding="utf-8"))
    rows = document["items"]
    actual = hashlib.sha256(canonical(rows)).hexdigest()
    if actual != ITEMS_SHA256 or document.get("sha256") != ITEMS_SHA256:
        raise SystemExit("REFUSING: frozen item digest mismatch")
    real = [row for row in rows if not row.get("calibration")]
    calibration = [row for row in rows if row.get("calibration")]
    if len(real) != 64 or len(calibration) != 8:
        raise SystemExit("REFUSING: frozen 64+8 sample changed")
    seed, strata, answer_positions = balanced_seed(real)
    panel = [
        {
            "name": READERS[0], "provider": "ollama",
            "model": "dexagon-mistral-small3.2-24b-pp-task:ctx4k",
            "model_digest": "sha256:6629ee92de51c9a1367e1331cfa9ef6a77058a44a6a3e18ab524b2d0404252de",
            "precision": "q4_k_m", "api": "openai", "base_url": "http://127.0.0.1:11435/v1",
            "max_tokens": 32, "timeout_s": 120, "temperature": 0, "seed": seed,
        },
        {
            "name": READERS[1], "provider": "ollama",
            "model": "dexagon-gemma3-12b-pp-task:ctx4k",
            "model_digest": "sha256:de1f65ea3438dfcc7c3387802b9425a140fb01ecc79edf4924a13fab051eb68f",
            "precision": "q4_k_m", "api": "openai", "base_url": "http://127.0.0.1:11435/v1",
            "max_tokens": 32, "timeout_s": 120, "temperature": 0, "seed": seed,
        },
    ]
    spec = {
        "construct": "human_needed(<why>) cold-comprehension recertification",
        "slug": SLUG,
        "metric": "comprehension_accuracy_delta",
        "seed": seed,
        "planted_arm": "ainglish",
        "calibration_min_gap": 0.5,
        "panel_neff": 2,
        "panel": panel,
        "comparator": {
            "kind": "complete-careful-english-v1",
            "description": "The complete registered human-decision, no-agent-resolution, no-unauthorized-action, and named-reason meaning.",
        },
        "items_url": (
            "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
            f"{args.items_commit}/human-needed-comprehension-2026-08-25/items.json"
        ),
        "items_sha256": ITEMS_SHA256,
        "resources": {
            "minimum_free_mib": 20_000,
            "expected_gpu_name": "NVIDIA GeForce RTX 3090",
            "maximum_utilization_percent": 25,
        },
        "attempt": {
            "proposal_revision": SLUG,
            "estimand": (
                "Post-ratification cold-legibility diagnostic: percentage-point difference in "
                "exact three-way consequence recovery, compact human_needed(<why>) arm minus the "
                "complete registered careful-English mapping, over 64 fresh pairs. Report the "
                "pooled result, absolute arms, the four implication strata, and both readers."
            ),
            "admissibility_gates": [
                f"the public 64+8 item array has SDK canonical-items sha256 {ITEMS_SHA256}",
                f"the answer-bearing carrier was frozen at public commit {args.items_commit} before attempt mint or reader spend",
                "the four implication strata are human decider, agent action boundary, still-unresolved status, and named escalation reason, with 16 scientific items each",
                "the English arm states the complete registered meaning; it is not a shorter ambiguous gloss",
                "the compact arm receives no definition card, so this remains a cold-comprehension diagnostic",
                "the assignment seed gives every reader 32 cells per arm, each implication stratum 13 to 19 cells per aggregate arm, and each answer position 18 to 25 cells per aggregate arm",
                "the two digest-pinned reader artifacts are distinct model families but remain one Dexagon evidence principal",
                "construct-free calibration runs first in both arms for every reader and must produce a planted-arm gap of at least 0.5",
                "the dedicated loopback reader is reachable and GPU 0 has at least 20,000 MiB free before mint",
                "zero response-bound truncations and a passing cell-yield guard are required",
                "every finite supportive, adverse, null, floor-bound, or ceiling-bound result is filed once; no outcome retry is permitted",
            ],
            "planned_sample": {
                "scientific_items": 64,
                "calibration_items": 8,
                "implication_strata": {"decider": 16, "scope": 16, "status": 16, "reason": 16},
                "domains": 16,
                "readers": 2,
                "reader_families": ["Mistral Small 3.2 24B", "Gemma 3 12B"],
                "reader_precision": "both local Q4_K_M",
                "real_cells": 128,
                "calibration_cells": 32,
                "aggregate_arm_cells": {"english": 64, "ainglish": 64},
                "implication_cells_per_arm": {
                    arm: {kind: strata[(arm, kind)] for kind in ("decider", "scope", "status", "reason")}
                    for arm in ("english", "ainglish")
                },
                "answer_positions_per_arm": {
                    arm: {str(pos): answer_positions[(arm, pos)] for pos in range(3)}
                    for arm in ("english", "ainglish")
                },
                "seed": seed,
                "sdk_version": "0.2.35",
            },
        },
    }
    spec_path = ROOT / "runspec.json"
    encoded = (json.dumps(spec, indent=2, ensure_ascii=False) + "\n").encode()
    spec_path.write_bytes(encoded)
    index = {
        "kind": "ainglish.human-needed-runspec-index.v1",
        "items_commit": args.items_commit,
        "campaigns": {
            "human-needed": {
                "runspec": spec_path.name,
                "runspec_sha256": hashlib.sha256(encoded).hexdigest(),
                "receipt_stem": "human-needed-cold-comprehension",
                "gpu_index": 0,
            }
        },
    }
    index["content_sha256"] = hashlib.sha256(canonical(index)).hexdigest()
    (ROOT / "runspec-index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"seed": seed, "runspec_sha256": index["campaigns"]["human-needed"]["runspec_sha256"], "index_sha256": index["content_sha256"], "reader_calls": 0}, indent=2))


if __name__ == "__main__":
    main()
