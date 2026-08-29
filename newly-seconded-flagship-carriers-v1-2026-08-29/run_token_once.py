#!/usr/bin/env python3
"""Mint, score, and file one frozen token prerequisite exactly once."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlparse

from ainglish.client import manifest_commitment


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
sys.path.insert(0, str(REPO.parent / "scripts"))
from local_colony_auth import ainglish_client, colony_client  # noqa: E402

ENCODINGS = ("cl100k_base", "o200k_base", "p50k_base")
TARGETS = {
    "average": {
        "file": "average-token-items.json",
        "construct": "mean-of / median-of statistic and population binding",
    },
    "deletion": {
        "file": "deletion-token-items.json",
        "construct": "removed-from / erased-from bounded deletion depth",
    },
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()


def load(target: str) -> dict:
    packet = json.loads((ROOT / TARGETS[target]["file"]).read_text(encoding="utf-8"))
    sealed = dict(packet)
    expected = sealed.pop("content_sha256")
    if hashlib.sha256(canonical(sealed)).hexdigest() != expected:
        raise RuntimeError("packet digest drift")
    if hashlib.sha256(canonical(packet["test_set"])).hexdigest() != packet["items_sha256"]:
        raise RuntimeError("item digest drift")
    return packet


def preflight(ainglish, colony, packet: dict) -> dict:
    if git("status", "--porcelain"):
        raise RuntimeError("evidence repository is not clean")
    commit = git("rev-parse", "HEAD")
    if commit != git("rev-parse", "origin/main"):
        raise RuntimeError("frozen source is not public at origin/main")
    if importlib.metadata.version("tiktoken") != "0.13.0":
        raise RuntimeError("tiktoken version drift")
    suggestions = ainglish.suggestions()
    proposal = ainglish.proposal(packet["proposal_slug"], authenticated=True)
    post_id = urlparse(proposal.get("colony_thread_url") or "").path.rsplit("/", 1)[-1]
    comments = colony.get_all_comments(post_id) if post_id else []
    if not comments:
        raise RuntimeError("proposal discussion was not readable immediately before mint")
    if proposal.get("stage") not in ("seconded", "measured") or proposal.get("superseded_by"):
        raise RuntimeError("proposal is not current and measurement-eligible")
    work = next((row for row in (proposal.get("evidence_readiness") or {}).get("work_items", []) if row.get("metric") == "token_delta"), None)
    if not work or work.get("state") != "submit_original":
        raise RuntimeError("token prerequisite no longer requests an original")
    if any(row.get("metric") == "token_delta" and not row.get("is_replication") for row in proposal.get("measurements", [])):
        raise RuntimeError("token original already exists")
    counts = {form: sum(row["form"] == form for row in packet["test_set"]) for form in packet["forms"]}
    if len(packet["test_set"]) != 32 or counts != packet["form_counts"]:
        raise RuntimeError("pair count or form balance drift")
    return {
        "commit": commit,
        "suggestions_generated_at": suggestions.get("generated_at"),
        "stage": proposal.get("stage"),
        "thread_post_id": post_id,
        "thread_comment_count": len(comments),
        "thread_tail_id": comments[-1].get("id"),
        "pairs": 32,
        "form_counts": counts,
    }


def make_manifest(target: str, packet: dict, check: dict) -> dict:
    return {
        "metric": "token_delta",
        "formula_version": 1,
        "construct": TARGETS[target]["construct"],
        "models": [f"tiktoken/{encoding}" for encoding in ENCODINGS],
        "test_set": packet["test_set"],
        "items_sha256": packet["items_sha256"],
        "test_set_note": packet["comparison"] + "; both forms receive equal weight",
        "estimand": {
            "population": "all 32 frozen same-semantic-cell complete pairs, 16 per form",
            "aggregation": "mean per tokenizer over the form-balanced population; headline is the least-favourable maximum mean",
            "acceptance": packet["acceptance"],
        },
        "evidentiary_limit": packet["evidentiary_limit"],
        "environment": {"library": "tiktoken", "version": "0.13.0", "python": sys.version.split()[0]},
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "commit": check["commit"],
            "path": f"newly-seconded-flagship-carriers-v1-2026-08-29/{TARGETS[target]['file']}",
        },
    }


def score(manifest: dict, forms: list[str]) -> tuple[dict, dict]:
    import tiktoken

    means, form_means, cells = {}, {}, {}
    for encoding in ENCODINGS:
        encode = tiktoken.get_encoding(encoding).encode
        cells[encoding] = []
        for row in manifest["test_set"]:
            a_tokens, e_tokens = len(encode(row["ainglish"])), len(encode(row["english"]))
            cells[encoding].append({
                "item_id": row["item_id"], "form": row["form"],
                "ainglish_tokens": a_tokens, "english_tokens": e_tokens, "delta": a_tokens - e_tokens,
            })
        form_means[encoding] = {
            form: sum(cell["delta"] for cell in cells[encoding] if cell["form"] == form) /
            sum(cell["form"] == form for cell in cells[encoding])
            for form in forms
        }
        means[encoding] = sum(form_means[encoding].values()) / len(forms)
    value = max(means.values())
    payload = {
        "metric": "token_delta", "formula_version": 1,
        "value": value, "value_lo": min(means.values()), "value_hi": value,
        "panel_models": manifest["models"],
        "per_member": [{"model": model, "value": means[encoding]} for model, encoding in zip(manifest["models"], ENCODINGS, strict=True)],
        "manifest": manifest,
    }
    return payload, {"value": value, "means": means, "form_means": form_means, "cells": cells}


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in TARGETS:
        raise SystemExit("usage: run_token_once.py <average|deletion>")
    target = sys.argv[1]
    attempt_path = ROOT / f"{target}-token-attempt.json"
    result_path = ROOT / f"{target}-token-measurement.json"
    abort_path = ROOT / f"{target}-token-abort.json"
    if any(path.exists() for path in (attempt_path, result_path, abort_path)):
        raise SystemExit(f"REFUSING: local {target} token attempt artifact already exists")
    packet = load(target)
    ainglish, colony = ainglish_client(), colony_client()
    check = preflight(ainglish, colony, packet)
    manifest = make_manifest(target, packet, check)
    check["manifest_commitment"] = manifest_commitment(manifest)
    check["manifest_bytes"] = len(canonical(manifest))
    if check["manifest_bytes"] > 20_000:
        raise RuntimeError("manifest exceeds register limit")
    opened = ainglish.mint_attempt(
        packet["proposal_slug"], manifest=manifest,
        estimand="Least-favourable maximum across three pinned tiktoken encodings of mean token_delta on 32 fresh same-cell pairs, with equal form weight.",
        admissibility_gates=[
            "fresh authenticated suggestions, current proposal, and Colony discussion reads precede mint",
            "the current lifecycle requests a token_delta original",
            "the exact pair packet and runner are public before mint or tokenizer load",
            "the population contains 32 unique complete pairs balanced 16 per form",
            "both arms preserve the same object or population reference, semantic scope, epoch where applicable, value, and unit",
            "all pinned tokenizers load only after mint",
            "every finite supportive, null, or adverse result is filed",
            "the result is price-only and never used as comprehension evidence",
        ],
        planned_sample={
            "metric": "token_delta", "pairs": 32, "forms": check["form_counts"],
            "models": manifest["models"], "readers": 0, "items_sha256": packet["items_sha256"],
        },
        proposal_revision=packet["proposal_slug"], store_manifest=True,
    )["attempt"]
    attempt_path.write_text(json.dumps({"attempt": opened, "preflight": check}, indent=2) + "\n", encoding="utf-8")
    try:
        payload, computed = score(manifest, packet["forms"])
        payload["attempt_id"] = opened["attempt_id"]
        filed = ainglish.measure(packet["proposal_slug"], payload)
    except Exception as exc:
        state = ainglish.attempt(opened["attempt_id"])
        if state.get("state") == "open":
            receipt = {
                "kind": f"dexagon.ainglish.{target}-token-abort.v1",
                "at": datetime.now(timezone.utc).isoformat(),
                "error": f"{type(exc).__name__}: {exc}", "preflight": check,
            }
            aborted = ainglish.abort_attempt(opened["attempt_id"], "token prerequisite harness failed before measurement emission", receipt, failed_gate_kind="harness_error")
            abort_path.write_text(json.dumps({"receipt": receipt, "abort": aborted}, indent=2) + "\n", encoding="utf-8")
        raise
    result = {
        "kind": f"dexagon.ainglish.{target}-token-result.v1",
        "attempt": opened, "preflight": check, "computed": computed, "measurement": filed,
    }
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    row = filed.get("measurement") or filed
    print(json.dumps({
        "target": target, "attempt_id": opened["attempt_id"],
        "manifest_commitment": check["manifest_commitment"], "value": computed["value"],
        "means": computed["means"], "form_means": computed["form_means"],
        "measurement_hash": row.get("hash") or row.get("manifest_hash"),
    }, indent=2))


if __name__ == "__main__":
    main()
