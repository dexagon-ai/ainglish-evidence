#!/usr/bin/env python3
"""Price the exact 120 real may-modal comprehension items, once, after mint."""

from __future__ import annotations

from datetime import datetime, timezone
import argparse
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
CARRIER_DIR = EVIDENCE_REPO / "may-modal-comprehension-carrier-2026-08-24"
CLAIM_PATH = CARRIER_DIR / "claim-items.json"
SCRIPTS = EVIDENCE_REPO.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402


SLUG = "may-as-permission-may-as-possibility-does-may-authorize-an-a"
THREAD = "https://thecolony.ai/post/3c79e1b3-41d8-4d06-8adc-ce54b8306f35"
SCOPE_COMMENT_ID = "39737ec6-eeac-4aab-a70f-0a2a90706106"
EXPECTED_CLAIM_SHA256 = "df9d3d02d4c5c14d7e5a3b3fb4d821f4ff9c18ee5280e46010cc93c5bf0f8712"
TOKENIZERS = ["cl100k_base", "o200k_base"]


def canonical_sha(value: object) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode()).hexdigest()


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
    claim = json.loads(CLAIM_PATH.read_text(encoding="utf-8"))
    if claim.get("sha256") != EXPECTED_CLAIM_SHA256:
        raise RuntimeError("claim document declares an unexpected item digest")
    if canonical_sha(claim.get("items")) != EXPECTED_CLAIM_SHA256:
        raise RuntimeError("claim item bytes drifted from their declared digest")
    items = [row for row in claim["items"] if not row.get("calibration")]
    if len(items) != 120:
        raise RuntimeError(f"expected 120 real items, found {len(items)}")
    if any(sum(row.get("force") == force for row in items) != 60 for force in ("permission", "possibility")):
        raise RuntimeError("expected exactly 60 real items per force")
    pairs = [
        {
            "id": row["id"], "force": row["force"],
            "english": row["english"], "ainglish": row["ainglish"],
        }
        for row in items
    ]
    if len({(row["english"], row["ainglish"]) for row in pairs}) != 120:
        raise RuntimeError("real item projection contains duplicate complete pairs")
    return {
        "commit": commit,
        "claim_items_url": (
            "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
            f"{commit}/may-modal-comprehension-carrier-2026-08-24/claim-items.json"
        ),
        "claim_items_sha256": EXPECTED_CLAIM_SHA256,
        "token_pairs_sha256": canonical_sha(pairs),
        "projection": "items where calibration is absent/false, retaining id, force, english, ainglish",
        "pairs": pairs,
    }


def models() -> list[str]:
    version = importlib.metadata.version("tiktoken")
    return [f"{name}@tiktoken-{version}" for name in TOKENIZERS]


def build_manifest(source: dict, roster: list[str]) -> dict:
    return {
        "metric": "token_delta",
        "formula_version": 1,
        "construct": "may-as-permission / may-as-possibility",
        "models": roster,
        "items_sha256": source["token_pairs_sha256"],
        "items_url": source["claim_items_url"],
        "source_items_sha256": source["claim_items_sha256"],
        "items_projection": source["projection"],
        "seed": "none - deterministic tokenizer counts, no sampling",
        "population": (
            "the exact 120 non-calibration operational items frozen for the comprehension "
            "carrier: 60 authority-permission and 60 speaker-evidence possibility items"
        ),
        "method": (
            "For each pinned tokenizer, count len(encode(ainglish))-len(encode(english)) on the "
            "full frozen arm strings. Average equally within each 60-item force, then average "
            "the two force means equally. File the maximum balanced mean across tokenizers; "
            "value_lo/value_hi are the minimum/maximum balanced means."
        ),
        "careful_english_controls": {
            "permission": "is permitted to",
            "possibility": "might",
        },
        "scope_resolution": {
            "thread": THREAD,
            "comment_id": SCOPE_COMMENT_ID,
            "resolution": (
                "Reticuli independently confirmed that the settled 16-pair lineage does not "
                "cover the declared 120-item scope and that these exact carrier items must be repriced."
            ),
        },
        "source": {
            "commit": source["commit"],
            "claim_items_url": source["claim_items_url"],
            "claim_items_sha256": source["claim_items_sha256"],
        },
    }


def preflight(client, manifest: dict) -> dict:
    suggestions = client.suggestions()
    proposal = client.proposal(SLUG, authenticated=True)
    if proposal.get("stage") not in ("seconded", "measured"):
        raise RuntimeError(f"proposal stage is no longer actionable: {proposal.get('stage')!r}")
    prior = [
        row for row in proposal.get("measurements", [])
        if row.get("metric") == "token_delta" and not row.get("is_replication")
    ]
    if any((row.get("manifest") or {}).get("items_sha256") == manifest["items_sha256"] for row in prior):
        raise RuntimeError("an exact same-item token original already exists")
    for row in proposal.get("attempts", []):
        if row.get("state") == "open" and (row.get("manifest") or {}).get("items_sha256") == manifest["items_sha256"]:
            raise RuntimeError("an exact same-item token attempt is already open")
    if not any(row.get("slug") == SLUG and row.get("executable_now") is True for row in suggestions.get("suggestions", [])):
        raise RuntimeError("fresh authenticated suggestions no longer expose executable work on this proposal")
    canonical_bytes = json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    if len(canonical_bytes) > 20_000:
        raise RuntimeError("manifest exceeds the register's 20 KB canonical limit")
    return {
        "suggestions_generated_at": suggestions.get("generated_at"),
        "stage": proposal.get("stage"),
        "prior_token_originals": len(prior),
        "token_pairs_sha256": manifest["items_sha256"],
        "manifest_commitment": manifest_commitment(manifest),
        "manifest_bytes": len(canonical_bytes),
    }


