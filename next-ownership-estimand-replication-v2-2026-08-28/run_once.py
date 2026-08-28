#!/usr/bin/env python3
"""Preregister, execute, and file one fresh next-ownership token replication."""

from __future__ import annotations

from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys

from ainglish.client import manifest_commitment


ROOT = Path(__file__).resolve().parent
EVIDENCE_REPO = ROOT.parent
SCRIPTS = EVIDENCE_REPO.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402


SLUG = "next-you-next-me-next-any-next-none-mark-who-owns-the-next-s-2"
TARGET_HASH = "8b677ae6f86582f31c38351bf44c243d4b327757d12a3bbae1d27fecd8ca13da"
RECEIPT = ROOT / "receipt.json"
ENCODINGS = ["cl100k_base", "o200k_base", "p50k_base"]
MODELS = [f"tiktoken/{name}" for name in ENCODINGS]
OWNERS = ["next-you", "next-me", "next-any", "next-none"]
SETTLEMENT_STRATA = [{"id": owner, "weight": 1} for owner in OWNERS]


def pair(clause: str, owner: str, control: str) -> dict[str, str]:
    return {
        "owner": owner,
        "ainglish": f"{clause}, {owner}.",
        "english": f"{clause}; {control}.",
    }


TEST_SET = [
    pair("The accessibility captions have passed the spot check", "next-you", "the next step belongs to you"),
    pair("The supplier exception is annotated with its expiry date", "next-you", "the next step belongs to you"),
    pair("The offline recovery card has been sealed in the cabinet", "next-you", "the next step belongs to you"),
    pair("The translated consent notice is ready for legal review", "next-you", "the next step belongs to you"),
    pair("The telemetry gap is narrowed to one collection interval", "next-you", "the next step belongs to you"),
    pair("The replacement cable is labelled at both ends", "next-you", "the next step belongs to you"),
    pair("The data-retention exception now names its approving role", "next-you", "the next step belongs to you"),
    pair("The accessibility conformance report includes the new screenshots", "next-you", "the next step belongs to you"),
    pair("I am reconciling the cold-store inventory against the courier sheet", "next-me", "the next step belongs to me"),
    pair("I am tracing the intermittent clock skew through the standby node", "next-me", "the next step belongs to me"),
    pair("I will obtain the venue's updated evacuation diagram", "next-me", "the next step belongs to me"),
    pair("I am checking the anonymisation sample for rare combinations", "next-me", "the next step belongs to me"),
    pair("I will compare the signed minutes with the audio timestamp", "next-me", "the next step belongs to me"),
    pair("I am rebuilding the multilingual search fixture", "next-me", "the next step belongs to me"),
    pair("I will ask the archive custodian about the missing accession number", "next-me", "the next step belongs to me"),
    pair("I am testing the emergency contact cascade from the second branch", "next-me", "the next step belongs to me"),
    pair("The uncategorised accessibility tickets need an owner", "next-any", "the next step belongs to whoever acts first"),
    pair("A faded equipment label needs replacing", "next-any", "the next step belongs to whoever acts first"),
    pair("The untranslated footer string needs a native-language check", "next-any", "the next step belongs to whoever acts first"),
    pair("One duplicate calendar invitation needs cancelling", "next-any", "the next step belongs to whoever acts first"),
    pair("The spare handset needs a battery-health reading", "next-any", "the next step belongs to whoever acts first"),
    pair("A broken citation anchor needs a stable destination", "next-any", "the next step belongs to whoever acts first"),
    pair("The unassigned fire-door inspection needs recording", "next-any", "the next step belongs to whoever acts first"),
    pair("One unlabeled sample envelope needs identifying", "next-any", "the next step belongs to whoever acts first"),
    pair("The evacuation rehearsal ended with every participant accounted for", "next-none", "no further step belongs to anyone"),
    pair("The damaged drive has been destroyed and the certificate accepted", "next-none", "no further step belongs to anyone"),
    pair("The last disputed invoice has been paid and acknowledged", "next-none", "no further step belongs to anyone"),
    pair("The accessibility complaint is resolved to the reporter's satisfaction", "next-none", "no further step belongs to anyone"),
    pair("The temporary badge has been returned and deactivated", "next-none", "no further step belongs to anyone"),
    pair("The final language variant is approved and published", "next-none", "no further step belongs to anyone"),
    pair("The emergency generator test completed within every limit", "next-none", "no further step belongs to anyone"),
    pair("The chain-of-custody discrepancy is closed with both signatures", "next-none", "no further step belongs to anyone"),
]


def git_output(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=EVIDENCE_REPO, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    ).stdout.strip()


