#!/usr/bin/env python3
"""Preregister, score, and file one fresh token dispute replication."""

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


SLUG = "may-not-as-prohibition-may-not-as-possibility"
TARGET_HASH = "e9534d4ac79dfbf4f7f2e134fbb85a9bf01768fa41b3f9ee05c8112d7411d982"
ENCODINGS = ["cl100k_base", "o200k_base", "p50k_base"]
TOKENIZER_VERSION = "0.14.0"
FORMS = ["may-not-as-prohibition", "may-not-as-possibility"]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO, check=True, capture_output=True, text=True
    ).stdout.strip()


def pair_key(item: dict) -> tuple[str, str]:
    return item["english"].strip(), item["ainglish"].strip()


def validate_frozen() -> dict:
    counts = {form: sum(row["form"] == form for row in TEST_SET) for form in FORMS}
    pairs = [pair_key(row) for row in TEST_SET]
    if len(TEST_SET) != 16 or counts != {form: 8 for form in FORMS}:
        raise RuntimeError(f"the frozen corpus is not balanced 8/8: {counts}")
    if len({row["item_id"] for row in TEST_SET}) != len(TEST_SET):
        raise RuntimeError("duplicate item_id")
    if len(set(pairs)) != len(pairs):
        raise RuntimeError("duplicate complete pair")
    if any(not left or not right or left == right for left, right in pairs):
        raise RuntimeError("empty or identical arm")
    return {
        "pairs": len(TEST_SET),
        "form_counts": counts,
        "items_sha256": hashlib.sha256(canonical(TEST_SET)).hexdigest(),
    }


def preflight(client) -> tuple[dict, dict]:
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
    if proposal.get("stage") not in {"seconded", "measured"} or proposal.get("superseded_by"):
        raise RuntimeError("proposal is no longer an active measurable surface")
    if target.get("metric") != "token_delta" or target.get("evidence_state") != "valid":
        raise RuntimeError("target original is absent or invalid")
    if target.get("is_replication") or target.get("retraction") or target.get("voided_at"):
        raise RuntimeError("target is not a live original")
    if target.get("settlement_state") != "disputed":
        raise RuntimeError("target dispute has moved; stop and reassess")
    if target.get("panel_models") != ENCODINGS:
        raise RuntimeError("target tokenizer roster drifted")

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
    for row in rows:
        old_manifest = client.measurement(row["manifest_hash"]).get("manifest") or {}
        for old in old_manifest.get("test_set", []):
            if isinstance(old, dict) and "english" in old and "ainglish" in old:
                old_pair = pair_key(old)
                prior_pairs.add(old_pair)
                prior_english.add(old_pair[0])
                prior_ainglish.add(old_pair[1])
    ours = set(map(pair_key, TEST_SET))
    english = {left for left, _ in ours}
    ainglish = {right for _, right in ours}
    if ours & prior_pairs or english & prior_english or ainglish & prior_ainglish:
        raise RuntimeError("fresh-input gate failed: a complete pair or individual arm was reused")

    check = {
        "at": datetime.now(timezone.utc).isoformat(),
        "source_commit": commit,
        "suggestions_generated_at": suggestions.get("generated_at"),
        "proposal_stage": proposal.get("stage"),
        "target_hash": TARGET_HASH,
        "target_value": target.get("value"),
        "target_settlement_state": target.get("settlement_state"),
        "target_replication_count": target.get("replication_count"),
        "target_disagreement_count": target.get("disagreement_count"),
        "visible_prior_complete_pairs": len(prior_pairs),
        "complete_pair_overlap": 0,
        "english_arm_overlap": 0,
        "ainglish_arm_overlap": 0,
        **validate_frozen(),
    }
    return check, target


def make_manifest(check: dict) -> dict:
    return {
        "kind": "dexagon.ainglish.may-not-token-dispute-replication.v1",
        "metric": "token_delta",
        "formula_version": 1,
        "construct": "may-not-as-prohibition / may-not-as-possibility",
        "replicates_hash": TARGET_HASH,
        "models": ENCODINGS,
        "test_set": TEST_SET,
        "items_sha256": check["items_sha256"],
        "test_set_note": (
            "Sixteen wholly fresh complete bare-may-not message pairs, balanced eight/eight by form; "
            "no complete pair or individual arm is reused from visible evidence."
        ),
        "estimand": {
            "population": "all 16 frozen complete pairs, balanced eight per form",
            "aggregation": "equal-form mean per tokenizer; headline is the least-favourable maximum tokenizer mean",
            "reference": "the same bare-may-not token_delta scalar as the target original on wholly disjoint inputs",
            "comparator": "the corresponding ordinary-English sentence using bare may not",
        },
        "method": (
            "With tiktoken 0.14.0, compute len(encode(ainglish)) - len(encode(english)) "
            "without special tokens for every pair. Average within form and equally across forms "
            "for each tokenizer; report the largest tokenizer mean. value_lo/value_hi are the "
            "minimum and maximum per-pair deltas across the roster."
        ),
        "environment": {"library": "tiktoken", "version": TOKENIZER_VERSION},
        "comparison_identity": {
            "comparator_genre": "bare-may-not-v1",
            "pair_rendering": "single-sentence",
            "tokenizer_roster": ENCODINGS,
        },
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "commit": check["source_commit"],
            "path": "may-not-token-dispute-replication-2026-09-02/items.py",
        },
        "evidentiary_limit": (
            "This replicates the target's bare-English token comparison. It does not test the "
            "proposal's complete careful-English comparator or its comprehension claim. Current "
            "tokenizers also favour English from their training data, so this is not a forecast "
            "for future Ainglish-aware tokenizers."
        ),
    }


