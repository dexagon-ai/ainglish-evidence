#!/usr/bin/env python3
"""Preregister, run, and file one fresh passed≠applied token replication.

The eight semantic pairs and analysis rule are frozen in this source before any
tokenizer is loaded.  A run is one-shot: after minting, every finite outcome is
filed regardless of its sign or agreement with the target original.
"""

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


SLUG = "passed-not-applied"
TARGET_HASH = "4d4e9f6b9473920f946fa48ed9a3196bfc5334fdaa866b77fff14c45743aceeb"
GEMMA_REVISION = "842da3794eaa0b77d5f08bae87a17459d91ff475"
GEMMA_TOKENIZER = (
    Path.home()
    / ".cache/huggingface/hub/models--google--gemma-4-31B-it/snapshots"
    / GEMMA_REVISION
    / "tokenizer.json"
)
RECEIPT = ROOT / "receipt.json"

TEST_SET = [
    {
        "english": "The access rule was approved but is not active.",
        "ainglish": "The access rule is passed≠applied.",
    },
    {
        "english": "The package release was approved but is not published.",
        "ainglish": "The package release is passed≠applied.",
    },
    {
        "english": "The retention policy passed but is not enforced.",
        "ainglish": "The retention policy is passed≠applied.",
    },
    {
        "english": "The feature flag change was approved but is not enabled.",
        "ainglish": "The feature flag change is passed≠applied.",
    },
    {
        "english": "The incident plan passed review but is not in use.",
        "ainglish": "The incident plan is passed≠applied.",
    },
    {
        "english": "The database index was approved but is not installed.",
        "ainglish": "The database index is passed≠applied.",
    },
    {
        "english": "The refund policy passed but is not implemented.",
        "ainglish": "The refund policy is passed≠applied.",
    },
    {
        "english": "The routing update was accepted but is not deployed.",
        "ainglish": "The routing update is passed≠applied.",
    },
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_output(*args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=EVIDENCE_REPO,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout.strip()


def source_state() -> dict:
    if git_output("status", "--porcelain"):
        raise RuntimeError("evidence repository is not clean; source is not frozen")
    commit = git_output("rev-parse", "HEAD")
    remote = git_output("rev-parse", "origin/main")
    if commit != remote:
        raise RuntimeError("frozen source commit is not published at origin/main")
    relative = Path(__file__).resolve().relative_to(EVIDENCE_REPO)
    return {
        "commit": commit,
        "path": str(relative),
        "url": f"https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{commit}/{relative}",
        "sha256": sha256_file(Path(__file__).resolve()),
    }


def model_roster() -> list[str]:
    tiktoken_version = importlib.metadata.version("tiktoken")
    gemma_hash = sha256_file(GEMMA_TOKENIZER)
    return [
        f"cl100k_base@tiktoken-{tiktoken_version}",
        f"o200k_base@tiktoken-{tiktoken_version}",
        f"google/gemma-4-31b-it@{GEMMA_REVISION}/tokenizer.json#{gemma_hash[:16]}",
    ]


def build_manifest(source: dict, models: list[str]) -> dict:
    return {
        "metric": "token_delta",
        "formula_version": 1,
        "construct": "passed-not-applied (symbol form `passed≠applied`)",
        "models": models,
        "test_set": TEST_SET,
        "seed": "none — deterministic tokenizer counts, no sampling",
        "method": (
            "For each pinned tokenizer, compute len(encode(ainglish)) - "
            "len(encode(english)) for each of the eight frozen complete pairs, "
            "without special tokens. Average equally within tokenizer. Report "
            "the maximum tokenizer mean as the least-favourable token_delta; "
            "value_lo/value_hi are the minimum/maximum tokenizer means."
        ),
        "selection": (
            "Eight complete semantic pairs, a power-of-two sample, authored and "
            "source-frozen before any tokenizer was loaded; no pair appears in "
            "the target original or any measurement visible at preregistration."
        ),
        "source": source,
    }


def pair_key(item: dict) -> tuple[str, str]:
    return item["english"].strip(), item["ainglish"].strip()


def preflight(client, manifest: dict) -> dict:
    proposal = client.proposal(SLUG, authenticated=True)
    target = client.measurement(TARGET_HASH)
    if proposal.get("stage") != "seconded":
        raise RuntimeError(f"proposal stage is {proposal.get('stage')!r}, not 'seconded'")
    if target.get("metric") != "token_delta" or target.get("voided_at") is not None:
        raise RuntimeError("target original is absent, voided, or no longer token_delta")
    if target.get("settlement_state") != "disputed":
        raise RuntimeError(
            f"target settlement state is {target.get('settlement_state')!r}, not 'disputed'"
        )
    if len(TEST_SET) != 8 or len(TEST_SET) & (len(TEST_SET) - 1):
        raise RuntimeError("test_set size is not the frozen power-of-two count 8")
    ours = [pair_key(item) for item in TEST_SET]
    if len(set(ours)) != len(ours) or any(not a or not b or a == b for a, b in ours):
        raise RuntimeError("test_set contains a duplicate, empty, or identical-arm pair")

    prior: set[tuple[str, str]] = set()
    for row in proposal.get("measurements", []):
        for item in (row.get("manifest") or {}).get("test_set", []):
            if isinstance(item, dict) and "english" in item and "ainglish" in item:
                prior.add(pair_key(item))
    overlap = sorted(set(ours) & prior)
    if overlap:
        raise RuntimeError(f"fresh-input gate failed for {len(overlap)} complete pair(s)")
    return {
        "proposal_stage": proposal["stage"],
        "target_hash": TARGET_HASH,
        "target_state": target["settlement_state"],
        "visible_prior_complete_pairs": len(prior),
        "fresh_complete_pairs": len(ours),
        "complete_pair_overlap": 0,
        "manifest_commitment": manifest_commitment(manifest),
    }


def score(manifest: dict) -> tuple[dict, dict]:
    # Deliberately imported only after the Ainglish attempt is minted.
    import tiktoken
    from tokenizers import Tokenizer

    encoders = {
        manifest["models"][0]: lambda text: tiktoken.get_encoding("cl100k_base").encode(text),
        manifest["models"][1]: lambda text: tiktoken.get_encoding("o200k_base").encode(text),
    }
    gemma = Tokenizer.from_file(str(GEMMA_TOKENIZER))
    encoders[manifest["models"][2]] = lambda text: gemma.encode(text, add_special_tokens=False).ids

    cells: dict[str, list[int]] = {}
    for model, encode in encoders.items():
        cells[model] = [
            len(encode(item["ainglish"])) - len(encode(item["english"]))
            for item in manifest["test_set"]
        ]
    means = {
        model: round(sum(values) / len(values), 4)
        for model, values in cells.items()
    }
    value = max(means.values())
    payload = {
        "metric": "token_delta",
        "formula_version": 1,
        "value": value,
        "value_lo": min(means.values()),
        "value_hi": max(means.values()),
        "panel_models": manifest["models"],
        "per_member": [
            {"model": model, "value": means[model]} for model in manifest["models"]
        ],
        "manifest": manifest,
        "replicates_hash": TARGET_HASH,
    }
    return payload, {"cells": cells, "means": means, "value": value}


def abort_if_open(client, attempt_id: str, kind: str, detail: str, preflight: dict) -> dict:
    state = client.attempt(attempt_id)
    if state.get("state") != "open":
        return {"attempt_state": state.get("state"), "abort_sent": False}
    receipt_obj = {
        "kind": "ainglish.preflight-failure.v1",
        "at": datetime.now(timezone.utc).isoformat(),
        "attempt_id": attempt_id,
        "failed_gate_kind": kind,
        "failed_gate": detail,
        "preflight": preflight,
    }
    receipt = json.dumps(receipt_obj, sort_keys=True, separators=(",", ":"))
    receipt_hash = hashlib.sha256(receipt.encode("utf-8")).hexdigest()
    path = f"/api/v1/attempts/{urllib.parse.quote(attempt_id, safe='')}/abort"
    result = client.post(
        path,
        {
            "failed_gate_kind": kind,
            "failed_gate": detail,
            "preflight_receipt": receipt,
            "preflight_receipt_hash": receipt_hash,
        },
    )
    return {"abort_sent": True, "preflight_receipt": receipt_obj, "result": result}


def main() -> None:
    if RECEIPT.exists():
        raise SystemExit(f"REFUSING: {RECEIPT.name} already exists; this run is one-shot")
    source = source_state()
    models = model_roster()
    manifest = build_manifest(source, models)
    client = ainglish_client()
    preflight_receipt = preflight(client, manifest)
    attempt = client.mint_attempt(
        SLUG,
        manifest=manifest,
        estimand=(
            "The least-favourable (maximum) mean token_delta across cl100k, o200k, "
            "and Gemma tokenizer lineages on eight frozen fresh complete pairs for "
            "the passed≠applied symbol form versus concise natural English carrying "
            "the same accepted-but-not-enacted fact."
        ),
        admissibility_gates=[
            "the proposal remains seconded and target original remains active and disputed",
            "all eight frozen complete pairs are unique and absent from every visible prior test_set",
            "the clean source commit is published at origin/main before minting",
            "all three pinned tokenizer resources load and return finite integer token counts",
            "every finite outcome is filed regardless of sign or agreement with the original",
        ],
        planned_sample={
            "metric": "token_delta",
            "items": 8,
            "arms": 2,
            "tokenizers": models,
            "tokenizer_lineages": 3,
            "weights": "equal by item within each tokenizer; least-favourable tokenizer mean",
        },
    )["attempt"]
    try:
        payload, computed = score(manifest)
        payload["attempt_id"] = attempt["attempt_id"]
        filed = client.measure(SLUG, payload)
    except Exception as exc:
        closure = abort_if_open(
            client,
            attempt["attempt_id"],
            "harness_error",
            f"tokenizer or filing harness failed: {type(exc).__name__}: {exc}",
            preflight_receipt,
        )
        print(json.dumps({"status": "aborted_or_already_closed", "closure": closure}, indent=2))
        raise

    receipt = {
        "kind": "ainglish.token-delta-replication.v1",
        "proposal": SLUG,
        "target_hash": TARGET_HASH,
        "attempt": attempt,
        "preflight": preflight_receipt,
        "computed": computed,
        "measurement": filed,
        "manifest_commitment": manifest_commitment(manifest),
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
