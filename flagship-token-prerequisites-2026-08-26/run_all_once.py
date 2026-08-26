#!/usr/bin/env python3
"""Mint, tokenize, and file one frozen flagship token prerequisite exactly once."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys

from ainglish.client import manifest_commitment


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
SCRIPTS = REPO.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402


ENCODINGS = ("cl100k_base", "o200k_base", "p50k_base")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO, check=True, capture_output=True, text=True,
    ).stdout.strip()


def load_campaign(name: str) -> tuple[dict, dict]:
    packet = json.loads((ROOT / "items.json").read_text(encoding="utf-8"))
    sealed = dict(packet)
    expected = sealed.pop("content_sha256")
    if hashlib.sha256(canonical(sealed)).hexdigest() != expected:
        raise RuntimeError("packet digest drift")
    row = packet["campaigns"][name]
    if hashlib.sha256(canonical(row["test_set"])).hexdigest() != row["items_sha256"]:
        raise RuntimeError("test-set digest drift")
    return packet, row


def current_token_work(proposal: dict) -> dict | None:
    readiness = proposal.get("evidence_readiness") or {}
    for item in readiness.get("work_items", []):
        if item.get("metric") == "token_delta":
            return item
    return None


def preflight(client, name: str, row: dict, predecessor: str | None) -> dict:
    if git("status", "--porcelain"):
        raise RuntimeError("evidence repository is not clean")
    commit = git("rev-parse", "HEAD")
    if commit != git("rev-parse", "origin/main"):
        raise RuntimeError("frozen source commit is not published at origin/main")
    if importlib.metadata.version("tiktoken") != "0.13.0":
        raise RuntimeError("tiktoken version drift")
    suggestions = client.suggestions()
    proposal = client.proposal(row["slug"], authenticated=True)
    if proposal.get("stage") not in ("seconded", "measured") or proposal.get("superseded_by"):
        raise RuntimeError("proposal is not a current measurement surface")
    work = current_token_work(proposal)
    if not work or work.get("state") != "submit_original":
        raise RuntimeError("fresh proposal no longer requests a token original")
    prior = [
        item for item in proposal.get("measurements", [])
        if item.get("metric") == "token_delta" and not item.get("is_replication")
    ]
    if prior:
        raise RuntimeError("a token original already exists on this lifecycle")
    pairs = row["test_set"]
    if len(pairs) & (len(pairs) - 1):
        raise RuntimeError("pair count is not a power of two")
    if len({(item["english"], item["ainglish"]) for item in pairs}) != len(pairs):
        raise RuntimeError("complete pairs are not unique")
    form_counts = {form: sum(item["form"] == form for item in pairs) for form in row["forms"]}
    if len(set(form_counts.values())) != 1:
        raise RuntimeError("forms are not equally represented")
    for attempt in proposal.get("attempts", []):
        if attempt.get("state") != "open":
            continue
        manifest = attempt.get("manifest") or {}
        if manifest.get("items_sha256") == row["items_sha256"]:
            raise RuntimeError("an identical open attempt already exists")
    predecessor_state = None
    if predecessor:
        predecessor_state = client.attempt(predecessor)
        if predecessor_state.get("state") != "aborted":
            raise RuntimeError("declared predecessor is not terminal-aborted")
        if predecessor_state.get("proposal") != row["slug"]:
            raise RuntimeError("declared predecessor belongs to another proposal")
    return {
        "campaign": name,
        "commit": commit,
        "suggestions_generated_at": suggestions.get("generated_at"),
        "proposal_stage": proposal.get("stage"),
        "fresh_work_state": work.get("state"),
        "prior_originals": 0,
        "pairs": len(pairs),
        "form_counts": form_counts,
        "predecessor_attempt": predecessor,
        "predecessor_state": predecessor_state.get("state") if predecessor_state else None,
    }


def build_manifest(name: str, row: dict, checked: dict) -> dict:
    return {
        "metric": "token_delta",
        "formula_version": 1,
        "construct": " / ".join(row["forms"]),
        "models": [f"tiktoken/{encoding}" for encoding in ENCODINGS],
        "test_set": row["test_set"],
        "items_sha256": row["items_sha256"],
        "test_set_note": (
            "Every pair differs only in the exact registered marker versus the proposal-pinned "
            "short careful-English control. Forms receive equal weight."
        ),
        "estimand": {
            "population": f"all {len(row['test_set'])} frozen complete minimal pairs",
            "aggregation": "mean per tokenizer; headline is the least-favourable maximum mean",
            "acceptance": row["acceptance"],
        },
        "environment": {"library": "tiktoken", "version": "0.13.0", "python": sys.version.split()[0]},
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "commit": checked["commit"],
            "path": "flagship-token-prerequisites-2026-08-26/items.json",
        },
        "execution_history": {
            "predecessor_attempt": checked["predecessor_attempt"],
            "note": (
                "When present, the predecessor stopped before measurement emission because the "
                "server rejected version-suffixed tokenizer roster identities. This manifest uses "
                "the mandated bare identities and retains version provenance in environment."
            ),
        },
    }


def score(manifest: dict, forms: list[str]) -> tuple[dict, dict]:
    import tiktoken  # imported only after the attempt is stored

    cells: dict[str, list[dict]] = {}
    means: dict[str, float] = {}
    form_means: dict[str, dict[str, float]] = {}
    for encoding in ENCODINGS:
        encode = tiktoken.get_encoding(encoding).encode
        cells[encoding] = [
            {
                "item": index + 1,
                "form": row["form"],
                "delta": len(encode(row["ainglish"])) - len(encode(row["english"])),
            }
            for index, row in enumerate(manifest["test_set"])
        ]
        means[encoding] = sum(cell["delta"] for cell in cells[encoding]) / len(cells[encoding])
        form_means[encoding] = {
            form: sum(cell["delta"] for cell in cells[encoding] if cell["form"] == form)
            / sum(cell["form"] == form for cell in cells[encoding])
            for form in forms
        }
    payload = {
        "metric": "token_delta",
        "formula_version": 1,
        "value": max(means.values()),
        "value_lo": min(means.values()),
        "value_hi": max(means.values()),
        "panel_models": manifest["models"],
        "per_member": [
            {"model": model, "value": means[encoding]}
            for model, encoding in zip(manifest["models"], ENCODINGS, strict=True)
        ],
        "manifest": manifest,
    }
    return payload, {"value": payload["value"], "means": means, "form_means": form_means, "cells": cells}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign", required=True, choices=("among", "scope"))
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--predecessor")
    args = parser.parse_args()
    receipt_stem = args.campaign if not args.predecessor else f"{args.campaign}.successor-{args.predecessor[:8]}"
    attempt_path = ROOT / f"{receipt_stem}.attempt.json"
    result_path = ROOT / f"{receipt_stem}.measurement.json"
    abort_path = ROOT / f"{receipt_stem}.abort.json"
    if attempt_path.exists() or result_path.exists() or abort_path.exists():
        raise SystemExit("REFUSING: a local attempt, result, or abort receipt already exists")
    _, row = load_campaign(args.campaign)
    client = ainglish_client()
    checked = preflight(client, args.campaign, row, args.predecessor)
    manifest = build_manifest(args.campaign, row, checked)
    checked["manifest_commitment"] = manifest_commitment(manifest)
    checked["manifest_bytes"] = len(canonical(manifest))
    if checked["manifest_bytes"] > 20_000:
        raise RuntimeError("manifest exceeds the register limit")
    if args.preflight_only:
        print(json.dumps(checked, indent=2))
        return
    opened = client.mint_attempt(
        row["slug"],
        manifest=manifest,
        estimand=(
            f"The least-favourable maximum across three pinned tiktoken encodings of mean "
            f"token_delta on {len(row['test_set'])} frozen complete minimal pairs, with equal form weight."
        ),
        admissibility_gates=[
            "fresh authenticated state still requests a token_delta original on the current lifecycle",
            "the clean runner and exact packet are published at origin/main before mint",
            "the complete-pair count is a power of two and every pair is unique",
            "forms remain equally represented and use only the proposal-pinned careful controls",
            "all three pinned tokenizer identities load only after mint",
            "every finite supportive, null, or adverse result is filed without outcome selection",
        ],
        planned_sample={
            "metric": "token_delta",
            "pairs": len(row["test_set"]),
            "forms": checked["form_counts"],
            "models": manifest["models"],
            "readers": 0,
            "items_sha256": row["items_sha256"],
        },
        proposal_revision=row["slug"],
        store_manifest=True,
    )["attempt"]
    attempt_path.write_text(json.dumps({"attempt": opened, "preflight": checked}, indent=2) + "\n", encoding="utf-8")
    try:
        payload, computed = score(manifest, row["forms"])
        payload["attempt_id"] = opened["attempt_id"]
        filed = client.measure(row["slug"], payload)
    except Exception as exc:
        state = client.attempt(opened["attempt_id"])
        if state.get("state") == "open":
            receipt = {
                "kind": "ainglish.flagship-token-prerequisite-abort.v1",
                "at": datetime.now(timezone.utc).isoformat(),
                "error": f"{type(exc).__name__}: {exc}",
                "preflight": checked,
            }
            aborted = client.abort_attempt(
                opened["attempt_id"],
                "token prerequisite harness failed before measurement emission",
                receipt,
                failed_gate_kind="harness_error",
            )
            abort_path.write_text(json.dumps({"receipt": receipt, "abort": aborted}, indent=2) + "\n", encoding="utf-8")
        raise
    result = {
        "kind": "ainglish.flagship-token-prerequisite-result.v1",
        "campaign": args.campaign,
        "attempt": opened,
        "preflight": checked,
        "computed": computed,
        "measurement": filed,
    }
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "campaign": args.campaign,
        "attempt_id": opened["attempt_id"],
        "manifest_commitment": checked["manifest_commitment"],
        "value": computed["value"],
        "means": computed["means"],
        "form_means": computed["form_means"],
        "measurement_hash": (filed.get("measurement") or filed).get("hash"),
    }, indent=2))


if __name__ == "__main__":
    main()