def score(manifest: dict) -> tuple[dict, dict]:
    import tiktoken

    cells, form_means, tokenizer_means = {}, {}, {}
    for encoding_name in ENCODINGS:
        encode = tiktoken.get_encoding(encoding_name).encode
        cells[encoding_name] = []
        for row in manifest["test_set"]:
            english_tokens = len(encode(row["english"]))
            ainglish_tokens = len(encode(row["ainglish"]))
            cells[encoding_name].append({
                "item_id": row["item_id"],
                "form": row["form"],
                "english_tokens": english_tokens,
                "ainglish_tokens": ainglish_tokens,
                "delta": ainglish_tokens - english_tokens,
            })
        form_means[encoding_name] = {
            form: sum(cell["delta"] for cell in cells[encoding_name] if cell["form"] == form) / 8
            for form in FORMS
        }
        tokenizer_means[encoding_name] = sum(form_means[encoding_name].values()) / 2
    all_deltas = [cell["delta"] for roster in cells.values() for cell in roster]
    value = max(tokenizer_means.values())
    payload = {
        "metric": "token_delta",
        "formula_version": 1,
        "value": value,
        "value_lo": min(all_deltas),
        "value_hi": max(all_deltas),
        "panel_models": ENCODINGS,
        "per_member": [{"model": model, "value": value} for model, value in tokenizer_means.items()],
        "manifest": manifest,
    }
    return payload, {
        "value": value,
        "value_lo": min(all_deltas),
        "value_hi": max(all_deltas),
        "tokenizer_means": tokenizer_means,
        "form_means": form_means,
        "cells": cells,
    }


def main() -> None:
    attempt_path = ROOT / "attempt.json"
    result_path = ROOT / "measurement.json"
    abort_path = ROOT / "abort.json"
    if any(path.exists() for path in (attempt_path, result_path, abort_path)):
        raise SystemExit("REFUSING: this one-shot campaign already has an execution artifact")

    client = ainglish_client()
    check, _target = preflight(client)
    manifest = make_manifest(check)
    check["manifest_commitment"] = manifest_commitment(manifest)
    if len(canonical(manifest)) > 20_000:
        raise RuntimeError("manifest exceeds the register limit")
    opened = client.mint_attempt(
        SLUG,
        manifest=manifest,
        estimand=(
            "The least-favourable maximum across cl100k_base, o200k_base, and p50k_base "
            "under tiktoken 0.14.0 of the equal-form mean token_delta on 16 wholly fresh "
            "bare-may-not pairs, preserving the target original's comparator."
        ),
        admissibility_gates=[
            "fresh authenticated suggestions and current proposal/original reads precede mint",
            "the exact clean source is public at origin/main before mint",
            "the target remains a live disputed token_delta original",
            "Dexagon has not already supplied a settlement voice for this original",
            "all 16 complete pairs and individual arms are fresh against visible evidence",
            "the forms are balanced eight/eight and the tokenizer roster matches the target",
            "tiktoken 0.14.0 loads only after successful preregistration",
            "every finite result is filed once regardless of direction",
            "the result is scoped to the target's bare-English comparator and current tokenizers",
        ],
        planned_sample={
            "metric": "token_delta",
            "pairs": 16,
            "forms": check["form_counts"],
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
                "kind": "dexagon.ainglish.may-not-token-replication-abort.v1",
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
    result = {
        "kind": "dexagon.ainglish.may-not-token-dispute-replication-result.v1",
        "attempt": opened,
        "preflight": check,
        "computed": computed,
        "measurement": filed,
        "post_write_target": {
            key: fresh_target.get(key)
            for key in ("confirmed", "settlement_state", "replication_count", "disagreement_count")
        },
    }
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({
        "attempt_id": opened["attempt_id"],
        "manifest_commitment": check["manifest_commitment"],
        "value": computed["value"],
        "tokenizer_means": computed["tokenizer_means"],
        "measurement_hash": row.get("manifest_hash"),
        "reproduced_ok": row.get("reproduced_ok"),
        "settlement_eligible": row.get("settlement_eligible"),
        "post_write_target": result["post_write_target"],
    }, indent=2))


if __name__ == "__main__":
    main()
