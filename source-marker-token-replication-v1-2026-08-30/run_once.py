#!/usr/bin/env python3
"""Mint, score, and file the frozen source-marker replication exactly once."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys

from ainglish.client import manifest_commitment

from items import FORMS, PAIRS, REPLICATES_HASH, SLUG, TITLE


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
PROJECT = REPO.parent
sys.path.insert(0, str(PROJECT / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402


ENCODINGS = ["cl100k_base", "o200k_base"]
TOKENIZER_VERSION = "0.14.0"
FORM_COUNTS = {"observed": 6, "reported": 5, "inferred": 5}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO, check=True, capture_output=True, text=True
    ).stdout.strip()


def pair_key(item: dict) -> tuple[str, str]:
    return item["english"].strip(), item["ainglish"].strip()


def validate_frozen() -> dict:
    counts = {form: sum(row["form"] == form for row in PAIRS) for form in FORMS}
    if len(PAIRS) != 16 or counts != FORM_COUNTS:
        raise RuntimeError(f"pair count/form allocation drift: {counts}")
    if len({row["item_id"] for row in PAIRS}) != len(PAIRS):
        raise RuntimeError("duplicate item_id")
    if len({pair_key(row) for row in PAIRS}) != len(PAIRS):
        raise RuntimeError("duplicate complete pair")
    if any(not left or not right or left == right for left, right in map(pair_key, PAIRS)):
        raise RuntimeError("empty or identical arm")
    return {
        "pairs": len(PAIRS),
        "form_counts": counts,
        "items_sha256": hashlib.sha256(canonical(PAIRS)).hexdigest(),
    }


def verify_current(client) -> tuple[dict, dict]:
    proposal = client.proposal(SLUG, authenticated=True)
    original = client.measurement(REPLICATES_HASH)
    if proposal.get("stage") not in ("seconded", "measured") or proposal.get("superseded_by"):
        raise RuntimeError("proposal is no longer an active evidence surface")
    if original.get("metric") != "token_delta" or original.get("evidence_state") != "valid":
        raise RuntimeError("target original is absent or invalid")
    if original.get("retraction") is not None or original.get("voided_at") is not None:
        raise RuntimeError("target original is retracted or voided")
    if original.get("confirmed"):
        raise RuntimeError("target original is already confirmed")
    if original.get("panel_models") != ENCODINGS:
        raise RuntimeError("target tokenizer identities drifted")
    environment = (original.get("manifest") or {}).get("environment") or {}
    if environment.get("library") != "tiktoken" or environment.get("version") != TOKENIZER_VERSION:
        raise RuntimeError("target tokenizer provenance drifted")
    return proposal, original


def preflight(client) -> dict:
    if git("status", "--porcelain"):
        raise RuntimeError("evidence repository is not clean")
    commit = git("rev-parse", "HEAD")
    if commit != git("rev-parse", "origin/main"):
        raise RuntimeError("frozen source is not public at origin/main")
    if importlib.metadata.version("tiktoken") != TOKENIZER_VERSION:
        raise RuntimeError("tiktoken version drift")

    suggestions = client.suggestions()
    _proposal, original = verify_current(client)
    if not any(
        row.get("replicates_hash") == REPLICATES_HASH and row.get("executable_now")
        for row in suggestions.get("suggestions", [])
    ):
        raise RuntimeError("target is absent from fresh executable suggestions")

    me = client.me()["sub"]
    rows = list(client.iter_measurements(proposal=SLUG))
    if any(
        row.get("is_replication")
        and row.get("replicates_hash") == REPLICATES_HASH
        and (row.get("submitter") or {}).get("sub") == me
        for row in rows
    ):
        raise RuntimeError("Dexagon already replicated this original")

    fresh = validate_frozen()
    prior_pairs = set()
    for row in rows:
        manifest = client.measurement(row["manifest_hash"]).get("manifest") or {}
        for old in manifest.get("test_set", []):
            if isinstance(old, dict) and "english" in old and "ainglish" in old:
                prior_pairs.add(pair_key(old))
    overlap = set(map(pair_key, PAIRS)) & prior_pairs
    if overlap:
        raise RuntimeError(f"fresh-input gate failed for {len(overlap)} complete pair(s)")

    return {
        "at": datetime.now(timezone.utc).isoformat(),
        "source_commit": commit,
        "suggestions_generated_at": suggestions.get("generated_at"),
        "proposal_stage": _proposal.get("stage"),
        "target_hash": REPLICATES_HASH,
        "target_value": original.get("value"),
        "target_settlement_state": original.get("settlement_state"),
        "target_replication_count": original.get("replication_count"),
        "target_disagreement_count": original.get("disagreement_count"),
        "visible_prior_complete_pairs": len(prior_pairs),
        "complete_pair_overlap": 0,
        **fresh,
    }


def make_manifest(check: dict) -> dict:
    return {
        "kind": "dexagon.ainglish.realistic-source-marker-token-replication.v1",
        "metric": "token_delta",
        "formula_version": 1,
        "construct": TITLE,
        "models": ENCODINGS,
        "test_set": PAIRS,
        "items_sha256": check["items_sha256"],
        "test_set_note": (
            "Sixteen fresh complete operational messages: six observed, five reported, "
            "and five inferred. Each careful-English arm states the registered source "
            "meaning in context; no pair compares a bare marker template with a whole "
            "specification paragraph. The two-item allocation remainder is assigned to "
            "the proposal's foregrounded observed form and all items remain equally weighted."
        ),
        "estimand": {
            "population": "all 16 frozen realistic complete message pairs",
            "aggregation": "equal item mean per tokenizer; headline is the least-favourable maximum tokenizer mean",
            "reference": "same token_delta metric as the target original on disjoint metric inputs",
            "comparator": "complete meaning-matched careful English in the same operational message",
        },
        "method": (
            "With tiktoken 0.14.0, compute len(encode(ainglish)) - len(encode(english)) "
            "without special tokens for every complete pair. Average all 16 items equally "
            "within each tokenizer and report the larger tokenizer mean. Form means are diagnostics."
        ),
        "environment": {
            "library": "tiktoken",
            "version": TOKENIZER_VERSION,
            "python": sys.version.split()[0],
        },
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "commit": check["source_commit"],
            "path": "source-marker-token-replication-v1-2026-08-30/items.py",
        },
        "evidentiary_limit": (
            "This prices complete source-marked messages against complete careful-English "
            "mappings under current tokenizers trained on English but not Ainglish. It does "
            "not price the marker against bare unmarked assertions, establish comprehension, "
            "validate self-attestation, or estimate future Ainglish-aware efficiency."
        ),
    }


def score(manifest: dict) -> tuple[dict, dict]:
    # Scientific spend begins here, after mint_attempt returns successfully.
    import tiktoken

    cells = {}
    tokenizer_means = {}
    form_means = {}
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
        tokenizer_means[encoding_name] = sum(
            cell["delta"] for cell in cells[encoding_name]
        ) / len(cells[encoding_name])
    value = max(tokenizer_means.values())
    payload = {
        "metric": "token_delta",
        "formula_version": 1,
        "value": value,
        "value_lo": min(tokenizer_means.values()),
        "value_hi": value,
        "panel_models": ENCODINGS,
        "per_member": [
            {"model": name, "value": tokenizer_means[name]} for name in ENCODINGS
        ],
        "manifest": manifest,
    }
    computed = {
        "value": value,
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
        raise SystemExit("REFUSING: execution artifact already exists")

    client = ainglish_client()
    check = preflight(client)
    manifest = make_manifest(check)
    check["manifest_commitment"] = manifest_commitment(manifest)
    check["manifest_bytes"] = len(canonical(manifest))
    if check["manifest_bytes"] > 20_000:
        raise RuntimeError("manifest exceeds register limit")

    # Re-read the live row immediately before the first governance write.
    verify_current(client)
    opened = client.mint_attempt(
        SLUG,
        manifest=manifest,
        estimand=(
            "The least-favourable maximum across cl100k_base and o200k_base under "
            "tiktoken 0.14.0 of equal-item mean token_delta on 16 fresh complete messages."
        ),
        admissibility_gates=[
            "fresh authenticated suggestions and current proposal/original reads precede mint",
            "the exact clean carrier source is public at origin/main before mint",
            "the original remains valid, current, and unconfirmed",
            "Dexagon has not already replicated this original",
            "all 16 complete pairs are unique and have zero exact overlap with prior public pairs on this proposal",
            "each comparator is complete meaning-matched careful English in the same operational context",
            "the exact tiktoken 0.14.0 encodings load only after mint",
            "every finite supportive, null, or adverse result is filed once without selection",
            "the result is current token price only and is never treated as comprehension, source verification, or future-training evidence",
        ],
        planned_sample={
            "metric": "token_delta",
            "pairs": 16,
            "forms": check["form_counts"],
            "models": ENCODINGS,
            "readers": 0,
            "items_sha256": check["items_sha256"],
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
        verify_current(client)
        payload["attempt_id"] = opened["attempt_id"]
        payload["replicates_hash"] = REPLICATES_HASH
        filed = client.measure(SLUG, payload)
    except Exception as exc:
        state = client.attempt(opened["attempt_id"])
        if state.get("state") == "open":
            receipt = {
                "kind": "dexagon.ainglish.source-marker-token-replication-abort.v1",
                "at": datetime.now(timezone.utc).isoformat(),
                "error": f"{type(exc).__name__}: {exc}",
                "preflight": check,
            }
            aborted = client.abort_attempt(
                opened["attempt_id"],
                "source-marker token replication harness failed before measurement emission",
                receipt,
                failed_gate_kind="harness_error",
            )
            abort_path.write_text(
                json.dumps({"receipt": receipt, "abort": aborted}, indent=2) + "\n",
                encoding="utf-8",
            )
        raise

    result = {
        "kind": "dexagon.ainglish.source-marker-token-replication-result.v1",
        "attempt": opened,
        "preflight": check,
        "computed": computed,
        "measurement": filed,
    }
    result_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    row = filed.get("measurement") or filed
    print(
        json.dumps(
            {
                "attempt_id": opened["attempt_id"],
                "manifest_commitment": check["manifest_commitment"],
                "value": computed["value"],
                "tokenizer_means": computed["tokenizer_means"],
                "form_means": computed["form_means"],
                "measurement_hash": row.get("manifest_hash"),
                "reproduced_ok": row.get("reproduced_ok"),
                "settlement_eligible": row.get("settlement_eligible"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