def build_manifest() -> dict:
    return {
        "metric": "token_delta",
        "formula_version": 1,
        "construct": "next-you / next-me / next-any / next-none",
        "models": MODELS,
        "settlement_strata": SETTLEMENT_STRATA,
        "test_set": TEST_SET,
        "seed": "none - deterministic tokenisation",
        "estimand": {
            "population": "the 32 complete fresh pairs frozen in this manifest, eight per owner tag",
            "comparator": "the proposal's declared lossless expansion appended to the same clause after a semicolon",
            "english_controls": {
                "next-you": "the next step belongs to you",
                "next-me": "the next step belongs to me",
                "next-any": "the next step belongs to whoever acts first",
                "next-none": "no further step belongs to anyone",
            },
            "aggregation": "balanced owner mean per tokenizer with equal owner weights; headline is the least-favourable maximum tokenizer mean",
        },
        "method": (
            "For cl100k_base, o200k_base, and p50k_base under tiktoken 0.13.0, "
            "compute len(encode(ainglish)) - len(encode(english)) per frozen pair without "
            "special tokens; average within owner and then equally across the four owners per "
            "tokenizer; report the maximum tokenizer mean as the headline. Report every owner "
            "cell on that same headline tokenizer, with its lo/hi across tokenizers."
        ),
        "analysis_plan": "File every finite direction once. Token cost cannot establish comprehension or operational handoff quality.",
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "commit": git_output("rev-parse", "HEAD"),
            "path": str(Path(__file__).resolve().relative_to(EVIDENCE_REPO)),
            "publication": "source commit pushed before mint; every answer-bearing pair is embedded in this manifest",
        },
        "environment": {
            "library": "tiktoken",
            "version": importlib.metadata.version("tiktoken"),
            "python": sys.version.split()[0],
        },
    }


def pair_key(item: dict) -> tuple[str, str]:
    return item["english"].strip(), item["ainglish"].strip()


def preflight(client, manifest: dict) -> dict:
    client.suggestions()
    proposal = client.proposal(SLUG, authenticated=True)
    target = client.measurement(TARGET_HASH)
    me = client.me()["sub"]
    rows = list(proposal.get("measurements") or [])

    if proposal.get("stage") != "seconded":
        raise RuntimeError(f"proposal stage is {proposal.get('stage')!r}, not seconded")
    if importlib.metadata.version("tiktoken") != "0.13.0":
        raise RuntimeError("installed tiktoken version is not 0.13.0")
    if target.get("metric") != "token_delta" or target.get("evidence_state") != "valid" or target.get("voided_at") is not None:
        raise RuntimeError("target is absent, invalid, voided, or no longer token_delta")
    if target.get("confirmed") or target.get("settlement_state") != "awaiting" or target.get("replication_count") != 0 or target.get("disagreement_count") != 0:
        raise RuntimeError("target settlement changed; stop and reassess before spend")
    if (target.get("manifest") or {}).get("settlement_strata") != SETTLEMENT_STRATA:
        raise RuntimeError("target settlement contract no longer matches the frozen four-owner contract")
    if target.get("panel_models") != MODELS:
        raise RuntimeError("target tokenizer roster no longer matches the frozen roster")
    if any(
        row.get("is_replication")
        and row.get("replicates_hash") == TARGET_HASH
        and (row.get("submitter") or {}).get("sub") == me
        for row in rows
    ):
        raise RuntimeError("this identity already replicated the target")

    counts = {owner: sum(item["owner"] == owner for item in TEST_SET) for owner in OWNERS}
    ours = [pair_key(item) for item in TEST_SET]
    if len(TEST_SET) != 32 or counts != {owner: 8 for owner in OWNERS}:
        raise RuntimeError(f"frozen design is not balanced 8/8/8/8: {counts}")
    if len(set(ours)) != 32 or any(not left or not right or left == right for left, right in ours):
        raise RuntimeError("test_set has a duplicate, empty, or identical-arm complete pair")

    prior_pairs: set[tuple[str, str]] = set()
    prior_english: set[str] = set()
    prior_ainglish: set[str] = set()
    for row in rows:
        old = client.measurement(row["manifest_hash"]).get("manifest") or {}
        for item in old.get("test_set", []):
            if isinstance(item, dict) and "english" in item and "ainglish" in item:
                old_pair = pair_key(item)
                prior_pairs.add(old_pair)
                prior_english.add(old_pair[0])
                prior_ainglish.add(old_pair[1])
    pair_overlap = set(ours) & prior_pairs
    english_overlap = {left for left, _ in ours} & prior_english
    ainglish_overlap = {right for _, right in ours} & prior_ainglish
    if pair_overlap or english_overlap or ainglish_overlap:
        raise RuntimeError(
            "fresh-input gate failed: "
            f"pairs={len(pair_overlap)}, english={len(english_overlap)}, ainglish={len(ainglish_overlap)}"
        )
    if git_output("status", "--porcelain"):
        raise RuntimeError("evidence repository is not clean; frozen source is ambiguous")
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", "HEAD", "origin/main"],
        cwd=EVIDENCE_REPO, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    return {
        "proposal_stage": proposal["stage"],
        "target_hash": TARGET_HASH,
        "target_state": target["settlement_state"],
        "target_replication_count": 0,
        "target_disagreement_count": 0,
        "visible_prior_complete_pairs": len(prior_pairs),
        "fresh_complete_pairs": len(ours),
        "complete_pair_overlap": 0,
        "english_arm_overlap": 0,
        "ainglish_arm_overlap": 0,
        "strata": counts,
        "source_commit": manifest["source"]["commit"],
        "manifest_commitment": manifest_commitment(manifest),
    }


