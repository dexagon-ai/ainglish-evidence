#!/usr/bin/env python3
"""Mint, score, and file one frozen flagship token replication exactly once."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys

from ainglish.client import manifest_commitment

from items import TARGETS


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
PROJECT = REPO.parent
sys.path.insert(0, str(PROJECT / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402


ENCODINGS = ["cl100k_base", "o200k_base"]
TOKENIZER_VERSION = "0.14.0"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO, check=True, capture_output=True, text=True
    ).stdout.strip()


def pair_key(item: dict) -> tuple[str, str]:
    return item["english"].strip(), item["ainglish"].strip()


def validate_frozen(target: dict) -> dict:
    pairs = target["pairs"]
    forms = target["forms"]
    counts = {form: sum(row["form"] == form for row in pairs) for form in forms}
    expected = 16 // len(forms)
    if len(pairs) != 16 or counts != {form: expected for form in forms}:
        raise RuntimeError(f"pair count/form balance drift: {counts}")
    if len({row["item_id"] for row in pairs}) != len(pairs):
        raise RuntimeError("duplicate item_id")
    if len({pair_key(row) for row in pairs}) != len(pairs):
        raise RuntimeError("duplicate complete pair")
    if any(not left or not right or left == right for left, right in map(pair_key, pairs)):
        raise RuntimeError("empty or identical arm")
    return {
        "pairs": len(pairs),
        "form_counts": counts,
        "items_sha256": hashlib.sha256(canonical(pairs)).hexdigest(),
    }


def preflight(client, target: dict) -> tuple[dict, dict, dict]:
    if git("status", "--porcelain"):
        raise RuntimeError("evidence repository is not clean")
    commit = git("rev-parse", "HEAD")
    if commit != git("rev-parse", "origin/main"):
        raise RuntimeError("frozen source is not public at origin/main")
    if importlib.metadata.version("tiktoken") != TOKENIZER_VERSION:
        raise RuntimeError("tiktoken version drift")

    suggestions = client.suggestions()
    proposal = client.proposal(target["slug"], authenticated=True)
    original = client.measurement(target["replicates_hash"])
    me = client.me()["sub"]
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

    rows = list(client.iter_measurements(proposal=target["slug"]))
    if any(
        row.get("is_replication")
        and row.get("replicates_hash") == target["replicates_hash"]
        and (row.get("submitter") or {}).get("sub") == me
        for row in rows
    ):
        raise RuntimeError("Dexagon already replicated this original")

    fresh = validate_frozen(target)
    prior_pairs = set()
    for row in rows:
        manifest = client.measurement(row["manifest_hash"]).get("manifest") or {}
        for old in manifest.get("test_set", []):
            if isinstance(old, dict) and "english" in old and "ainglish" in old:
                prior_pairs.add(pair_key(old))
    overlap = set(map(pair_key, target["pairs"])) & prior_pairs
    if overlap:
        raise RuntimeError(f"fresh-input gate failed for {len(overlap)} complete pair(s)")

    check = {
        "at": datetime.now(timezone.utc).isoformat(),
        "source_commit": commit,
        "suggestions_generated_at": suggestions.get("generated_at"),
        "proposal_stage": proposal.get("stage"),
        "target_hash": target["replicates_hash"],
        "target_value": original.get("value"),
        "target_settlement_state": original.get("settlement_state"),
        "target_replication_count": original.get("replication_count"),
        "target_disagreement_count": original.get("disagreement_count"),
        "visible_prior_complete_pairs": len(prior_pairs),
        "complete_pair_overlap": 0,
        **fresh,
    }
    return check, proposal, original


def make_manifest(name: str, target: dict, check: dict) -> dict:
    return {
        "kind": "dexagon.ainglish.flagship-realistic-token-replication.v1",
        "metric": "token_delta",
        "formula_version": 1,
        "construct": target["title"],
        "models": ENCODINGS,
        "test_set": target["pairs"],
        "items_sha256": check["items_sha256"],
        "test_set_note": (
            "Sixteen fresh complete operational messages, balanced by form where the construct "
            "has two forms. Each English arm states the registered meaning in context; no arm "
            "compares a bare marker template with a specification paragraph."
        ),
        "estimand": {
            "population": "all 16 frozen realistic complete message pairs",
            "aggregation": "equal item mean per tokenizer; headline is the least-favourable maximum tokenizer mean",
            "reference": "same token_delta metric as the target original on disjoint metric inputs",
            "comparator": "complete meaning-matched careful English in the same operational message",
        },
        "method": (
            "With tiktoken 0.14.0, compute len(encode(ainglish)) - len(encode(english)) "
            "without special tokens for every complete pair. Average equally by form and then "
            "across forms within each tokenizer; report the larger tokenizer mean."
        ),
        "environment": {
            "library": "tiktoken",
            "version": TOKENIZER_VERSION,
            "python": sys.version.split()[0],
        },
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "commit": check["source_commit"],
            "path": f"flagship-token-replications-v1-2026-08-30/items.py#{name}",
        },
        "evidentiary_limit": (
            "This prices the forms under current tokenizers trained on English but not on "
            "Ainglish. It is not comprehension evidence and cannot determine the efficiency "
            "of future models or tokenizers trained on ratified Ainglish."
        ),
    }


def score(manifest: dict, forms: list[str]) -> tuple[dict, dict]:
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
            for form in forms
        }
        tokenizer_means[encoding_name] = sum(form_means[encoding_name].values()) / len(forms)
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
    if len(sys.argv) != 2 or sys.argv[1] not in TARGETS:
        raise SystemExit("usage: run_once.py {idempotent|parallel|behalf}")
    name = sys.argv[1]
    target = TARGETS[name]
    attempt_path = ROOT / f"{name}.attempt.json"
    result_path = ROOT / f"{name}.measurement.json"
    abort_path = ROOT / f"{name}.abort.json"
    if any(path.exists() for path in (attempt_path, result_path, abort_path)):
        raise SystemExit(f"REFUSING: {name} already has an execution artifact")

    client = ainglish_client()
    check, _proposal, _original = preflight(client, target)
    manifest = make_manifest(name, target, check)
    check["manifest_commitment"] = manifest_commitment(manifest)
    check["manifest_bytes"] = len(canonical(manifest))
    if check["manifest_bytes"] > 20_000:
        raise RuntimeError("manifest exceeds register limit")

    opened = client.mint_attempt(
        target["slug"],
        manifest=manifest,
        estimand=(
            "The least-favourable maximum across cl100k_base and o200k_base under "
            "tiktoken 0.14.0 of mean token_delta on 16 fresh complete realistic messages."
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
            "the result is current token price only and is never treated as comprehension or future-training evidence",
        ],
        planned_sample={
            "metric": "token_delta",
            "pairs": 16,
            "forms": check["form_counts"],
            "models": ENCODINGS,
            "readers": 0,
            "items_sha256": check["items_sha256"],
        },
        proposal_revision=target["slug"],
        store_manifest=True,
    )["attempt"]
    attempt_path.write_text(
        json.dumps({"attempt": opened, "preflight": check}, indent=2) + "\n",
        encoding="utf-8",
    )
    try:
        payload, computed = score(manifest, target["forms"])
        payload["attempt_id"] = opened["attempt_id"]
        payload["replicates_hash"] = target["replicates_hash"]
        filed = client.measure(target["slug"], payload)
    except Exception as exc:
        state = client.attempt(opened["attempt_id"])
        if state.get("state") == "open":
            receipt = {
                "kind": "dexagon.ainglish.flagship-token-replication-abort.v1",
                "at": datetime.now(timezone.utc).isoformat(),
                "error": f"{type(exc).__name__}: {exc}",
                "preflight": check,
            }
            aborted = client.abort_attempt(
                opened["attempt_id"],
                "flagship token replication harness failed before measurement emission",
                receipt,
                failed_gate_kind="harness_error",
            )
            abort_path.write_text(
                json.dumps({"receipt": receipt, "abort": aborted}, indent=2) + "\n",
                encoding="utf-8",
            )
        raise

    result = {
        "kind": "dexagon.ainglish.flagship-token-replication-result.v1",
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
                "name": name,
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
