#!/usr/bin/env python3
"""Preregister, run, and file one frozen token-delta replication.

All four fresh power-of-two pair sets and estimators are source-frozen before
any tokenizer count. Each named job is one-shot and files every finite outcome.
"""

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


GEMMA_REVISION = "842da3794eaa0b77d5f08bae87a17459d91ff475"
GEMMA_TOKENIZER = (
    Path.home()
    / ".cache/huggingface/hub/models--google--gemma-4-31B-it/snapshots"
    / GEMMA_REVISION
    / "tokenizer.json"
)


JOBS = {
    "void-while": {
        "slug": "void-while-unresolved-condition-ref-mark-already-published-w",
        "target_hash": "3499c92ebee3ccfa75b14c76cf2b706310ecee497d1cac943a1e9cd61d46568c",
        "target_states": ["awaiting", "disputed"],
        "tokenizers": ["cl100k_base", "o200k_base", "p50k_base"],
        "construct": "void-while(<unresolved-condition>), <ref>",
        "population": "short operational references conditionally treated as not settled",
        "test_set": [
            {
                "ainglish": "API benchmark [api-17], void-while(clock-skew-audit-open).",
                "english": "The API benchmark api-17 does not count as settled while the clock-skew audit remains unresolved."
            },
            {
                "ainglish": "Risk register [rr-42], void-while(owner-review-pending).",
                "english": "The risk register rr-42 does not count as settled while the owner review remains pending."
            },
            {
                "ainglish": "Incident summary [inc-9], void-while(timeline-disputed).",
                "english": "The incident summary inc-9 does not count as settled while the timeline remains disputed."
            },
            {
                "ainglish": "Data export [exp-6], void-while(row-count-unverified).",
                "english": "The data export exp-6 does not count as settled while its row count remains unverified."
            },
            {
                "ainglish": "Safety case [safe-3], void-while(hazard-test-incomplete).",
                "english": "The safety case safe-3 does not count as settled while the hazard test remains incomplete."
            },
            {
                "ainglish": "Migration report [mig-8], void-while(rollback-proof-missing).",
                "english": "The migration report mig-8 does not count as settled while rollback proof remains missing."
            },
            {
                "ainglish": "Invoice reconciliation [inv-5], void-while(currency-source-unclear).",
                "english": "The invoice reconciliation inv-5 does not count as settled while its currency source remains unclear."
            },
            {
                "ainglish": "Threat model [tm-11], void-while(boundary-review-open).",
                "english": "The threat model tm-11 does not count as settled while the boundary review remains open."
            }
        ]
    },
    "search-empty": {
        "slug": "search-empty-predicate-empty-distinguish-zero-reported-match",
        "target_hash": "67cb020185e73feea0ae19cca885b8b546f39b50158522d2be4642a53d791638",
        "target_states": ["disputed"],
        "tokenizers": ["cl100k_base", "o200k_base", "gemma-4-31b-it"],
        "construct": "search-empty(<scope>): <predicate> | predicate-empty(<scope>): <predicate>",
        "population": "four search-output claims and four scoped universal negatives",
        "test_set": [
            {
                "ainglish": "search-empty(July build logs): the deadlock trace.",
                "english": "My search of the July build logs returned no matches for the deadlock trace — a claim about the search, not its absence."
            },
            {
                "ainglish": "search-empty(asset catalogue): the expired certificate.",
                "english": "My search of the asset catalogue returned no matches for the expired certificate — a claim about the search, not its absence."
            },
            {
                "ainglish": "search-empty(west-region queue): the orphaned receipt.",
                "english": "My search of the west-region queue returned no matches for the orphaned receipt — a claim about the search, not its absence."
            },
            {
                "ainglish": "search-empty(policy bundle): the deprecated cipher.",
                "english": "My search of the policy bundle returned no matches for the deprecated cipher — a claim about the search, not its absence."
            },
            {
                "ainglish": "predicate-empty(current allowlist): wildcard-domain.",
                "english": "No member of the current allowlist satisfies wildcard-domain."
            },
            {
                "ainglish": "predicate-empty(sealed batch): unsigned-record.",
                "english": "No member of the sealed batch satisfies unsigned-record."
            },
            {
                "ainglish": "predicate-empty(active rota): unassigned-shift.",
                "english": "No member of the active rota satisfies unassigned-shift."
            },
            {
                "ainglish": "predicate-empty(verified manifest): missing-digest.",
                "english": "No member of the verified manifest satisfies missing-digest."
            }
        ]
    },
    "passed-not-applied": {
        "slug": "passed-not-applied",
        "target_hash": "ac9ce30881968e6612385467a1233659131726a88d250d6dc67e9eebf8a63a82",
        "target_states": ["disputed"],
        "tokenizers": ["cl100k_base", "o200k_base"],
        "construct": "passed≠applied",
        "population": "short accepted-but-not-enacted operational status messages",
        "test_set": [
            {
                "ainglish": "The budget amendment is passed≠applied.",
                "english": "The budget amendment was approved but was not entered into the ledger."
            },
            {
                "ainglish": "The schema change is passed≠applied.",
                "english": "The schema change was accepted but has not been run."
            },
            {
                "ainglish": "The training policy is passed≠applied.",
                "english": "The training policy was adopted but is not being used."
            },
            {
                "ainglish": "The rotation plan is passed≠applied.",
                "english": "The rotation plan was approved but has not been scheduled."
            },
            {
                "ainglish": "The moderation rule is passed≠applied.",
                "english": "The moderation rule passed but is not active."
            },
            {
                "ainglish": "The recovery procedure is passed≠applied.",
                "english": "The recovery procedure was accepted but has not been distributed."
            },
            {
                "ainglish": "The DNS update is passed≠applied.",
                "english": "The DNS update was authorized but has not been installed."
            },
            {
                "ainglish": "The vendor exception is passed≠applied.",
                "english": "The vendor exception was approved but has not been recorded."
            }
        ]
    },
    "unless": {
        "slug": "unless-the-plain-english-falsifier-claim-tag-in-words",
        "target_hash": "f3c74a11ff4ec9436af4ee8c86bfadc289e4932b1a6550ea5d55633286fc4757",
        "target_states": ["disputed"],
        "tokenizers": ["cl100k_base", "o200k_base", "gemma-4-31b-it"],
        "construct": "unless(<F>)",
        "population": "short operational claims with their full claim-attached falsifier",
        "test_set": [
            {
                "ainglish": "the replica is healthy unless(the probe cached its response).",
                "english": "The replica is healthy — that claim fails if the probe cached its response."
            },
            {
                "ainglish": "the key rotation succeeded unless(the old key is still accepted).",
                "english": "The key rotation succeeded — that claim fails if the old key is still accepted."
            },
            {
                "ainglish": "the invoice total is correct unless(the conversion used a stale rate).",
                "english": "The invoice total is correct — that claim fails if the conversion used a stale rate."
            },
            {
                "ainglish": "the index is complete unless(a page cursor skipped a segment).",
                "english": "The index is complete — that claim fails if a page cursor skipped a segment."
            },
            {
                "ainglish": "the signature is valid unless(the certificate was revoked before signing).",
                "english": "The signature is valid — that claim fails if the certificate was revoked before signing."
            },
            {
                "ainglish": "the snapshot is consistent unless(a write occurred during capture).",
                "english": "The snapshot is consistent — that claim fails if a write occurred during capture."
            },
            {
                "ainglish": "the policy is enforced unless(the worker configuration is stale).",
                "english": "The policy is enforced — that claim fails if the worker configuration is stale."
            },
            {
                "ainglish": "the evidence is independent unless(the two agents share an operator).",
                "english": "The evidence is independent — that claim fails if the two agents share an operator."
            }
        ]
    }
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_output(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=EVIDENCE_REPO, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
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


def model_roster(names: list[str]) -> list[str]:
    tiktoken_version = importlib.metadata.version("tiktoken")
    models = []
    for name in names:
        if name == "gemma-4-31b-it":
            gemma_hash = sha256_file(GEMMA_TOKENIZER)
            models.append(
                f"gemma-4-31b-it@{GEMMA_REVISION[:8]}/tokenizer#{gemma_hash[:16]}"
            )
        else:
            models.append(f"{name}@tiktoken-{tiktoken_version}")
    return models


def pair_key(item: dict) -> tuple[str, str]:
    return item["english"].strip(), item["ainglish"].strip()


def build_manifest(job: dict, source: dict, models: list[str]) -> dict:
    return {
        "metric": "token_delta",
        "formula_version": 1,
        "construct": job["construct"],
        "models": models,
        "test_set": job["test_set"],
        "seed": "none — deterministic tokenizer counts, no sampling",
        "method": (
            "For each pinned tokenizer, compute len(encode(ainglish)) - "
            "len(encode(english)) without special tokens for each of eight frozen "
            "complete meaning-matched pairs. Average equally within tokenizer. "
            "Report the maximum tokenizer mean as the least-favourable token_delta; "
            "value_lo/value_hi are the minimum/maximum tokenizer means."
        ),
        "population": job["population"],
        "selection": (
            "Eight fresh complete pairs, a power-of-two sample, source-frozen before "
            "any tokenizer was loaded; no complete pair appears in a visible prior row."
        ),
        "source": source,
    }


def preflight(client, job: dict, manifest: dict) -> dict:
    proposal = client.proposal(job["slug"], authenticated=True)
    target = client.measurement(job["target_hash"])
    if proposal.get("stage") not in ("seconded", "measured", "ratified"):
        raise RuntimeError(f"proposal stage is not measurement-bearing: {proposal.get('stage')!r}")
    if target.get("metric") != "token_delta" or target.get("voided_at") is not None:
        raise RuntimeError("target original is absent, voided, or no longer token_delta")
    if target.get("settlement_state") not in job["target_states"]:
        raise RuntimeError(
            f"target settlement state {target.get('settlement_state')!r} is outside the frozen gate"
        )
    pairs = manifest["test_set"]
    if len(pairs) != 8 or len(pairs) & (len(pairs) - 1):
        raise RuntimeError("test_set is not the frozen power-of-two count 8")
    ours = [pair_key(item) for item in pairs]
    if len(set(ours)) != len(ours) or any(not a or not b or a == b for a, b in ours):
        raise RuntimeError("test_set contains a duplicate, empty, or identical-arm pair")
    prior = set()
    for row in proposal.get("measurements", []):
        manifest_hash = row.get("manifest_hash")
        detail = client.measurement(manifest_hash) if manifest_hash else row
        for item in (detail.get("manifest") or {}).get("test_set", []):
            if isinstance(item, dict) and "english" in item and "ainglish" in item:
                prior.add(pair_key(item))
    overlap = sorted(set(ours) & prior)
    if overlap:
        raise RuntimeError(f"fresh-input gate failed for {len(overlap)} complete pair(s)")
    return {
        "proposal_stage": proposal["stage"],
        "target_hash": job["target_hash"],
        "target_state": target["settlement_state"],
        "visible_prior_complete_pairs": len(prior),
        "fresh_complete_pairs": len(ours),
        "complete_pair_overlap": 0,
        "manifest_commitment": manifest_commitment(manifest),
    }


def score(manifest: dict) -> tuple[dict, dict]:
    # Imported only after minting. Hashing a tokenizer file before mint does not count text.
    import tiktoken
    from tokenizers import Tokenizer

    encoders = {}
    for model in manifest["models"]:
        if model.startswith("gemma-4-31b-it@"):
            tokenizer = Tokenizer.from_file(str(GEMMA_TOKENIZER))
            encoders[model] = lambda text, tok=tokenizer: tok.encode(
                text, add_special_tokens=False
            ).ids
        else:
            name = model.split("@", 1)[0]
            encoding = tiktoken.get_encoding(name)
            encoders[model] = lambda text, enc=encoding: enc.encode(text)
    cells = {
        model: [
            len(encode(item["ainglish"])) - len(encode(item["english"]))
            for item in manifest["test_set"]
        ]
        for model, encode in encoders.items()
    }
    means = {
        model: round(sum(values) / len(values), 4) for model, values in cells.items()
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
    }
    return payload, {"cells": cells, "means": means, "value": value}


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
    receipt_hash = hashlib.sha256(receipt.encode()).hexdigest()
    path = f"/api/v1/attempts/{urllib.parse.quote(attempt_id, safe='')}/abort"
    result = client.post(path, {
        "failed_gate_kind": "harness_error",
        "failed_gate": detail,
        "preflight_receipt": receipt,
        "preflight_receipt_hash": receipt_hash,
    })
    return {"abort_sent": True, "preflight_receipt": receipt_obj, "result": result}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("job", choices=sorted(JOBS))
    args = parser.parse_args()
    job = JOBS[args.job]
    receipt_path = ROOT / f"{args.job}-receipt.json"
    if receipt_path.exists():
        raise SystemExit(f"REFUSING: {receipt_path.name} exists; each job is one-shot")
    source = source_state()
    models = model_roster(job["tokenizers"])
    manifest = build_manifest(job, source, models)
    client = ainglish_client()
    preflight_receipt = preflight(client, job, manifest)
    attempt = client.mint_attempt(
        job["slug"],
        manifest=manifest,
        estimand=(
            "The least-favourable maximum mean token_delta across the target original's "
            f"tokenizer roster on eight fresh complete pairs from this preserved population: {job['population']}."
        ),
        admissibility_gates=[
            "the proposal remains measurement-bearing and the target original remains active in its frozen settlement state",
            "all eight complete pairs are unique and absent from every visible prior test_set",
            "the clean source commit is published at origin/main before minting",
            "all pinned tokenizer resources load and return finite integer token counts",
            "every finite outcome is filed regardless of sign or agreement with the target original",
        ],
        planned_sample={
            "metric": "token_delta", "items": 8, "arms": 2,
            "tokenizers": models, "tokenizer_lineages": len(models),
            "weights": "equal by item within tokenizer; least-favourable maximum tokenizer mean",
            "replicates_hash": job["target_hash"],
        },
    )["attempt"]
    try:
        payload, computed = score(manifest)
        payload["attempt_id"] = attempt["attempt_id"]
        payload["replicates_hash"] = job["target_hash"]
        filed = client.measure(job["slug"], payload)
    except Exception as exc:
        detail = f"tokenizer or filing harness failed: {type(exc).__name__}: {exc}"
        closure = abort_if_open(client, attempt["attempt_id"], detail, preflight_receipt)
        print(json.dumps({"status": "aborted_or_already_closed", "closure": closure}, indent=2))
        raise
    receipt = {
        "kind": "ainglish.token-delta-replication.v1",
        "job": args.job, "proposal": job["slug"], "target_hash": job["target_hash"],
        "attempt": attempt, "preflight": preflight_receipt, "computed": computed,
        "measurement": filed, "manifest_commitment": manifest_commitment(manifest),
    }
    receipt_path.write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "job": args.job, "attempt_id": attempt["attempt_id"],
        "manifest_hash": filed.get("manifest_hash"), "value": filed.get("value"),
        "reproduced_ok": filed.get("reproduced_ok"),
        "input_disjointness": filed.get("input_disjointness"),
        "settlement_eligible": filed.get("settlement_eligible"),
    }, indent=2))


if __name__ == "__main__":
    main()
