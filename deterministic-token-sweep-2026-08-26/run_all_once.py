#!/usr/bin/env python3
"""Preflight, mint, score, and file one frozen token original exactly once."""

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
    return subprocess.run(["git", *args], cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()


def load(name: str) -> dict:
    packet = json.loads((ROOT / "items.json").read_text(encoding="utf-8"))
    sealed = dict(packet); expected = sealed.pop("content_sha256")
    if hashlib.sha256(canonical(sealed)).hexdigest() != expected:
        raise RuntimeError("packet digest drift")
    row = packet["campaigns"][name]
    if hashlib.sha256(canonical(row["test_set"])).hexdigest() != row["items_sha256"]:
        raise RuntimeError("test-set digest drift")
    return row


def preflight(client, name: str, row: dict) -> dict:
    if git("status", "--porcelain"):
        raise RuntimeError("evidence repository is not clean")
    commit = git("rev-parse", "HEAD")
    if commit != git("rev-parse", "origin/main"):
        raise RuntimeError("frozen source is not published")
    if importlib.metadata.version("tiktoken") != "0.13.0":
        raise RuntimeError("tiktoken version drift")
    suggestions = client.suggestions()
    proposal = client.proposal(row["slug"], authenticated=True)
    if proposal.get("stage") not in ("seconded", "measured") or proposal.get("superseded_by"):
        raise RuntimeError("proposal lifecycle changed")
    token_work = next((item for item in (proposal.get("evidence_readiness") or {}).get("work_items", []) if item.get("metric") == "token_delta"), None)
    if not token_work or token_work.get("state") != "submit_original":
        raise RuntimeError("fresh row no longer requests a token original")
    if any(item.get("metric") == "token_delta" and not item.get("is_replication") for item in proposal.get("measurements", [])):
        raise RuntimeError("token original now exists")
    pairs = row["test_set"]
    if len(pairs) & (len(pairs) - 1) or len({(item["english"], item["ainglish"]) for item in pairs}) != len(pairs):
        raise RuntimeError("pair population gate")
    counts = {form: sum(item["form"] == form for item in pairs) for form in row["forms"]}
    if len(set(counts.values())) != 1:
        raise RuntimeError("form balance gate")
    return {"campaign": name, "commit": commit, "generated_at": suggestions.get("generated_at"), "stage": proposal.get("stage"), "work_state": token_work.get("state"), "pairs": len(pairs), "form_counts": counts}


def manifest(name: str, row: dict, check: dict) -> dict:
    return {
        "metric": "token_delta", "formula_version": 1,
        "construct": " / ".join(row["forms"]),
        "models": [f"tiktoken/{encoding}" for encoding in ENCODINGS],
        "test_set": row["test_set"], "items_sha256": row["items_sha256"],
        "test_set_note": "Every complete pair compares the registered marker with its full proposal-pinned careful-English meaning; forms receive equal weight.",
        "estimand": {"population": f"all {len(row['test_set'])} frozen complete minimal pairs", "aggregation": "mean per tokenizer; headline is the least-favourable maximum mean", "acceptance": row["acceptance"]},
        "environment": {"library": "tiktoken", "version": "0.13.0", "python": sys.version.split()[0]},
        "source": {"repository": "dexagon-ai/ainglish-evidence", "commit": check["commit"], "path": "deterministic-token-sweep-2026-08-26/items.json"},
    }


def score(spec: dict, forms: list[str]) -> tuple[dict, dict]:
    import tiktoken
    means = {}; form_means = {}; cells = {}
    for encoding in ENCODINGS:
        encode = tiktoken.get_encoding(encoding).encode
        cells[encoding] = [{"item": i + 1, "form": row["form"], "delta": len(encode(row["ainglish"])) - len(encode(row["english"]))} for i, row in enumerate(spec["test_set"])]
        means[encoding] = sum(cell["delta"] for cell in cells[encoding]) / len(cells[encoding])
        form_means[encoding] = {form: sum(cell["delta"] for cell in cells[encoding] if cell["form"] == form) / sum(cell["form"] == form for cell in cells[encoding]) for form in forms}
    payload = {"metric": "token_delta", "formula_version": 1, "value": max(means.values()), "value_lo": min(means.values()), "value_hi": max(means.values()), "panel_models": spec["models"], "per_member": [{"model": model, "value": means[encoding]} for model, encoding in zip(spec["models"], ENCODINGS, strict=True)], "manifest": spec}
    return payload, {"value": payload["value"], "means": means, "form_means": form_means, "cells": cells}


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--campaign", required=True, choices=("they", "next", "different")); parser.add_argument("--preflight-only", action="store_true"); args = parser.parse_args()
    attempt_path = ROOT / f"{args.campaign}.attempt.json"; result_path = ROOT / f"{args.campaign}.measurement.json"; abort_path = ROOT / f"{args.campaign}.abort.json"
    if attempt_path.exists() or result_path.exists() or abort_path.exists():
        raise SystemExit("REFUSING: campaign already has a terminal local artifact")
    row = load(args.campaign); client = ainglish_client(); check = preflight(client, args.campaign, row); spec = manifest(args.campaign, row, check)
    check["manifest_commitment"] = manifest_commitment(spec); check["manifest_bytes"] = len(canonical(spec))
    if check["manifest_bytes"] > 20000: raise RuntimeError("manifest exceeds register limit")
    if args.preflight_only: print(json.dumps(check, indent=2)); return
    opened = client.mint_attempt(row["slug"], manifest=spec, estimand=f"The least-favourable maximum across three pinned tiktoken encodings of mean token_delta on {len(row['test_set'])} frozen complete minimal pairs, with equal form weight.", admissibility_gates=["fresh authenticated state still requests a token_delta original", "the clean exact packet is published before mint", "the pair count is a power of two and complete pairs are unique", "forms remain equally represented and controls preserve the proposal mapping", "all pinned tokenizers load only after mint", "every finite supportive, null, or adverse result is filed"], planned_sample={"metric": "token_delta", "pairs": len(row["test_set"]), "forms": check["form_counts"], "models": spec["models"], "readers": 0, "items_sha256": row["items_sha256"]}, proposal_revision=row["slug"], store_manifest=True)["attempt"]
    attempt_path.write_text(json.dumps({"attempt": opened, "preflight": check}, indent=2) + "\n", encoding="utf-8")
    try:
        payload, computed = score(spec, row["forms"]); payload["attempt_id"] = opened["attempt_id"]; filed = client.measure(row["slug"], payload)
    except Exception as exc:
        state = client.attempt(opened["attempt_id"])
        if state.get("state") == "open":
            receipt = {"kind": "ainglish.deterministic-token-sweep-abort.v1", "at": datetime.now(timezone.utc).isoformat(), "error": f"{type(exc).__name__}: {exc}", "preflight": check}
            aborted = client.abort_attempt(opened["attempt_id"], "token sweep harness failed before measurement emission", receipt, failed_gate_kind="harness_error")
            abort_path.write_text(json.dumps({"receipt": receipt, "abort": aborted}, indent=2) + "\n", encoding="utf-8")
        raise
    result = {"kind": "ainglish.deterministic-token-sweep-result.v1", "campaign": args.campaign, "attempt": opened, "preflight": check, "computed": computed, "measurement": filed}
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    row_out = filed.get("measurement") or filed
    print(json.dumps({"campaign": args.campaign, "attempt_id": opened["attempt_id"], "manifest_commitment": check["manifest_commitment"], "value": computed["value"], "means": computed["means"], "form_means": computed["form_means"], "measurement_hash": row_out.get("hash") or row_out.get("manifest_hash")}, indent=2))


if __name__ == "__main__":
    main()
