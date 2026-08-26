#!/usr/bin/env python3
"""Mint, score, and file the frozen recertification exactly once."""

from __future__ import annotations

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
    return subprocess.run(["git", *args], cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()


def load() -> dict:
    packet = json.loads((ROOT / "items.json").read_text(encoding="utf-8"))
    sealed = dict(packet)
    expected = sealed.pop("content_sha256")
    if hashlib.sha256(canonical(sealed)).hexdigest() != expected:
        raise RuntimeError("packet digest drift")
    if hashlib.sha256(canonical(packet["test_set"])).hexdigest() != packet["items_sha256"]:
        raise RuntimeError("item digest drift")
    return packet


def preflight(client, packet: dict) -> dict:
    if git("status", "--porcelain"):
        raise RuntimeError("evidence repository is not clean")
    commit = git("rev-parse", "HEAD")
    if commit != git("rev-parse", "origin/main"):
        raise RuntimeError("frozen source is not published")
    if importlib.metadata.version("tiktoken") != "0.13.0":
        raise RuntimeError("tiktoken version drift")
    suggestions = client.suggestions()
    proposal = client.proposal(packet["proposal_slug"], authenticated=True)
    if proposal.get("stage") != "ratified" or proposal.get("superseded_by"):
        raise RuntimeError("proposal is not the current ratified surface")
    pairs = packet["test_set"]
    if len(pairs) != 32 or len(pairs) & (len(pairs) - 1):
        raise RuntimeError("pair-count gate")
    if len({(row["ainglish"], row["english"]) for row in pairs}) != len(pairs):
        raise RuntimeError("pair uniqueness gate")
    return {
        "commit": commit,
        "generated_at": suggestions.get("generated_at"),
        "stage": proposal.get("stage"),
        "ratified_at": proposal.get("ratified_at"),
        "prior_measurements": len(proposal.get("measurements", [])),
        "pairs": len(pairs),
    }


def make_manifest(packet: dict, check: dict) -> dict:
    return {
        "metric": "token_delta",
        "formula_version": 1,
        "construct": "human_needed(<why>)",
        "models": [f"tiktoken/{encoding}" for encoding in ENCODINGS],
        "test_set": packet["test_set"],
        "items_sha256": packet["items_sha256"],
        "test_set_note": packet["comparison"],
        "estimand": {
            "population": "all 32 frozen complete minimal pairs",
            "aggregation": "mean per tokenizer; headline is the least-favourable maximum mean",
            "acceptance": packet["acceptance"],
        },
        "evidentiary_limit": packet["evidentiary_limit"],
        "environment": {"library": "tiktoken", "version": "0.13.0", "python": sys.version.split()[0]},
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "commit": check["commit"],
            "path": "human-needed-token-recertification-2026-08-26/items.json",
        },
    }


def score(manifest: dict) -> tuple[dict, dict]:
    import tiktoken
    means = {}
    cells = {}
    for encoding in ENCODINGS:
        encode = tiktoken.get_encoding(encoding).encode
        cells[encoding] = [
            {
                "item_id": row["item_id"],
                "ainglish_tokens": len(encode(row["ainglish"])),
                "english_tokens": len(encode(row["english"])),
                "delta": len(encode(row["ainglish"])) - len(encode(row["english"])),
            }
            for row in manifest["test_set"]
        ]
        means[encoding] = sum(row["delta"] for row in cells[encoding]) / len(cells[encoding])
    value = max(means.values())
    payload = {
        "metric": "token_delta",
        "formula_version": 1,
        "value": value,
        "value_lo": min(means.values()),
        "value_hi": value,
        "panel_models": manifest["models"],
        "per_member": [
            {"model": model, "value": means[encoding]}
            for model, encoding in zip(manifest["models"], ENCODINGS, strict=True)
        ],
        "manifest": manifest,
    }
    return payload, {"value": value, "means": means, "cells": cells}


def main() -> None:
    attempt_path = ROOT / "attempt.json"
    result_path = ROOT / "measurement.json"
    abort_path = ROOT / "abort.json"
    if attempt_path.exists() or result_path.exists() or abort_path.exists():
        raise SystemExit("REFUSING: local attempt artifact already exists")
    packet = load()
    client = ainglish_client()
    check = preflight(client, packet)
    manifest = make_manifest(packet, check)
    check["manifest_commitment"] = manifest_commitment(manifest)
    check["manifest_bytes"] = len(canonical(manifest))
    if check["manifest_bytes"] > 20000:
        raise RuntimeError("manifest exceeds register limit")
    opened = client.mint_attempt(
        packet["proposal_slug"],
        manifest=manifest,
        estimand="The least-favourable maximum across three pinned tiktoken encodings of mean token_delta on 32 fresh complete pairs.",
        admissibility_gates=[
            "the current surface remains ratified and unsuperseded",
            "the clean exact packet is public before mint",
            "the pair count is exactly 32 and every pair is unique",
            "each control carries both human-decision and agent-must-not-resolve semantics",
            "all pinned tokenizers load only after mint",
            "every finite supportive, null, or adverse result is filed",
            "the result is labelled price-only and never used as comprehension evidence",
        ],
        planned_sample={"metric": "token_delta", "pairs": 32, "models": manifest["models"], "readers": 0, "items_sha256": packet["items_sha256"]},
        proposal_revision=packet["proposal_slug"],
        store_manifest=True,
    )["attempt"]
    attempt_path.write_text(json.dumps({"attempt": opened, "preflight": check}, indent=2) + "\n", encoding="utf-8")
    try:
        payload, computed = score(manifest)
        payload["attempt_id"] = opened["attempt_id"]
        filed = client.measure(packet["proposal_slug"], payload)
    except Exception as exc:
        state = client.attempt(opened["attempt_id"])
        if state.get("state") == "open":
            receipt = {"kind": "ainglish.human-needed-token-recertification-abort.v1", "at": datetime.now(timezone.utc).isoformat(), "error": f"{type(exc).__name__}: {exc}", "preflight": check}
            aborted = client.abort_attempt(opened["attempt_id"], "recertification harness failed before measurement emission", receipt, failed_gate_kind="harness_error")
            abort_path.write_text(json.dumps({"receipt": receipt, "abort": aborted}, indent=2) + "\n", encoding="utf-8")
        raise
    result = {"kind": "ainglish.human-needed-token-recertification-result.v1", "attempt": opened, "preflight": check, "computed": computed, "measurement": filed}
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    row = filed.get("measurement") or filed
    print(json.dumps({
        "attempt_id": opened["attempt_id"],
        "manifest_commitment": check["manifest_commitment"],
        "value": computed["value"],
        "means": computed["means"],
        "measurement_hash": row.get("hash") or row.get("manifest_hash"),
    }, indent=2))


if __name__ == "__main__":
    main()
