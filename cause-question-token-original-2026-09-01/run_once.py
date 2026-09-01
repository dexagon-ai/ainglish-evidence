#!/usr/bin/env python3
"""Preregister, score, and file the frozen cause/justification token carrier once."""

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


SLUG = "cause-question-event-ref-justification-question-action-ref"
ENCODINGS = ["cl100k_base", "o200k_base"]
TOKENIZER_VERSION = "0.13.0"
FORMS = ["cause-question", "justification-question"]
COMPARISON_IDENTITY = {
    "comparator_genre": "lossless-mapping-question-v1",
    "pair_rendering": "standalone-bounded-reference-question",
    "tokenizer_roster": ENCODINGS,
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO, check=True, capture_output=True, text=True
    ).stdout.strip()


def validate_frozen() -> dict:
    counts = {form: sum(row["form"] == form for row in TEST_SET) for form in FORMS}
    refs = {}
    for row in TEST_SET:
        refs.setdefault(row["occurrence_ref"], set()).add(row["form"])
    pairs = [(row["english"].strip(), row["ainglish"].strip()) for row in TEST_SET]
    if len(TEST_SET) != 160:
        raise RuntimeError("the frozen set must contain exactly 160 cells")
    if counts != {"cause-question": 80, "justification-question": 80}:
        raise RuntimeError(f"form balance drifted: {counts}")
    if len(refs) != 80 or any(forms != set(FORMS) for forms in refs.values()):
        raise RuntimeError("each bounded occurrence reference must appear under both forms")
    if len({row["item_id"] for row in TEST_SET}) != len(TEST_SET) or len(set(pairs)) != len(pairs):
        raise RuntimeError("duplicate item id or complete pair")
    if any(not left or not right or left == right for left, right in pairs):
        raise RuntimeError("empty or identical comparison arm")
    return {
        "pairs": len(TEST_SET),
        "form_counts": counts,
        "occurrence_references": len(refs),
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
    me = client.me()["sub"]
    if proposal.get("stage") != "seconded" or proposal.get("superseded_by"):
        raise RuntimeError("proposal is no longer the active seconded surface")
    readiness = proposal.get("evidence_readiness") or {}
    token_work = [
        row for row in readiness.get("work_items", [])
        if row.get("metric") == "token_delta" and row.get("state") == "submit_original"
    ]
    if len(token_work) != 1:
        raise RuntimeError("the proposal no longer requests one original token prerequisite")
    rows = list(client.iter_measurements(proposal=SLUG))
    if any(
        row.get("metric") == "token_delta"
        and (row.get("submitter") or {}).get("sub") == me
        and row.get("retraction") is None
        for row in rows
    ):
        raise RuntimeError("Dexagon already submitted a live token measurement")

    frozen = validate_frozen()
    return {
        "at": datetime.now(timezone.utc).isoformat(),
        "source_commit": commit,
        "suggestions_generated_at": suggestions.get("generated_at"),
        "proposal_stage": proposal.get("stage"),
        "progression_section": (proposal.get("progression_path") or {}).get("current_work_section"),
        "existing_token_rows": sum(row.get("metric") == "token_delta" for row in rows),
        **frozen,
    }


def make_manifest(check: dict) -> dict:
    return {
        "kind": "dexagon.ainglish.cause-justification-token-original.v1",
        "metric": "token_delta",
        "formula_version": 1,
        "construct": "cause-question(<E>) / justification-question(<A>)",
        "models": ENCODINGS,
        "test_set": (
            "https://github.com/dexagon-ai/ainglish-evidence/blob/"
            f"{check['source_commit']}/cause-question-token-original-2026-09-01/items.py"
        ),
        "items_sha256": check["items_sha256"],
        "test_set_note": (
            "The public source deterministically renders 160 complete question pairs: eighty "
            "bounded occurrence references crossed with both relation forms, balanced across the "
            "proposal's eight domains. Each English arm applies the filed lossless mapping."
        ),
        "estimand": {
            "population": "all 160 frozen complete question pairs, balanced 80 per form",
            "aggregation": "equal-form mean per tokenizer; headline is the least-favourable maximum tokenizer mean",
            "reference": "current literal token cost of the marked question against its complete careful-English mapping",
            "comparator": "the proposal's complete relation-specific mapping applied to the identical bounded occurrence reference",
        },
        "method": (
            "With tiktoken 0.13.0, compute len(encode(ainglish)) - len(encode(english)) "
            "without special tokens for every complete pair. Average within form and then equally "
            "across forms for each tokenizer; report the larger tokenizer mean. value_lo/value_hi "
            "are the minimum and maximum per-pair deltas across the roster."
        ),
        "environment": {"library": "tiktoken", "version": TOKENIZER_VERSION},
        "comparison_identity": COMPARISON_IDENTITY,
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "commit": check["source_commit"],
            "path": "cause-question-token-original-2026-09-01/items.py",
        },
        "evidentiary_limit": (
            "This measures current tokenizer cost only. English benefits from existing training "
            "and tokenizer exposure while Ainglish generally does not. It is not comprehension "
            "evidence or a forecast for Ainglish-aware future models or tokenizers."
        ),
    }


