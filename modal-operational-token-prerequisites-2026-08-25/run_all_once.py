#!/usr/bin/env python3
"""Mint, tokenize and file one frozen token prerequisite at a time."""

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


def load_campaign(name: str) -> tuple[dict, dict]:
    packet = json.loads((ROOT / "items.json").read_text(encoding="utf-8"))
    sealed = dict(packet); expected = sealed.pop("content_sha256")
    if hashlib.sha256(canonical(sealed)).hexdigest() != expected:
        raise RuntimeError("item packet drift")
    row = packet["campaigns"].get(name)
    if row is None:
        raise RuntimeError(f"unknown campaign {name!r}")
    if hashlib.sha256(canonical(row["test_set"])).hexdigest() != row["items_sha256"]:
        raise RuntimeError("campaign item digest drift")
    return packet, row


def preflight(client, name: str, row: dict) -> dict:
    if git("status", "--porcelain"):
        raise RuntimeError("repository is not clean")
    commit = git("rev-parse", "HEAD")
    if commit != git("rev-parse", "origin/main"):
        raise RuntimeError("HEAD is not published at origin/main")
    if importlib.metadata.version("tiktoken") != "0.13.0":
        raise RuntimeError("tiktoken version drift")
    suggestions = client.suggestions()
    queue = client.queue()
    proposal = client.proposal(row["slug"], authenticated=True)
    if proposal.get("stage") not in ("seconded", "measured") or proposal.get("superseded_by"):
        raise RuntimeError("proposal is not a current measurement surface")
    suggested = any(card.get("slug") == row["slug"] and card.get("executable_now") for card in suggestions.get("suggestions", []))
    queued = any(card.get("slug") == row["slug"] for card in queue.get("needs_measurement", []))
    if not suggested and not queued:
        raise RuntimeError("fresh suggestions and needs_measurement queue do not route this proposal")
    prior = [item for item in proposal.get("measurements", []) if item.get("metric") == "token_delta" and not item.get("is_replication")]
    if prior:
        raise RuntimeError("a token original already exists on this lifecycle")
    pairs = row["test_set"]
    if len(pairs) & (len(pairs) - 1):
        raise RuntimeError("pair count is not a power of two")
    return {
        "commit": commit, "suggestions_generated_at": suggestions.get("generated_at"),
        "stage": proposal.get("stage"), "prior_originals": 0,
        "routing": "personalized_suggestion" if suggested else "needs_measurement_queue",
    }


def manifest(name: str, row: dict, checked: dict) -> dict:
    return {
        "metric": "token_delta", "formula_version": 1,
        "construct": name, "models": list(ENCODINGS), "test_set": row["test_set"],
        "items_sha256": row["items_sha256"],
        "test_set_note": "Complete careful-English mappings are the confirmatory comparator; bare ambiguous modal wording is excluded.",
        "estimand": {
            "population": f"the {len(row['test_set'])} frozen complete pairs in items.json",
            "aggregation": "mean delta per tokenizer; headline is the least-favourable maximum tokenizer mean",
        },
        "environment": {"tiktoken": "0.13.0", "python": sys.version.split()[0]},
        "source": {
            "repository": "dexagon-ai/ainglish-evidence", "commit": checked["commit"],
            "path": "modal-operational-token-prerequisites-2026-08-25/items.json",
        },
    }


def score(manifest_obj: dict) -> tuple[dict, dict]:
    import tiktoken  # intentionally imported only after mint
    cells = {}
    means = {}
    form_means = {}
    for name in ENCODINGS:
        encode = tiktoken.get_encoding(name).encode
        values = [len(encode(row["ainglish"])) - len(encode(row["english"])) for row in manifest_obj["test_set"]]
        cells[name] = values
        means[name] = round(sum(values) / len(values), 8)
        forms = sorted({row["form"] for row in manifest_obj["test_set"]})
        form_means[name] = {
            form: round(sum(value for value, row in zip(values, manifest_obj["test_set"]) if row["form"] == form) / sum(row["form"] == form for row in manifest_obj["test_set"]), 8)
            for form in forms
        }
    payload = {
        "metric": "token_delta", "formula_version": 1,
        "value": max(means.values()), "value_lo": min(means.values()), "value_hi": max(means.values()),
        "panel_models": list(ENCODINGS),
        "per_member": [{"model": name, "value": means[name]} for name in ENCODINGS],
        "manifest": manifest_obj,
    }
    return payload, {"cells": cells, "means": means, "form_means": form_means, "value": payload["value"]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign", required=True, choices=("may-not", "must", "should", "will", "retention"))
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    attempt_path = ROOT / f"{args.campaign}.attempt.json"
    result_path = ROOT / f"{args.campaign}.measurement.json"
    if attempt_path.exists() or result_path.exists():
        raise SystemExit("REFUSING: local attempt/result receipt exists")
    _, row = load_campaign(args.campaign)
    client = ainglish_client()
    checked = preflight(client, args.campaign, row)
    manifest_obj = manifest(args.campaign, row, checked)
    if len(canonical(manifest_obj)) > 20_000:
        raise RuntimeError("manifest exceeds 20 KB")
    checked["manifest_commitment"] = manifest_commitment(manifest_obj)
    checked["manifest_bytes"] = len(canonical(manifest_obj))
    if args.preflight_only:
        print(json.dumps(checked, indent=2)); return
    opened = client.mint_attempt(
        row["slug"], manifest=manifest_obj,
        estimand=f"The least-favourable maximum across cl100k_base, o200k_base and p50k_base of mean token_delta on {len(row['test_set'])} frozen complete careful-English pairs.",
        admissibility_gates=[
            "fresh authenticated suggestions still route work on the current non-superseded lifecycle",
            "the current lifecycle has no prior token_delta original",
            "the clean source commit and exact complete-pair packet are public before mint",
            "the pair count remains a power of two and every complete pair is unique",
            "the three bare tokenizer roster identities load only after mint under tiktoken 0.13.0",
            "every finite result is filed regardless of direction or prerequisite interpretation",
        ],
        planned_sample={"metric": "token_delta", "pairs": len(row["test_set"]), "models": list(ENCODINGS), "items_sha256": row["items_sha256"], "readers": 0},
        store_manifest=True,
    )["attempt"]
    attempt_path.write_text(json.dumps({"attempt": opened, "preflight": checked}, indent=2) + "\n", encoding="utf-8")
    try:
        payload, computed = score(manifest_obj)
        payload["attempt_id"] = opened["attempt_id"]
        filed = client.measure(row["slug"], payload)
    except Exception as exc:
        state = client.attempt(opened["attempt_id"])
        if state.get("state") == "open":
            receipt = {"kind": "ainglish.token-prerequisite-abort.v1", "at": datetime.now(timezone.utc).isoformat(), "error": f"{type(exc).__name__}: {exc}"}
            client.abort_attempt(opened["attempt_id"], "token prerequisite harness failed", receipt, failed_gate_kind="harness_error")
        raise
    result = {"kind": "ainglish.modal-operational-token-original.v1", "campaign": args.campaign, "attempt": opened, "preflight": checked, "computed": computed, "measurement": filed}
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"campaign": args.campaign, "attempt_id": opened["attempt_id"], "manifest_hash": checked["manifest_commitment"], "value": computed["value"], "means": computed["means"], "form_means": computed["form_means"]}, indent=2))


if __name__ == "__main__":
    main()
