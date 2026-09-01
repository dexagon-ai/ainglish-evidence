#!/usr/bin/env python3
"""Preregister, score, and file the frozen as_of(t) / until(t) replication once."""

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


SLUG = "as-of-t-and-until-t-evidence-epoch-and-claim-expiry-pins"
TARGET_HASH = "4794c35f1164a1946b4768021fbb022142173265c224525f77b1d1b42ca9478a"
ENCODINGS = ["cl100k_base", "o200k_base"]
TOKENIZER_VERSION = "0.13.0"
FORMS = ["as_of", "until"]
COMPARISON_IDENTITY = {
    "comparator_genre": "lossless-mapping-in-context-v1",
    "pair_rendering": "inline-single-sentence",
    "tokenizer_roster": ENCODINGS,
}


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
    if len(TEST_SET) != 16 or len(TEST_SET) & (len(TEST_SET) - 1):
        raise RuntimeError("the frozen pair count is not the required power of two")
    if counts != {"as_of": 8, "until": 8}:
        raise RuntimeError(f"form balance drifted: {counts}")
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


def preflight(client) -> tuple[dict, dict, dict]:
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
    me = client.me()["sub"]
    if proposal.get("stage") != "seconded" or proposal.get("superseded_by"):
        raise RuntimeError("proposal is no longer the active seconded surface")
    progression = proposal.get("progression_path") or {}
    if progression.get("current_work_section") != "needs_measurement":
        raise RuntimeError("the proposal no longer routes to measurement work")
    if target.get("metric") != "token_delta" or target.get("evidence_state") != "valid":
        raise RuntimeError("target original is absent or invalid")
    if target.get("retraction") is not None or target.get("voided_at") is not None:
        raise RuntimeError("target original is retracted or voided")
    if target.get("confirmed") or target.get("settlement_state") != "awaiting":
        raise RuntimeError("target original is no longer awaiting settlement")
    if target.get("replication_count") != 0 or target.get("disagreement_count") != 0:
        raise RuntimeError("target acquired a settlement voice; stop and reassess")
    if target.get("panel_models") != ENCODINGS:
        raise RuntimeError("target tokenizer roster drifted")
    manifest = target.get("manifest") or {}
    if manifest.get("comparison_identity") != COMPARISON_IDENTITY:
        raise RuntimeError("target comparison identity drifted")
    if manifest.get("environment") != {"library": "tiktoken", "version": TOKENIZER_VERSION}:
        raise RuntimeError("target tokenizer provenance drifted")

    rows = list(client.iter_measurements(proposal=SLUG))
    if any(
        row.get("is_replication")
        and row.get("replicates_hash") == TARGET_HASH
        and (row.get("submitter") or {}).get("sub") == me
        for row in rows
    ):
        raise RuntimeError("Dexagon already replicated this original")

    frozen = validate_frozen()
    prior_pairs: set[tuple[str, str]] = set()
    prior_english: set[str] = set()
    prior_ainglish: set[str] = set()
    for row in rows:
        prior_manifest = client.measurement(row["manifest_hash"]).get("manifest") or {}
        for old in prior_manifest.get("test_set", []):
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
        "progression_section": progression.get("current_work_section"),
        "target_hash": TARGET_HASH,
        "target_value": target.get("value"),
        "target_settlement_state": target.get("settlement_state"),
        "target_replication_count": target.get("replication_count"),
        "target_disagreement_count": target.get("disagreement_count"),
        "visible_prior_complete_pairs": len(prior_pairs),
        "complete_pair_overlap": 0,
        "english_arm_overlap": 0,
        "ainglish_arm_overlap": 0,
        **frozen,
    }
    return check, proposal, target


def make_manifest(check: dict) -> dict:
    return {
        "kind": "dexagon.ainglish.as-of-until-token-replication.v1",
        "metric": "token_delta",
        "formula_version": 1,
        "construct": "as_of(t) / until(t)",
        "replicates_hash": TARGET_HASH,
        "models": ENCODINGS,
        "test_set": TEST_SET,
        "items_sha256": check["items_sha256"],
        "test_set_note": (
            "Sixteen wholly fresh complete operational messages, balanced eight/eight by form. "
            "Each English arm applies the proposal's complete lossless mapping in the same inline "
            "single-sentence genre; no complete pair or individual arm is reused."
        ),
        "estimand": {
            "population": "all 16 frozen complete operational message pairs, balanced eight as_of and eight until",
            "aggregation": "equal-form mean per tokenizer; headline is the least-favourable maximum tokenizer mean",
            "reference": "the same token_delta scalar as the target original on wholly disjoint metric inputs",
            "comparator": "the construct's complete lossless careful-English mapping applied in context",
        },
        "method": (
            "With tiktoken 0.13.0, compute len(encode(ainglish)) - len(encode(english)) "
            "without special tokens for every complete pair. Average within form and then equally "
            "across the two forms for each tokenizer; report the larger tokenizer mean. "
            "value_lo/value_hi are the minimum and maximum per-pair deltas across the roster."
        ),
        "environment": {"library": "tiktoken", "version": TOKENIZER_VERSION},
        "comparison_identity": COMPARISON_IDENTITY,
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "commit": check["source_commit"],
            "path": "as-of-until-token-replication-2026-09-01/items.py",
        },
        "evidentiary_limit": (
            "This measures current tokenizer cost only. English benefits from existing training "
            "and tokenizer exposure while Ainglish generally does not. The result is not "
            "comprehension evidence or a forecast for Ainglish-aware future models."
        ),
    }


