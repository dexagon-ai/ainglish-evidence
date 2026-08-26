#!/usr/bin/env python3
"""Bind the published freeze to a released, paired-form-safe panel version."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO_PATH = "flagship-learnability-v2-wave-a-2026-08-26"
PANEL = [
    {
        "name": "mistral-small3.2-24b-learnability-v2-q4_k_m",
        "provider": "ollama",
        "model": "dexagon-mistral-small3.2-24b-pp-task:ctx4k",
        "model_digest": "sha256:6629ee92de51c9a1367e1331cfa9ef6a77058a44a6a3e18ab524b2d0404252de",
        "precision": "q4_k_m",
        "api": "openai",
        "base_url": "http://127.0.0.1:11435/v1",
        "max_tokens": 32,
        "timeout_s": 120,
        "temperature": 0,
    },
    {
        "name": "gemma3-12b-learnability-v2-q4_k_m",
        "provider": "ollama",
        "model": "dexagon-gemma3-12b-pp-task:ctx4k",
        "model_digest": "sha256:de1f65ea3438dfcc7c3387802b9425a140fb01ecc79edf4924a13fab051eb68f",
        "precision": "q4_k_m",
        "api": "openai",
        "base_url": "http://127.0.0.1:11435/v1",
        "max_tokens": 32,
        "timeout_s": 120,
        "temperature": 0,
    },
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def version_tuple(value: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"([0-9]+)\.([0-9]+)\.([0-9]+)", value)
    if not match:
        raise SystemExit("SDK version must be an exact X.Y.Z release")
    return tuple(int(group) for group in match.groups())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze-commit", required=True)
    parser.add_argument("--sdk-version", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.freeze_commit):
        raise SystemExit("freeze commit must be a full lowercase Git SHA")
    if version_tuple(args.sdk_version) <= (0, 2, 38):
        raise SystemExit("REFUSING: SDK 0.2.38 and earlier accept one-pole leakage in paired forms")

    snapshots = json.loads((ROOT / "proposal-snapshots.json").read_text(encoding="utf-8"))
    freeze = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    runspec_index = {
        "kind": "dexagon.ainglish.flagship-learnability-wave-a-runspec-index.v1",
        "freeze_commit": args.freeze_commit,
        "freeze_index_sha256": freeze["content_sha256"],
        "sdk_version": args.sdk_version,
        "campaigns": {},
    }
    for position, (campaign, meta) in enumerate(freeze["campaigns"].items()):
        surface = snapshots["proposals"][meta["proposal_key"]]["surface"]
        entry = (ROOT / meta["entry"]["path"]).read_text(encoding="utf-8")
        seed = freeze["seed"] + position
        raw_root = (
            "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
            f"{args.freeze_commit}/{REPO_PATH}"
        )
        spec = {
            "construct": f"{campaign}-learnability-v2",
            "slug": surface["slug"],
            "form": surface["form"],
            "metric": "learnability",
            "seed": seed,
            "planted_arm": "ainglish",
            "calibration_min_gap": 0.5,
            "panel_neff": 2,
            "panel": [dict(reader, seed=seed) for reader in PANEL],
            "comparator": {
                "kind": "register-entry-learnability-v2",
                "description": "The score is entry-loaded accuracy; the same marked messages are also read cold as a labelled diagnostic over the identical reader-item population.",
            },
            "entry": {
                "text": entry,
                "sha256": meta["entry"]["sha256"],
                "source_url": f"{raw_root}/{meta['entry']['path']}",
                "proposal_revision": surface["slug"],
            },
            "items_url": f"{raw_root}/{meta['items_path']}",
            "items_sha256": meta["items_sha256"],
            "resources": {
                "minimum_free_mib": 20_000,
                "expected_gpu_name": "NVIDIA GeForce RTX 3090",
                "maximum_utilization_percent": 25,
            },
            "attempt": {
                "proposal_revision": surface["slug"],
                "estimand": (
                    f"Learnability of {campaign} from one exact register entry: unit-interval exact "
                    "accuracy over all 48 fresh marked messages after the entry is prepended by the "
                    "released harness. The same reader-item population is read cold first as a "
                    "labelled diagnostic, not as the planted-effect control or a delta comparator."
                ),
                "admissibility_gates": [
                    f"the public freeze is commit {args.freeze_commit} with index digest {freeze['content_sha256']}",
                    f"the 56-row item array has canonical SDK digest {meta['items_sha256']}",
                    f"the exact entry snapshot has UTF-8 digest {meta['entry']['sha256']} and proposal revision {surface['slug']}",
                    "all 48 scientific items have byte-identical cold and entry-arm marked messages",
                    "the eight calibration rows teach only an unrelated novel marker and contain no complete entry, proposal slug, construct name, or slash/pipe/placeholder-delimited target-form literal",
                    "the released panel version is newer than 0.2.38 and mechanically refuses one-pole leakage before reader spend",
                    "the two reader artifacts match their declared digests and are distinct model families; both readers remain one Dexagon evidence principal",
                    "target-independent calibration runs first in both arms for every reader and must produce a planted-arm gap of at least 0.5",
                    "the dedicated loopback reader is reachable and its assigned GPU has at least 20,000 MiB free before mint",
                    "zero response-bound truncations and a passing cell-yield guard are required",
                    "every finite supportive, adverse, null, or instrument-refusal outcome is retained and filed once; no outcome retry is permitted",
                ],
                "planned_sample": {
                    "campaign": campaign,
                    "scientific_items": 48,
                    "calibration_items": 8,
                    "readers": 2,
                    "reader_families": ["Mistral Small 3.2 24B", "Gemma 3 12B"],
                    "panel_neff": 2,
                    "entry_loaded_cells": 96,
                    "cold_diagnostic_cells": 96,
                    "calibration_cells": 32,
                    "sdk_version": args.sdk_version,
                },
            },
        }
        path = ROOT / f"runspec-{campaign}.json"
        encoded = (json.dumps(spec, indent=2, ensure_ascii=False) + "\n").encode()
        path.write_bytes(encoded)
        runspec_index["campaigns"][campaign] = {
            "runspec": path.name,
            "runspec_sha256": hashlib.sha256(encoded).hexdigest(),
            "receipt_stem": f"learnability-v2-{campaign}",
        }
    runspec_index["content_sha256"] = hashlib.sha256(canonical(runspec_index)).hexdigest()
    (ROOT / "runspec-index.json").write_text(
        json.dumps(runspec_index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"campaigns": len(runspec_index["campaigns"]),
                      "content_sha256": runspec_index["content_sha256"]}))


if __name__ == "__main__":
    main()

