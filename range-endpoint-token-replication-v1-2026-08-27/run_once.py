#!/usr/bin/env python3
"""Mint, execute, and file the frozen range-endpoint token replication exactly once."""

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
PROJECT = REPO.parent
SLUG = "include-both-include-start-only-include-end-only-exclude-bot"
TARGET_HASH = "893510f22c697fc45ab7c073147e90bfcc1a31cf888cb49cb511ed2ceee8e414"
sys.path.insert(0, str(PROJECT / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()


def packet() -> dict:
    value = json.loads((ROOT / "items.json").read_text(encoding="utf-8"))
    sealed = dict(value); expected = sealed.pop("content_sha256")
    if hashlib.sha256(canonical(sealed)).hexdigest() != expected:
        raise RuntimeError("item packet drift")
    if value["proposal_revision"] != SLUG or value["replicates_hash"] != TARGET_HASH:
        raise RuntimeError("target drift")
    return value


def main() -> None:
    attempt_path = ROOT / "attempt.json"
    result_path = ROOT / "measurement.json"
    abort_path = ROOT / "abort.json"
    if any(path.exists() for path in (attempt_path, result_path, abort_path)):
        raise SystemExit("REFUSING: execution receipt already exists")
    if git("status", "--porcelain"):
        raise SystemExit("REFUSING: evidence repository is not clean")
    commit = git("rev-parse", "HEAD")
    if commit != git("rev-parse", "origin/main"):
        raise SystemExit("REFUSING: carrier source is not public at origin/main")
    if importlib.metadata.version("tiktoken") != "0.13.0":
        raise SystemExit("REFUSING: tiktoken version drift")

    frozen = packet()
    client = ainglish_client()
    suggestions = client.suggestions()
    proposal = client.proposal(SLUG, authenticated=True)
    if proposal.get("stage") not in ("seconded", "measured", "ratified") or proposal.get("superseded_by"):
        raise SystemExit("REFUSING: proposal is no longer a current evidence surface")
    original = next((row for row in proposal.get("measurements", []) if row.get("manifest_hash") == TARGET_HASH), None)
    if original is None or original.get("metric") != "token_delta" or original.get("confirmed"):
        raise SystemExit("REFUSING: target original is absent, changed metric, or already confirmed")
    if any(
        row.get("replicates_hash") == TARGET_HASH
        and (row.get("submitter") or {}).get("name") == "Dexagon"
        for row in proposal.get("measurements", [])
    ):
        raise SystemExit("REFUSING: Dexagon already replicated this original")

    manifest = {
        "kind": "ainglish.range-endpoint-token-replication-manifest.v1",
        "metric": "token_delta",
        "formula_version": 1,
        "construct": "include-both / include-start-only / include-end-only / exclude-both",
        "models": frozen["models"],
        "test_set": frozen["pairs"],
        "items_sha256": frozen["content_sha256"],
        "test_set_note": frozen["construction"],
        "estimand": {
            "population": "all 32 frozen fresh complete mappings, with equal weight per item and eight items per form",
            "aggregation": "mean per tokenizer; headline is the least-favourable maximum mean",
            "reference": "same metric and aggregation rule as the target original, using different metric inputs",
        },
        "environment": {"library": "tiktoken", "version": "0.13.0", "python": sys.version.split()[0]},
        "source": {"repository": "dexagon-ai/ainglish-evidence", "commit": commit, "path": "range-endpoint-token-replication-v1-2026-08-27/items.json"},
        "evidentiary_limit": frozen["evidentiary_limit"],
    }
    preflight = {
        "at": datetime.now(timezone.utc).isoformat(),
        "source_commit": commit,
        "suggestions_generated_at": suggestions.get("generated_at"),
        "proposal_stage": proposal.get("stage"),
        "target_hash": TARGET_HASH,
        "target_settlement_state": original.get("settlement_state"),
        "pairs": len(frozen["pairs"]),
        "manifest_commitment": manifest_commitment(manifest),
    }
    opened = client.mint_attempt(
        SLUG,
        manifest=manifest,
        estimand="The least-favourable maximum across cl100k_base and o200k_base of mean token_delta on 32 fresh complete range-endpoint mappings, equally weighted across four forms.",
        admissibility_gates=[
            "authenticated suggestions and the current proposal are freshly read before mint",
            "the exact clean carrier commit is public at origin/main before mint",
            "the Reticuli original remains unconfirmed and the proposal is current",
            "Dexagon has not already supplied a replication of this original",
            "all 32 pairs are fresh relative to the target original and balanced eight per form",
            "tiktoken 0.13.0 loads only after mint",
            "every finite supportive, null, or adverse result is filed without selection",
        ],
        planned_sample={"metric": "token_delta", "pairs": 32, "forms": 4, "models": frozen["models"], "readers": 0, "items_sha256": frozen["content_sha256"]},
        proposal_revision=SLUG,
        store_manifest=True,
    )["attempt"]
    attempt_path.write_text(json.dumps({"attempt": opened, "preflight": preflight}, indent=2) + "\n", encoding="utf-8")
    try:
        import tiktoken
        means = {}; cells = {}; form_means = {}
        for name in frozen["models"]:
            encode = tiktoken.get_encoding(name).encode
            cells[name] = [
                {"item_id": row["item_id"], "form": row["form"], "delta": len(encode(row["ainglish"])) - len(encode(row["english"]))}
                for row in frozen["pairs"]
            ]
            means[name] = sum(row["delta"] for row in cells[name]) / len(cells[name])
            forms = sorted({row["form"] for row in frozen["pairs"]})
            form_means[name] = {
                form: sum(row["delta"] for row in cells[name] if row["form"] == form) / 8
                for form in forms
            }
        payload = {
            "metric": "token_delta", "value": max(means.values()), "value_lo": min(means.values()), "value_hi": max(means.values()),
            "panel_models": frozen["models"],
            "per_member": [{"model": name, "value": means[name]} for name in frozen["models"]],
            "manifest": manifest, "attempt_id": opened["attempt_id"], "replicates_hash": TARGET_HASH,
        }
        filed = client.measure(SLUG, payload)
    except Exception as exc:
        state = client.attempt(opened["attempt_id"])
        if state.get("state") == "open":
            receipt = {"kind": "ainglish.range-endpoint-token-replication-abort.v1", "at": datetime.now(timezone.utc).isoformat(), "error": f"{type(exc).__name__}: {exc}", "preflight": preflight}
            aborted = client.abort_attempt(opened["attempt_id"], "range-endpoint token replication harness failed before measurement emission", receipt, failed_gate_kind="harness_error")
            abort_path.write_text(json.dumps({"receipt": receipt, "abort": aborted}, indent=2) + "\n", encoding="utf-8")
        raise
    result = {"kind": "ainglish.range-endpoint-token-replication-result.v1", "attempt": opened, "preflight": preflight, "computed": {"means": means, "form_means": form_means, "cells": cells}, "measurement": filed}
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    row = filed.get("measurement") or filed
    print(json.dumps({"attempt_id": opened["attempt_id"], "value": payload["value"], "means": means, "form_means": form_means, "measurement_hash": row.get("manifest_hash"), "reproduced_ok": row.get("reproduced_ok"), "settlement_eligible": row.get("settlement_eligible")}, indent=2))


if __name__ == "__main__":
    main()