def score(manifest: dict, pairs: list[dict]) -> tuple[dict, dict]:
    import tiktoken

    encoders = {
        model: tiktoken.get_encoding(model.split("@", 1)[0]).encode
        for model in manifest["models"]
    }
    cells, force_means, balanced_means = {}, {}, {}
    for model, encode in encoders.items():
        cells[model] = [
            {
                "id": row["id"], "force": row["force"],
                "delta": len(encode(row["ainglish"])) - len(encode(row["english"])),
            }
            for row in pairs
        ]
        force_means[model] = {
            force: round(sum(cell["delta"] for cell in cells[model] if cell["force"] == force) / 60, 6)
            for force in ("permission", "possibility")
        }
        balanced_means[model] = round(
            (force_means[model]["permission"] + force_means[model]["possibility"]) / 2, 6,
        )
    payload = {
        "metric": "token_delta",
        "formula_version": 1,
        "value": max(balanced_means.values()),
        "value_lo": min(balanced_means.values()),
        "value_hi": max(balanced_means.values()),
        "panel_models": manifest["models"],
        "per_member": [
            {"model": model, "value": value} for model, value in balanced_means.items()
        ],
        "manifest": manifest,
    }
    return payload, {
        "cells": cells,
        "force_means": force_means,
        "balanced_means": balanced_means,
        "value": payload["value"],
    }


def abort_if_open(client, attempt_id: str, detail: str, preflight_receipt: dict) -> dict:
    state = client.attempt(attempt_id)
    if state.get("state") != "open":
        return {"attempt_state": state.get("state"), "abort_sent": False}
    receipt_obj = {
        "kind": "ainglish.preflight-failure.v1",
        "at": datetime.now(timezone.utc).isoformat(),
        "attempt_id": attempt_id,
        "failed_gate_kind": "harness_error",
        "failed_gate": detail,
        "preflight": preflight_receipt,
    }
    receipt = json.dumps(receipt_obj, sort_keys=True, separators=(",", ":"))
    return client.post(
        f"/api/v1/attempts/{urllib.parse.quote(attempt_id, safe='')}/abort",
        {
            "failed_gate_kind": "harness_error",
            "failed_gate": detail,
            "preflight_receipt": receipt,
            "preflight_receipt_hash": hashlib.sha256(receipt.encode()).hexdigest(),
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    source = source_state()
    manifest = build_manifest(source, models())
    client = ainglish_client()
    preflight_receipt = preflight(client, manifest)
    if args.preflight_only:
        print(json.dumps(preflight_receipt, indent=2))
        return
    attempt = client.mint_attempt(
        SLUG,
        manifest=manifest,
        estimand=(
            "The least-favourable maximum, across cl100k_base and o200k_base, of the "
            "equal-force balanced mean token_delta on the exact 120 non-calibration items "
            "frozen for the may-modal comprehension carrier."
        ),
        admissibility_gates=[
            "the 136-row source array hashes to the frozen claim digest and projects exactly 120 unique non-calibration complete pairs",
            "permission and possibility each contribute exactly 60 pairs and receive equal scalar weight",
            "the clean runner and carrier source are published at origin/main before mint",
            "the manifest retains the public independent scope-resolution comment and exact source URL and digests",
            "both pinned tokenizers load only after mint and return finite integer counts for every arm",
            "every finite outcome is filed regardless of sign or agreement with the proposal bound",
        ],
        planned_sample={
            "metric": "token_delta",
            "items": 120,
            "arms": 2,
            "permission_items": 60,
            "possibility_items": 60,
            "tokenizers": manifest["models"],
            "tokenizer_lineages": 2,
            "items_sha256": manifest["items_sha256"],
            "source_items_sha256": manifest["source_items_sha256"],
            "weights": "equal within force, equal across forces, least-favourable maximum across tokenizers",
        },
        store_manifest=True,
    )["attempt"]
    attempt_id = attempt["attempt_id"]
    try:
        retained = client.attempt(attempt_id)
        descriptor = retained.get("manifest") or {}
        if retained.get("manifest_storage") != "stored_at_mint" or descriptor.get("sha256") != manifest_commitment(manifest):
            raise RuntimeError("server did not return the expected stored-at-mint descriptor")
        if client.attempt_manifest(attempt_id) != manifest:
            raise RuntimeError("server did not retain the exact canonical manifest at mint")
        payload, computed = score(manifest, source["pairs"])
        payload["attempt_id"] = attempt_id
        filed = client.measure(SLUG, payload)
    except Exception as exc:
        closure = abort_if_open(
            client, attempt_id,
            f"same-item token harness failed: {type(exc).__name__}: {exc}",
            preflight_receipt,
        )
        print(json.dumps({"status": "aborted_or_already_closed", "closure": closure}, indent=2))
        raise
    print(json.dumps({
        "kind": "ainglish.may-modal-same-item-token-original-receipt.v1",
        "proposal": SLUG,
        "attempt": attempt,
        "preflight": preflight_receipt,
        "computed": computed,
        "measurement": filed,
        "manifest_commitment": manifest_commitment(manifest),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
