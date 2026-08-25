#!/usr/bin/env python3
"""Run one fresh-input evidential-tags token replication."""

from __future__ import annotations

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


SLUG = "evidential-tags-obs-inf-rep-src-with-instrument-recall-and-p-2"
TARGET = "2cf05685d30675c1ee342fc35e9c7af93a8b63a2d9f66b34efbcd5ec9d6c112a"
VERSION = "0.13.0"
MODELS = ("cl100k_base", "o200k_base")
RECEIPT = ROOT / "replication-receipt.json"
ABORT_RECEIPT = ROOT / "abort-receipt.json"

TEST_SET = (
    {
        "english": "I directly observed that the retention queue became empty.",
        "ainglish": "obs: the retention queue became empty.",
    },
    {
        "english": "The signed health probe reported that the archive node is reachable.",
        "ainglish": "obs(signed health probe): the archive node is reachable.",
    },
    {
        "english": "I deduce, from premises I have not stated, that the replica is behind.",
        "ainglish": "inf: the replica is behind.",
    },
    {
        "english": "From the audit trail and the stale cursor, I infer the export skipped a page; the claim stands no stronger than the weaker of those two sources.",
        "ainglish": "inf(audit trail + stale cursor): the export skipped a page.",
    },
    {
        "english": "According to the regional incident bulletin, the gateway is unavailable.",
        "ainglish": "rep(regional incident bulletin): the gateway is unavailable.",
    },
    {
        "english": "Recalled from my own earlier state and unverified now: the signing key expires today.",
        "ainglish": "rep(self-past): the signing key expires today.",
    },
    {
        "english": "My immutable event counter reported that twelve jobs were retried.",
        "ainglish": "obs(immutable event counter): twelve jobs were retried.",
    },
    {
        "english": "From the two checksum ledgers alone, I infer the mirror differs; the claim is bounded by those sources.",
        "ainglish": "inf(two checksum ledgers): the mirror differs.",
    },
)


def git_output(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=EVIDENCE_REPO, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    ).stdout.strip()


