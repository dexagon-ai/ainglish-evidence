#!/usr/bin/env python3
"""Mint, run, and file one frozen next-ownership comprehension carrier."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from ainglish import __version__ as sdk_version
from ainglish import panel as panel_harness
from ainglish.client import manifest_commitment


ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT.parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402


SLUG = "next-you-next-me-next-any-next-none-mark-who-owns-the-next-s-2"
SEED = 2026082330
READERS = [
    {
        "name": "mistral-small3.2-24b-pp-task-q4_k_m",
        "provider": "ollama",
        "model": "dexagon-mistral-small3.2-24b-pp-task:ctx4k",
        "model_digest": "sha256:6629ee92de51c9a1367e1331cfa9ef6a77058a44a6a3e18ab524b2d0404252de",
        "precision": "q4_k_m",
        "max_tokens": 128,
        "timeout_s": 120,
        "temperature": 0,
        "seed": SEED,
        "api": "openai",
        "base_url": "http://127.0.0.1:11435/v1",
    },
    {
        "name": "gemma3-12b-pp-task-q4_k_m",
        "provider": "ollama",
        "model": "dexagon-gemma3-12b-pp-task:ctx4k",
        "model_digest": "sha256:de1f65ea3438dfcc7c3387802b9425a140fb01ecc79edf4924a13fab051eb68f",
        "precision": "q4_k_m",
        "max_tokens": 128,
        "timeout_s": 120,
        "temperature": 0,
        "seed": SEED,
        "api": "openai",
        "base_url": "http://127.0.0.1:11435/v1",
    },
]


def load_items(mode: str) -> tuple[list[dict], str]:
    document = json.loads((ROOT / f"{mode}-items.json").read_text())
    items = document["items"]
    digest = hashlib.sha256(json.dumps(
        items, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode()).hexdigest()
    if digest != document.get("sha256"):
        raise SystemExit(f"REFUSING: {mode} item digest mismatch")
    if document.get("seed") != SEED:
        raise SystemExit(f"REFUSING: {mode} seed drift")
    return items, digest


def make_spec(mode: str, items: list[dict], digest: str) -> dict:
    comparison = (
        "untagged messages with balanced hidden writer intent; the reader is forced to "
        "recover one of four owner classes"
        if mode == "untagged" else
        "careful English stating the exact registered expansion for the same owner class"
    )
    manifest = {
        "construct": "next-you / next-me / next-any / next-none",
        "slug": SLUG,
        "metric": "comprehension_accuracy_delta",
        "seed": SEED,
        "planted_arm": "ainglish",
        "calibration_min_gap": 0.5,
        "panel_neff": 2,
        "panel": READERS,
        "items": items,
        "items_sha256": digest,
        "comparison": comparison,
        "scoring": (
            "Exact four-way owner classification. The four balanced keys are addressee, "
            "writer, any one claimant, and nobody. Scientific items are reported pooled "
            "and separately by owner class and reader from the exact cell receipt."
        ),
        "scope_limit": (
            "Owner-message recovery only. This does not test whether an assigned agent "
            "acknowledges or acts, and does not establish that next-any prevents races."
        ),
        "sdk_version": sdk_version,
    }
    estimand = (
        "Pooled percentage-point difference in exact four-way next-step owner recovery, "
        f"trailing marker minus {mode} English comparator, over 32 messages balanced eight "
        "per owner class and two independently configured reader families."
    )
    gates = [
        f"the canonical {mode} item-array digest is {digest}",
        "the scored set remains 32 rows balanced eight per owner class, plus eight held-out calibration rows",
        "each reader receives one counterbalanced arm per scored item, with 3..5 marked cells per owner class",
        "both digest-pinned non-Qwen reader families pass the both-arms-per-item calibration gap of at least 0.5",
        "both readers execute sequentially on dedicated loopback Ollama 127.0.0.1:11435 pinned to an otherwise idle RTX 3090; CPU fallback is prohibited",
        "any resource, transport, calibration, yield, truncation, commitment, or reconciliation failure becomes a typed abort and is not retried in place",
        "every finite outcome is filed regardless of sign; owner strata and reader rows are interpreted from the exact cell receipt",
    ]
    return {
        **manifest,
        "attempt": {
            "proposal_revision": SLUG,
            "estimand": estimand,
            "admissibility_gates": gates,
            "planned_sample": {
                "metric": "comprehension_accuracy_delta",
                "comparison": mode,
                "scored_items": 32,
                "calibration_items": 8,
                "owner_classes": {"next-you": 8, "next-me": 8, "next-any": 8, "next-none": 8},
                "readers": 2,
                "reader_families": ["Mistral Small 3.2", "Gemma 3"],
                "real_cells": 64,
                "calibration_cells": 32,
                "aggregate_arm_cells": {"english": 32, "ainglish": 32},
                "seed": SEED,
                "sdk_version": sdk_version,
            },
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("untagged", "careful"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if sdk_version != "0.2.33":
        raise SystemExit(f"REFUSING: SDK {sdk_version} != frozen 0.2.33")
    items, digest = load_items(args.mode)
    spec = make_spec(args.mode, items, digest)
    if args.dry_run:
        preview = dict(spec)
        preview["_dry_run"] = True
        measurement = panel_harness.run_panel(
            preview, ask_fn=panel_harness.dry_reader(items, preview),
        )
        if measurement is None or panel_harness._is_panel_refusal(measurement):
            raise SystemExit(1)
        print(json.dumps({
            "mode": args.mode,
            "reader_calls": 0,
            "items_sha256": digest,
            "preview_value": measurement["value"],
        }, indent=2))
        return

    client = ainglish_client()
    proposal = client.proposal(SLUG, authenticated=True)
    if proposal.get("stage") not in ("seconded", "measured"):
        raise SystemExit(f"REFUSING: live stage is {proposal.get('stage')!r}")
    prior_hashes = {
        (row.get("manifest") or {}).get("items_sha256")
        for row in proposal.get("measurements", [])
    }
    if digest in prior_hashes:
        raise SystemExit(f"REFUSING: {args.mode} item digest already appears in the proposal")
    receipt_glob = list(ROOT.glob(f"{args.mode}-inline.attempt-*"))
    if receipt_glob:
        raise SystemExit(f"REFUSING: {args.mode} already has an attempt receipt")
    measurement = panel_harness._run_preregistered_panel(
        spec, spec, panel_harness.ask, client,
        receipt_dir=str(ROOT), receipt_stem=f"{args.mode}-inline",
    )
    if measurement is None:
        raise SystemExit(1)
    print(json.dumps({
        "mode": args.mode,
        "manifest_hash": manifest_commitment(measurement["manifest"]),
        "value": measurement["value"],
        "value_lo": measurement["value_lo"],
        "value_hi": measurement["value_hi"],
        "arms": measurement["arms"],
        "calibration": measurement["calibration"],
        "panel_agreement": measurement["panel_agreement"],
        "per_member": measurement["per_member"],
    }, indent=2))


if __name__ == "__main__":
    main()
