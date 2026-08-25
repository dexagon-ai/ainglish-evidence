#!/usr/bin/env python3
"""Mint, run, and file the preference-valence token prerequisite exactly once."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import urllib.parse

from ainglish.client import manifest_commitment


ROOT = Path(__file__).resolve().parent
EVIDENCE_REPO = ROOT.parent
SCRIPTS = EVIDENCE_REPO.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402


SLUG = "rather-not-fine-either-way-would-welcome-you-don-t-have-to-s"
TOKENIZER_VERSION = "0.13.0"
ENCODINGS = ("cl100k_base", "o200k_base", "p50k_base")
MODELS = tuple(f"tiktoken/{name}" for name in ENCODINGS)
RECEIPT = ROOT / "token-delta-receipt.json"
ABORT_RECEIPT = ROOT / "token-delta-abort-receipt.json"
PREDECESSOR_ATTEMPTS = (
    "38f98e27-d19d-4445-9a29-e484f5478b63",
    "4d7c9c81-09ca-4697-889b-9c48b4344f6c",
    "6cb1a836-fc98-4e98-9399-bd00c50b5b82",
)

BASES = (
    "You don't need to add another regression test",
    "There's no need to update the changelog",
    "You don't have to review the generated files",
    "You aren't required to attend the planning call",
    "You don't need to send a separate status note",
    "There's no need to bring a printed copy",
    "You don't have to reorder the replacement cable",
    "You aren't required to polish the draft diagrams",
    "You don't need to rerun the completed audit",
    "There's no need to reserve a larger meeting room",
    "You don't have to translate the appendix",
    "You aren't required to archive the scratch logs",
)

FORMS = {
    "rather-not": {
        "marker": ", rather-not.",
        "control": ", but I'd rather you didn't.",
    },
    "fine-either-way": {
        "marker": ", fine-either-way.",
        "control": ", either way is fine.",
    },
    "would-welcome": {
        "marker": ", would-welcome.",
        "control": ", but I'd welcome it.",
    },
}


def git_output(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=EVIDENCE_REPO, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    ).stdout.strip()


def source_state() -> dict:
    if git_output("status", "--porcelain"):
        raise RuntimeError("evidence repository is not clean; source is not frozen")
    commit = git_output("rev-parse", "HEAD")
    if commit != git_output("rev-parse", "origin/main"):
        raise RuntimeError("frozen source commit is not published at origin/main")
    path = Path(__file__).resolve()
    relative = path.relative_to(EVIDENCE_REPO)
    return {
        "commit": commit,
        "path": str(relative),
        "url": f"https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{commit}/{relative}",
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def build_manifest(source: dict | None = None) -> dict:
    rows = []
    for form, suffixes in FORMS.items():
        for base in BASES:
            rows.append({
                "form": form,
                "english": base + suffixes["control"],
                "ainglish": base + suffixes["marker"],
            })
    assert len(rows) == 36 and len({(row["english"], row["ainglish"]) for row in rows}) == 36
    manifest = {
        "metric": "token_delta",
        "formula_version": 1,
        "construct": "rather-not / fine-either-way / would-welcome",
        "models": list(MODELS),
        "environment": {"library": "tiktoken", "version": TOKENIZER_VERSION},
        "test_set": rows,
        "seed": "none — deterministic tokenizer counts, no sampling",
        "population": "twelve operational releases from obligation crossed with all three preference states",
        "selection": (
            "The base release is byte-identical within each three-form block. The careful-control "
            "suffixes are fixed verbatim by the proposal contract; no paraphrase substitution is admissible."
        ),
        "method": (
            "For each pinned tokenizer, compute len(encode(ainglish))-len(encode(english)) per pair. "
            "Average twelve rows within each form and then give the three form means equal weight. "
            "The filed scalar is the maximum pooled mean across tokenizers; value_lo/value_hi span "
            "the tokenizer means. Per-form means and all cells are retained."
        ),
        "acceptance": {"metric": "token_delta", "at_most": 0},
        "execution_history": {
            "terminal_predecessor_attempts": list(PREDECESSOR_ATTEMPTS),
            "note": (
                "All three predecessors aborted before a measurement was accepted: first on an "
                "invalid versioned tokenizer roster identity, then twice on obsolete successor-link "
                "handling. Terminal attempts are immutable, so this clean attempt does not rewrite them."
            ),
        },
    }
    if source is not None:
        manifest["source"] = source
    return manifest


def preflight(client, manifest: dict) -> dict:
    suggestions = client.suggestions()
    proposal = client.proposal(SLUG, authenticated=True)
    if proposal.get("stage") != "seconded":
        raise RuntimeError(f"proposal stage is {proposal.get('stage')!r}, not freshly seconded")
    if any(row.get("metric") == "token_delta" and row.get("voided_at") is None for row in proposal.get("measurements", [])):
        raise RuntimeError("a live token_delta row appeared; refusing a duplicate original")
    if any(row.get("state") == "open" for row in proposal.get("attempts", [])):
        raise RuntimeError("an open attempt appeared; refusing to race it")
    if not suggestions["budgets"]["attempts"]["remaining"] or not suggestions["budgets"]["measurements"]["remaining"]:
        raise RuntimeError("authenticated attempt or measurement budget is exhausted")
    rows = manifest["test_set"]
    if len(rows) != 36 or {row["form"] for row in rows} != set(FORMS):
        raise RuntimeError("frozen 36-row three-form design is incomplete")
    if any(sum(row["form"] == form for row in rows) != 12 for form in FORMS):
        raise RuntimeError("each form must contribute exactly twelve pairs")
    for row in rows:
        marker = FORMS[row["form"]]["marker"]
        control = FORMS[row["form"]]["control"]
        if not row["ainglish"].endswith(marker) or not row["english"].endswith(control):
            raise RuntimeError("a row diverged from its contract-pinned suffix")
        if row["ainglish"][:-len(marker)] != row["english"][:-len(control)]:
            raise RuntimeError("a pair's obligation-release base is not byte-identical")
    return {
        "suggestions_generated_at": suggestions.get("generated_at"),
        "proposal_stage": proposal.get("stage"),
        "rows": len(rows),
        "per_form": 12,
        "manifest_commitment": manifest_commitment(manifest),
    }


def score(manifest: dict) -> tuple[dict, dict]:
    import tiktoken  # Imported only after attempt mint.

    actual = importlib.metadata.version("tiktoken")
    if actual != TOKENIZER_VERSION:
        raise RuntimeError(f"tiktoken {actual!r} != pinned {TOKENIZER_VERSION!r}")
    cells = {}
    form_means = {}
    pooled_means = {}
    for encoding_name, roster_name in zip(ENCODINGS, MODELS, strict=True):
        encode = tiktoken.get_encoding(encoding_name).encode
        rows = [
            {
                "item": index + 1,
                "form": row["form"],
                "delta": len(encode(row["ainglish"])) - len(encode(row["english"])),
            }
            for index, row in enumerate(manifest["test_set"])
        ]
        cells[roster_name] = rows
        form_means[roster_name] = {
            form: sum(row["delta"] for row in rows if row["form"] == form) / 12
            for form in FORMS
        }
        pooled_means[roster_name] = sum(form_means[roster_name].values()) / 3
    value = max(pooled_means.values())
    payload = {
        "metric": "token_delta",
        "formula_version": 1,
        "value": value,
        "value_lo": min(pooled_means.values()),
        "value_hi": max(pooled_means.values()),
        "panel_models": list(MODELS),
        "per_member": [{"model": model, "value": pooled_means[model]} for model in MODELS],
        "manifest": manifest,
    }
    return payload, {"value": value, "pooled_means": pooled_means, "form_means": form_means, "cells": cells}


def abort(client, attempt_id: str, message: str, details: dict) -> None:
    receipt = {
        "kind": "ainglish.token-delta.abort-receipt.v1",
        "at": datetime.now(timezone.utc).isoformat(),
        "attempt_id": attempt_id,
        "failed_gate_kind": "harness_error",
        "failed_gate": message,
        "details": details,
    }
    encoded = json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    ABORT_RECEIPT.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    client.post(
        f"/api/v1/attempts/{urllib.parse.quote(attempt_id, safe='')}/abort",
        {
            "failed_gate_kind": "harness_error",
            "failed_gate": message,
            "preflight_receipt": encoded,
            "preflight_receipt_hash": hashlib.sha256(encoded.encode()).hexdigest(),
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--submit", action="store_true")
    args = parser.parse_args()
    if not args.submit:
        spec = build_manifest()
        print(json.dumps({
            "status": "frozen-not-run",
            "manifest_without_source": manifest_commitment(spec),
            "rows": len(spec["test_set"]),
            "per_form": 12,
        }, indent=2))
        return
    if RECEIPT.exists():
        raise SystemExit("REFUSING: a completed local receipt already exists")
    if ABORT_RECEIPT.exists():
        predecessor_receipt = json.loads(ABORT_RECEIPT.read_text(encoding="utf-8"))
        if predecessor_receipt.get("attempt_id") != PREDECESSOR_ATTEMPTS[-1]:
            raise SystemExit("REFUSING: latest local aborted predecessor is not the declared terminal attempt")
    manifest = build_manifest(source_state())
    client = ainglish_client()
    receipt = preflight(client, manifest)
    opened = client.mint_attempt(
        SLUG,
        manifest=manifest,
        estimand=(
            "The least-favourable maximum across cl100k_base, o200k_base and p50k_base 0.13.0 "
            "of the equal-form pooled token_delta on 36 fixed minimal pairs, twelve per marker, "
            "against the exact careful-control suffixes declared by the proposal."
        ),
        admissibility_gates=[
            "the committed test_set contains exactly 36 unique complete pairs, twelve per form",
            "each pair has a byte-identical obligation-release base and its contract-pinned suffixes",
            "the clean runner is published at origin/main before minting",
            "all three pinned tiktoken encodings load only after the server stores the manifest",
            "the scalar pools all 36 pairs with equal form weight; per-form values remain diagnostics",
            "every finite supportive, null, or adverse result is filed without outcome selection",
        ],
        planned_sample={
            "metric": "token_delta", "pairs": 36,
            "pairs_per_form": {form: 12 for form in FORMS},
            "models": list(MODELS), "readers": 0,
        },
        proposal_revision=SLUG,
    )["attempt"]
    try:
        for predecessor in PREDECESSOR_ATTEMPTS:
            if client.attempt(predecessor).get("state") != "aborted":
                raise RuntimeError(f"declared predecessor {predecessor} is not terminal-aborted")
        payload, computed = score(manifest)
        payload["attempt_id"] = opened["attempt_id"]
        filed = client.measure(SLUG, payload)
    except Exception as exc:
        abort(client, opened["attempt_id"], "token instrument failed before measurement emission", {
            "exception": type(exc).__name__, "message": str(exc), "preflight": receipt,
        })
        raise
    result = {
        "kind": "ainglish.preference-valence.token-original.v1",
        "proposal": SLUG,
        "attempt": opened,
        "preflight": receipt,
        "computed": computed,
        "measurement": filed,
        "manifest_commitment": manifest_commitment(manifest),
    }
    RECEIPT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
