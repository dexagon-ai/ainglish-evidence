#!/usr/bin/env python3
"""Preregister, score and file one fresh replication of the corrected token original."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys

from ainglish.client import manifest_commitment

from items import TEST_SET


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
PROJECT = REPO.parent
sys.path.insert(0, str(PROJECT / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402


SLUG = "repeat-or-front-a-modifier-never-shares-an-unmarked-2"
TARGET_HASH = "173bb0036b13b110b05f2846efd4d27a02f91a9d77c737067a4cec63f92d6088"
ENCODINGS = ["cl100k_base", "o200k_base", "p50k_base"]
TOKENIZER_VERSION = "0.14.0"
REPAIRS = {"repeat-wide": 8, "front-narrow": 4, "double-determiner-narrow": 4}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO, check=True, capture_output=True, text=True
    ).stdout.strip()


def pair_key(row: dict) -> tuple[str, str]:
    return row["english"].strip(), row["ainglish"].strip()


def validate_frozen() -> dict:
    counts = {name: sum(row["repair"] == name for row in TEST_SET) for name in REPAIRS}
    pairs = [pair_key(row) for row in TEST_SET]
    if len(TEST_SET) != 16 or counts != REPAIRS:
        raise RuntimeError(f"frozen corpus shape changed: {counts}")
    if len({row["item_id"] for row in TEST_SET}) != 16 or len(set(pairs)) != 16:
        raise RuntimeError("duplicate item id or complete pair")
    if any(not left or not right or left == right for left, right in pairs):
        raise RuntimeError("empty or identical pair arm")
    return {
        "pairs": 16,
        "repair_counts": counts,
        "items_sha256": hashlib.sha256(canonical(TEST_SET)).hexdigest(),
    }


def preflight(client) -> dict:
    if git("status", "--porcelain"):
        raise RuntimeError("evidence repository is not clean")
    commit = git("rev-parse", "HEAD")
    if commit != git("rev-parse", "origin/main"):
        raise RuntimeError("frozen source is not public at origin/main")
    if importlib.metadata.version("tiktoken") != TOKENIZER_VERSION:
        raise RuntimeError("tiktoken version drift")

    suggestions = client.suggestions()
    proposal = client.proposal(SLUG, authenticated=True)
    target = client.measurement(TARGET_HASH)
    me = client.whoami()["sub"]
    offered = any(
        item.get("slug") == SLUG and item.get("replicates_hash") == TARGET_HASH
        for item in suggestions.get("suggestions", [])
    )
    if not offered:
        raise RuntimeError("fresh authenticated suggestions no longer offer this replication")
    if proposal.get("stage") not in {"seconded", "measured"} or proposal.get("superseded_by"):
        raise RuntimeError("proposal is no longer an active measurable surface")
    if target.get("metric") != "token_delta" or target.get("evidence_state") != "valid":
        raise RuntimeError("corrected target is absent or invalid")
    if target.get("is_replication") or target.get("retraction") or target.get("voided_at"):
        raise RuntimeError("target is not a live original")
    if target.get("panel_models") != ENCODINGS or target.get("value") != 1:
        raise RuntimeError("corrected target contract or value drifted")

    rows = list(client.iter_measurements(proposal=SLUG))
    if any(
        row.get("is_replication")
        and row.get("replicates_hash") == TARGET_HASH
        and (row.get("submitter") or {}).get("sub") == me
        for row in rows
    ):
        raise RuntimeError("Dexagon already supplied a settlement voice for this original")

    prior_pairs: set[tuple[str, str]] = set()
    prior_english: set[str] = set()
    prior_ainglish: set[str] = set()
    for summary in rows:
        manifest = client.measurement(summary["manifest_hash"]).get("manifest") or {}
        for old in manifest.get("test_set", []):
            if isinstance(old, dict) and isinstance(old.get("english"), str) \
                    and isinstance(old.get("ainglish"), str):
                pair = pair_key(old)
                prior_pairs.add(pair)
                prior_english.add(pair[0])
                prior_ainglish.add(pair[1])
    ours = set(map(pair_key, TEST_SET))
    english = {left for left, _ in ours}
    ainglish = {right for _, right in ours}
    if ours & prior_pairs or english & prior_english or ainglish & prior_ainglish:
        raise RuntimeError("fresh-input gate failed: pair or individual arm reused")

    return {
        "at": datetime.now(timezone.utc).isoformat(),
        "source_commit": commit,
        "suggestions_generated_at": suggestions.get("generated_at"),
        "proposal_stage": proposal.get("stage"),
        "target_hash": TARGET_HASH,
        "target_value": target.get("value"),
        "target_settlement_state": target.get("settlement_state"),
        "visible_prior_complete_pairs": len(prior_pairs),
        "complete_pair_overlap": 0,
        "english_arm_overlap": 0,
        "ainglish_arm_overlap": 0,
        **validate_frozen(),
    }


def make_manifest(check: dict) -> dict:
    return {
        "kind": "dexagon.ainglish.repeat-or-front-corrected-token-replication.v1",
        "metric": "token_delta",
        "formula_version": 1,
        "construct": "repeat-or-front",
        "replicates_hash": TARGET_HASH,
        "models": ENCODINGS,
        "test_set": TEST_SET,
        "items_sha256": check["items_sha256"],
        "test_set_note": (
            "Sixteen wholly fresh coordination-boundary repairs: eight repeated-wide, four "
            "fronted-narrow, and four determiner-doubled-narrow pairs."
        ),
        "estimand": {
            "population": "all 16 frozen repair pairs",
            "aggregation": "equal item mean per tokenizer; headline maximum tokenizer mean",
            "reference": "the corrected original's current-tokenizer cost per repaired boundary",
            "comparator": "the corresponding bare modifier-plus-coordination sentence",
        },
        "method": (
            "With tiktoken 0.14.0, compute len(encode(ainglish)) - len(encode(english)) "
            "without special tokens for each pair; average all 16 pairs per tokenizer; report "
            "the largest tokenizer mean, with the tokenizer-member span as the interval."
        ),
        "environment": {"library": "tiktoken", "version": TOKENIZER_VERSION},
        "comparison_identity": {
            "comparator_genre": "bare-modifier-coordination-v1",
            "pair_rendering": "single-sentence",
            "tokenizer_roster": ENCODINGS,
        },
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "commit": check["source_commit"],
            "path": "repeat-or-front-corrected-token-replication-v1-2026-09-02/items.py",
        },
        "evidentiary_limit": (
            "This tests current tokenizer cost, not modifier-scope comprehension. Present "
            "tokenizers have ordinary-English training exposure and are not a forecast of "
            "future Ainglish-aware tokenization."
        ),
    }


def score(manifest: dict) -> tuple[dict, dict]:
    import tiktoken

    cells = {}
    means = {}
    repair_means = {}
    for name in ENCODINGS:
        encode = tiktoken.get_encoding(name).encode
        cells[name] = []
        for row in manifest["test_set"]:
            english_tokens = len(encode(row["english"]))
            ainglish_tokens = len(encode(row["ainglish"]))
            cells[name].append({
                "item_id": row["item_id"],
                "repair": row["repair"],
                "english_tokens": english_tokens,
                "ainglish_tokens": ainglish_tokens,
                "delta": ainglish_tokens - english_tokens,
            })
        means[name] = sum(cell["delta"] for cell in cells[name]) / 16
        repair_means[name] = {
            repair: sum(cell["delta"] for cell in cells[name] if cell["repair"] == repair)
            / count
            for repair, count in REPAIRS.items()
        }
    value = max(means.values())
    payload = {
        "metric": "token_delta",
        "formula_version": 1,
        "value": value,
        "value_lo": min(means.values()),
        "value_hi": max(means.values()),
        "panel_models": ENCODINGS,
        "per_member": [{"model": name, "value": means[name]} for name in ENCODINGS],
        "manifest": manifest,
    }
    return payload, {
        "value": value,
        "value_lo": min(means.values()),
        "value_hi": max(means.values()),
        "tokenizer_means": means,
        "repair_means": repair_means,
        "cells": cells,
    }


def main() -> None:
    attempt_path = ROOT / "attempt.json"
    result_path = ROOT / "measurement.json"
    abort_path = ROOT / "abort.json"
    if any(path.exists() for path in (attempt_path, result_path, abort_path)):
        raise SystemExit("REFUSING: one-shot campaign already has an execution artifact")

    client = ainglish_client()
    check = preflight(client)
    manifest = make_manifest(check)
    check["manifest_commitment"] = manifest_commitment(manifest)
    if len(canonical(manifest)) > 20_000:
        raise RuntimeError("manifest exceeds register limit")
    opened = client.mint_attempt(
        SLUG,
        manifest=manifest,
        estimand=(
            "Maximum tokenizer mean token_delta across cl100k_base, o200k_base and p50k_base "
            "on sixteen wholly fresh repeat-or-front repair pairs."
        ),
        admissibility_gates=[
            "fresh authenticated suggestions and proposal/target reads precede mint",
            "the exact clean source is public at origin/main before mint",
            "the corrected target remains a live valid token_delta original",
            "Dexagon has not already supplied a settlement voice for the corrected original",
            "all complete pairs and individual arms are fresh against visible evidence",
            "the sixteen-pair power-of-two sample and target tokenizer roster remain intact",
            "tiktoken 0.14.0 loads only after successful preregistration",
            "every finite result is filed once regardless of direction",
        ],
        planned_sample={
            "metric": "token_delta",
            "pairs": 16,
            "repair_counts": check["repair_counts"],
            "models": ENCODINGS,
            "readers": 0,
            "items_sha256": check["items_sha256"],
            "replicates_hash": TARGET_HASH,
        },
        proposal_revision=SLUG,
        store_manifest=True,
    )["attempt"]
    attempt_path.write_text(json.dumps({"attempt": opened, "preflight": check}, indent=2) + "\n")
    try:
        payload, computed = score(manifest)
        payload["attempt_id"] = opened["attempt_id"]
        payload["replicates_hash"] = TARGET_HASH
        filed = client.measure(SLUG, payload)
    except Exception as exc:
        state = client.attempt(opened["attempt_id"])
        if state.get("state") == "open":
            receipt = {
                "kind": "dexagon.ainglish.repeat-or-front-token-abort.v1",
                "at": datetime.now(timezone.utc).isoformat(),
                "error": f"{type(exc).__name__}: {exc}",
                "preflight": check,
            }
            aborted = client.abort_attempt(
                opened["attempt_id"],
                "token replication harness failed before measurement emission",
                receipt,
                failed_gate_kind="harness_error",
            )
            abort_path.write_text(json.dumps({"receipt": receipt, "abort": aborted}, indent=2) + "\n")
        raise

    row = filed.get("measurement") or filed
    fresh_target = client.measurement(TARGET_HASH)
    result_path.write_text(json.dumps({
        "kind": "dexagon.ainglish.repeat-or-front-corrected-token-replication-result.v1",
        "attempt": opened,
        "preflight": check,
        "computed": computed,
        "measurement": filed,
        "post_write_target": {
            key: fresh_target.get(key)
            for key in ("confirmed", "settlement_state", "replication_count", "disagreement_count")
        },
    }, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({
        "attempt_id": opened["attempt_id"],
        "measurement_hash": row.get("manifest_hash"),
        "value": computed["value"],
        "tokenizer_means": computed["tokenizer_means"],
        "repair_means": computed["repair_means"],
        "reproduced_ok": row.get("reproduced_ok"),
        "settlement_eligible": row.get("settlement_eligible"),
    }, indent=2))


if __name__ == "__main__":
    main()