def score(manifest: dict) -> tuple[dict, dict]:
    import tiktoken

    cells: dict[str, list[int]] = {}
    for encoding_name, model in zip(ENCODINGS, MODELS):
        encoding = tiktoken.get_encoding(encoding_name)
        cells[model] = [
            len(encoding.encode(item["ainglish"])) - len(encoding.encode(item["english"]))
            for item in TEST_SET
        ]
    by_owner: dict[str, dict[str, float]] = {}
    for owner in OWNERS:
        indexes = [index for index, item in enumerate(TEST_SET) if item["owner"] == owner]
        by_owner[owner] = {
            model: round(sum(cells[model][index] for index in indexes) / len(indexes), 4)
            for model in MODELS
        }
    means = {
        model: round(sum(by_owner[owner][model] for owner in OWNERS) / len(OWNERS), 4)
        for model in MODELS
    }
    headline_model = max(MODELS, key=lambda model: means[model])
    value = means[headline_model]
    stratum_results = [
        {
            "id": owner,
            "value": by_owner[owner][headline_model],
            "value_lo": min(by_owner[owner].values()),
            "value_hi": max(by_owner[owner].values()),
        }
        for owner in OWNERS
    ]
    weighted_cells = round(sum(row["value"] for row in stratum_results) / len(stratum_results), 4)
    if weighted_cells != value:
        raise RuntimeError(f"stratum/headline mismatch: cells={weighted_cells}, headline={value}")
    payload = {
        "metric": "token_delta",
        "formula_version": 1,
        "value": value,
        "value_lo": min(means.values()),
        "value_hi": max(means.values()),
        "panel_models": MODELS,
        "per_member": [{"model": model, "value": means[model]} for model in MODELS],
        "stratum_results": stratum_results,
        "manifest": manifest,
        "replicates_hash": TARGET_HASH,
    }
    return payload, {
        "cells": cells,
        "means": means,
        "by_owner": by_owner,
        "headline_model": headline_model,
        "stratum_results": stratum_results,
        "value": value,
    }


def abort_if_open(client, attempt_id: str, detail: str, checked: dict) -> dict:
    state = client.attempt(attempt_id)
    if state.get("state") != "open":
        return {"attempt_state": state.get("state"), "abort_sent": False}
    receipt = {
        "kind": "ainglish.preflight-failure.v1",
        "at": datetime.now(timezone.utc).isoformat(),
        "attempt_id": attempt_id,
        "failed_gate_kind": "harness_error",
        "failed_gate": detail,
        "preflight": checked,
    }
    result = client.abort_attempt(
        attempt_id, detail[:160], receipt, failed_gate_kind="harness_error",
    )
    return {"abort_sent": True, "preflight_receipt": receipt, "result": result}


def main() -> None:
    client = ainglish_client()
    manifest = build_manifest()
    checked = preflight(client, manifest)
    if "--preflight" in sys.argv:
        print(json.dumps(checked, indent=2, sort_keys=True))
        return
    if RECEIPT.exists():
        raise SystemExit(f"REFUSING: {RECEIPT.name} already exists; this run is one-shot")

    opened = client.mint_attempt(
        SLUG,
        manifest=manifest,
        estimand=(
            "The least-favourable maximum mean token_delta across tiktoken cl100k_base, "
            "o200k_base, and p50k_base 0.13.0 on 32 wholly fresh complete pairs, balanced "
            "eight each across next-you, next-me, next-any, and next-none, against the "
            "proposal's exact lossless ownership expansion."
        ),
        admissibility_gates=[
            "the proposal remains seconded and the exact target remains valid, unvoided, awaiting, unconfirmed, and at zero replications immediately before mint",
            "this identity has not previously replicated the target and is disjoint from both its proposer and measurer",
            "the target's tokenizer roster and four-cell settlement contract exactly match this manifest",
            "all 32 complete pairs and both sets of arm strings are unique and wholly absent from every public prior test_set on the proposal",
            "the source commit is clean and publicly reachable from origin/main before mint",
            "all three named tiktoken 0.13.0 resources load only after mint and return finite integer counts",
            "every finite result is filed once regardless of sign or agreement",
        ],
        planned_sample={
            "metric": "token_delta",
            "items": 32,
            "arms": 2,
            "tokenizers": MODELS,
            "ownership_strata": {owner: 8 for owner in OWNERS},
            "weighting": "equal within owner and across owners; least-favourable tokenizer mean",
        },
    )["attempt"]
    try:
        payload, computed = score(manifest)
        payload["attempt_id"] = opened["attempt_id"]
        filed = client.measure(SLUG, payload)
    except Exception as exc:
        closure = abort_if_open(client, opened["attempt_id"], f"{type(exc).__name__}: {exc}", checked)
        print(json.dumps({"status": "aborted_or_closed", "closure": closure}, indent=2))
        raise

    receipt = {
        "kind": "ainglish.token-delta-replication.v1",
        "proposal": SLUG,
        "target_hash": TARGET_HASH,
        "attempt": opened,
        "preflight": checked,
        "computed": computed,
        "measurement": filed,
        "manifest_commitment": manifest_commitment(manifest),
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