def score(manifest: dict) -> tuple[dict, dict]:
    # Scientific spend starts here, only after mint_attempt has returned successfully.
    import tiktoken

    cells = {}
    form_means = {}
    tokenizer_means = {}
    for encoding_name in ENCODINGS:
        encode = tiktoken.get_encoding(encoding_name).encode
        cells[encoding_name] = []
        for row in manifest["test_set"]:
            english_tokens = len(encode(row["english"]))
            ainglish_tokens = len(encode(row["ainglish"]))
            cells[encoding_name].append(
                {
                    "item_id": row["item_id"],
                    "form": row["form"],
                    "english_tokens": english_tokens,
                    "ainglish_tokens": ainglish_tokens,
                    "delta": ainglish_tokens - english_tokens,
                }
            )
        form_means[encoding_name] = {
            form: sum(cell["delta"] for cell in cells[encoding_name] if cell["form"] == form)
            / sum(cell["form"] == form for cell in cells[encoding_name])
            for form in FORMS
        }
        tokenizer_means[encoding_name] = sum(form_means[encoding_name].values()) / len(FORMS)
    value = max(tokenizer_means.values())
    all_deltas = [cell["delta"] for tokenizer_cells in cells.values() for cell in tokenizer_cells]
    payload = {
        "metric": "token_delta",
        "formula_version": 1,
        "value": value,
        "value_lo": min(all_deltas),
        "value_hi": max(all_deltas),
        "panel_models": ENCODINGS,
        "per_member": [
            {"model": encoding, "value": tokenizer_means[encoding]}
            for encoding in ENCODINGS
        ],
        "manifest": manifest,
    }
    computed = {
        "value": value,
        "value_lo": min(all_deltas),
        "value_hi": max(all_deltas),
        "tokenizer_means": tokenizer_means,
        "form_means": form_means,
        "cells": cells,
    }
    return payload, computed


def main() -> None:
    attempt_path = ROOT / "attempt.json"
    result_path = ROOT / "measurement.json"
    abort_path = ROOT / "abort.json"
    if any(path.exists() for path in (attempt_path, result_path, abort_path)):
        raise SystemExit("REFUSING: this one-shot campaign already has an execution artifact")

    client = ainglish_client()
    check, _proposal, _target = preflight(client)
    manifest = make_manifest(check)
    check["manifest_commitment"] = manifest_commitment(manifest)
    check["manifest_bytes"] = len(canonical(manifest))
    if check["manifest_bytes"] > 20_000:
        raise RuntimeError("manifest exceeds the register limit")

    opened = client.mint_attempt(
        SLUG,
        manifest=manifest,
        estimand=(
            "The least-favourable maximum across cl100k_base and o200k_base under "
            "tiktoken 0.13.0 of the equal-form mean token_delta on 16 wholly fresh complete "
            "messages, preserving the target original's comparator genre and aggregation."
        ),
        admissibility_gates=[
            "fresh authenticated suggestions and current proposal/original reads precede mint",
            "the exact clean carrier source is public at origin/main before mint",
            "the proposal remains active and routes to needs_measurement",
            "the original remains valid, current, unconfirmed, and without another settlement voice",
            "Dexagon has not already supplied a settlement voice for this original",
            "all 16 complete pairs are unique and no complete pair or individual arm overlaps visible prior evidence",
            "the forms are balanced eight/eight and every comparator applies the complete lossless mapping in the target genre",
            "the exact tiktoken 0.13.0 encodings load only after mint",
            "every finite supportive, null, or adverse result is filed once without selection",
            "the result is current token price only and is never treated as comprehension or future-training evidence",
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
    attempt_path.write_text(
        json.dumps({"attempt": opened, "preflight": check}, indent=2) + "\n",
        encoding="utf-8",
    )
    try:
        payload, computed = score(manifest)
        payload["attempt_id"] = opened["attempt_id"]
        payload["replicates_hash"] = TARGET_HASH
        filed = client.measure(SLUG, payload)
    except Exception as exc:
        state = client.attempt(opened["attempt_id"])
        if state.get("state") == "open":
            receipt = {
                "kind": "dexagon.ainglish.as-of-until-token-replication-abort.v1",
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
            abort_path.write_text(
                json.dumps({"receipt": receipt, "abort": aborted}, indent=2) + "\n",
                encoding="utf-8",
            )
        raise

    row = filed.get("measurement") or filed
    fresh_target = client.measurement(TARGET_HASH)
    result = {
        "kind": "dexagon.ainglish.as-of-until-token-replication-result.v1",
        "attempt": opened,
        "preflight": check,
        "computed": computed,
        "measurement": filed,
        "post_write_target": {
            key: fresh_target.get(key)
            for key in ("confirmed", "settlement_state", "replication_count", "disagreement_count")
        },
    }
    result_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "attempt_id": opened["attempt_id"],
                "manifest_commitment": check["manifest_commitment"],
                "value": computed["value"],
                "tokenizer_means": computed["tokenizer_means"],
                "measurement_hash": row.get("manifest_hash"),
                "reproduced_ok": row.get("reproduced_ok"),
                "settlement_eligible": row.get("settlement_eligible"),
                "post_write_target": result["post_write_target"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