def source_state() -> dict:
    if git_output("status", "--porcelain"):
        raise RuntimeError("evidence repository is not clean")
    commit = git_output("rev-parse", "HEAD")
    if commit != git_output("rev-parse", "origin/main"):
        raise RuntimeError("source commit is not published at origin/main")
    path = Path(__file__).resolve()
    relative = path.relative_to(EVIDENCE_REPO)
    return {
        "commit": commit, "path": str(relative),
        "url": f"https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{commit}/{relative}",
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def manifest(source: dict) -> dict:
    return {
        "metric": "token_delta", "formula_version": 1,
        "construct": "evidential tags (obs / inf / rep with instruments, premises, source and recall)",
        "models": list(MODELS),
        "environment": {"library": "tiktoken", "version": VERSION},
        "test_set": list(TEST_SET),
        "seed": "none — deterministic tokenizer counts, no sampling",
        "population": "three observation, three inference and two reported-or-recalled provenance claims",
        "selection": (
            "Eight new complete meaning-matched pairs preserving the original 3/3/2 tag-family mix; "
            "instrument, weakest-premise, named-source and self-past cells are retained."
        ),
        "method": (
            "For each tokenizer, compute len(encode(ainglish))-len(encode(english)) for every pair "
            "and take the arithmetic mean. File the maximum tokenizer mean as the least-favourable "
            "value; value_lo/value_hi span member means."
        ),
        "source": source,
    }


def pair_key(row: dict) -> tuple[str, str]:
    return row["english"].strip(), row["ainglish"].strip()


def preflight(client, spec: dict) -> dict:
    suggestions = client.suggestions()
    proposal = client.proposal(SLUG, authenticated=True)
    target = client.measurement(TARGET)
    card = next((row for row in suggestions.get("suggestions", []) if row.get("slug") == SLUG and row.get("replicates_hash") == TARGET and row.get("executable_now")), None)
    if card is None:
        raise RuntimeError("fresh suggestions no longer offer this exact replication")
    if target.get("settlement_state") != "disputed" or target.get("metric") != "token_delta":
        raise RuntimeError("target is no longer the frozen disputed token original")
    ours = {pair_key(row) for row in spec["test_set"]}
    if len(ours) != 8:
        raise RuntimeError("replication does not contain eight unique complete pairs")
    prior = set()
    for row in proposal.get("measurements", []):
        if not row.get("manifest_hash"):
            continue
        detail = client.measurement(row["manifest_hash"])
        for item in (detail.get("manifest") or {}).get("test_set", []):
            if isinstance(item, dict) and "english" in item and "ainglish" in item:
                prior.add(pair_key(item))
    overlap = sorted(ours & prior)
    if overlap:
        raise RuntimeError(f"fresh-input gate failed for {len(overlap)} complete pairs")
    return {
        "suggestions_generated_at": suggestions.get("generated_at"),
        "proposal_stage": proposal.get("stage"), "target_state": target.get("settlement_state"),
        "visible_prior_pairs": len(prior), "fresh_pairs": 8, "overlap": 0,
        "manifest_commitment": manifest_commitment(spec),
    }


def score(spec: dict) -> tuple[dict, dict]:
    import tiktoken  # Imported only after attempt mint.

    if importlib.metadata.version("tiktoken") != VERSION:
        raise RuntimeError("pinned tiktoken version is unavailable")
    cells = {}
    means = {}
    for model in MODELS:
        encode = tiktoken.get_encoding(model).encode
        cells[model] = [
            len(encode(row["ainglish"])) - len(encode(row["english"]))
            for row in spec["test_set"]
        ]
        means[model] = sum(cells[model]) / len(cells[model])
    payload = {
        "metric": "token_delta", "formula_version": 1,
        "value": max(means.values()), "value_lo": min(means.values()), "value_hi": max(means.values()),
        "panel_models": list(MODELS),
        "per_member": [{"model": model, "value": means[model]} for model in MODELS],
        "manifest": spec, "replicates_hash": TARGET,
    }
    return payload, {"cells": cells, "means": means, "value": payload["value"]}


def abort(client, attempt_id: str, message: str, details: dict) -> None:
    receipt = {
        "kind": "ainglish.token-replication.abort.v1", "at": datetime.now(timezone.utc).isoformat(),
        "attempt_id": attempt_id, "failed_gate_kind": "harness_error", "failed_gate": message,
        "details": details,
    }
    encoded = json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    ABORT_RECEIPT.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    client.post(
        f"/api/v1/attempts/{urllib.parse.quote(attempt_id, safe='')}/abort",
        {"failed_gate_kind": "harness_error", "failed_gate": message,
         "preflight_receipt": encoded, "preflight_receipt_hash": hashlib.sha256(encoded.encode()).hexdigest()},
    )


def main() -> None:
    if RECEIPT.exists() or ABORT_RECEIPT.exists():
        raise SystemExit("REFUSING: terminal local receipt already exists")
    spec = manifest(source_state())
    client = ainglish_client()
    checked = preflight(client, spec)
    opened = client.mint_attempt(
        SLUG, manifest=spec,
        estimand=(
            "The maximum mean token_delta across the original's cl100k_base and o200k_base "
            "members on eight fresh complete provenance-tag pairs preserving its 3/3/2 family mix."
        ),
        admissibility_gates=[
            "fresh suggestions still offer this exact disputed original for replication",
            "all eight complete pairs are absent from every visible prior manifest",
            "the 3 observation / 3 inference / 2 report-or-recall mix and complete mappings are preserved",
            "the clean source is published before mint and tiktoken loads only after mint",
            "every finite agreement, disagreement or null result is filed",
        ],
        planned_sample={
            "metric": "token_delta", "pairs": 8, "models": list(MODELS),
            "replicates_hash": TARGET, "readers": 0,
        }, proposal_revision=SLUG,
    )["attempt"]
    try:
        payload, computed = score(spec)
        payload["attempt_id"] = opened["attempt_id"]
        filed = client.measure(SLUG, payload)
    except Exception as exc:
        abort(client, opened["attempt_id"], "token replication failed before measurement emission", {
            "exception": type(exc).__name__, "message": str(exc), "preflight": checked,
        })
        raise
    result = {
        "kind": "ainglish.evidential-tags.token-replication.v1", "target": TARGET,
        "attempt": opened, "preflight": checked, "computed": computed,
        "measurement": filed, "manifest_commitment": manifest_commitment(spec),
    }
    RECEIPT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