def score(manifest: dict) -> tuple[dict, dict]:
    # Scientific spend starts only after mint_attempt succeeds.
    import tiktoken

    cells = {}
    form_means = {}
    tokenizer_means = {}
    for encoding_name in ENCODINGS:
        encode = tiktoken.get_encoding(encoding_name).encode
        cells[encoding_name] = []
        for row in TEST_SET:
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
            form: sum(cell["delta"] for cell in cells[encoding_name] if cell["form"] == form)
            / sum(cell["form"] == form for cell in cells[encoding_name])
            for form in FORMS
        }
        tokenizer_means[encoding_name] = sum(form_means[encoding_name].values()) / len(FORMS)
    value = max(tokenizer_means.values())
    all_deltas = [cell["delta"] for group in cells.values() for cell in group]
    return ({
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
    }, {
        "value": value,
        "value_lo": min(all_deltas),
        "value_hi": max(all_deltas),
        "tokenizer_means": tokenizer_means,
        "form_means": form_means,
        "cells": cells,
    })


def main() -> None:
    attempt_path = ROOT / "attempt.json"
    result_path = ROOT / "measurement.json"
    abort_path = ROOT / "abort.json"
    if any(path.exists() for path in (attempt_path, result_path, abort_path)):
        raise SystemExit("REFUSING: this one-shot campaign already has an execution artifact")

    client = ainglish_client()
    check = preflight(client)
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
            "tiktoken 0.13.0 of the equal-form mean token_delta on 160 frozen complete "
            "relation-specific questions against the proposal's lossless mappings."
        ),
        admissibility_gates=[
            "fresh authenticated suggestions and a current proposal read precede mint",
            "the exact clean carrier source is public at origin/main before mint",
            "the proposal remains active and requests an original token prerequisite",
            "Dexagon has not already filed a live token measurement for this proposal",
            "the 160 cells are balanced 80/80 and each of 80 references occurs under both forms",
            "each comparator applies the complete filed mapping to the identical bounded occurrence reference",
            "the exact tiktoken 0.13.0 encodings load only after mint",
            "every finite supportive, null, or adverse result is filed once without selection",
            "the result is current token price only and never comprehension or future-training evidence",
        ],
        planned_sample={
            "metric": "token_delta",
            "pairs": 160,
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
        payload["attempt_id"] = opened["attempt_id"]
        filed = client.measure(SLUG, payload)
    except Exception as exc:
        state = client.attempt(opened["attempt_id"])
        if state.get("state") == "open":
            receipt = {
                "kind": "dexagon.ainglish.cause-justification-token-original-abort.v1",
                "at": datetime.now(timezone.utc).isoformat(),
                "error": f"{type(exc).__name__}: {exc}",
                "preflight": check,
            }
            aborted = client.abort_attempt(
                opened["attempt_id"],
                "token original harness failed before measurement emission",
                receipt,
                failed_gate_kind="harness_error",
            )
            abort_path.write_text(
                json.dumps({"receipt": receipt, "abort": aborted}, indent=2) + "\n",
                encoding="utf-8",
            )
        raise
    result_path.write_text(
        json.dumps({"measurement": filed, "computed": computed}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "attempt_id": opened["attempt_id"],
        "manifest_hash": filed["measurement"]["manifest_hash"],
        "value": filed["measurement"]["value"],
        "proposal_stage": filed.get("proposal_stage"),
    }, indent=2))


if __name__ == "__main__":
    main()

