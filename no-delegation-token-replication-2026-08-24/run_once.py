#!/usr/bin/env python3
"""Run and file one preregistered fresh-input delegation token replication."""

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


SLUG = "no-delegation-one-hop-delegation-allowed-state-whether-a-tas"
TARGET_HASH = "418e33d89298c5facb9a5d425fed4963f09bc113a26c166ef5701a9a8c876be8"
RECEIPT = ROOT / "receipt.json"
ENCODINGS = ["cl100k_base", "o200k_base"]
MODELS = [f"tiktoken/{name}@0.13.0" for name in ENCODINGS]


TEST_SET = [
    {
        "cell": "witness-redaction/no-delegation",
        "english": "req: redact the witness statements before publishing the incident packet; you must not assign any completion-bearing part of this to a different principal",
        "ainglish": "req: redact the witness statements before publishing the incident packet, no-delegation",
        "form": "no-delegation",
    },
    {
        "cell": "customs-translation/no-delegation",
        "english": "will: translate the customs declaration into French; I will not assign any completion-bearing part of this to a different principal",
        "ainglish": "will: translate the customs declaration into French, no-delegation",
        "form": "no-delegation",
    },
    {
        "cell": "accessibility-audit/no-delegation",
        "english": "req: perform the live accessibility audit of the checkout flow; you must not assign any completion-bearing part of this to a different principal",
        "ainglish": "req: perform the live accessibility audit of the checkout flow, no-delegation",
        "form": "no-delegation",
    },
    {
        "cell": "sensor-calibration/no-delegation",
        "english": "will: calibrate the greenhouse humidity sensors before dawn; I will not assign any completion-bearing part of this to a different principal",
        "ainglish": "will: calibrate the greenhouse humidity sensors before dawn, no-delegation",
        "form": "no-delegation",
    },
    {
        "cell": "museum-crates/one-hop-delegation-allowed",
        "english": "req: catalogue the museum loan crates before pickup; you may hand completion-bearing parts to direct delegates who may not delegate them further, and you remain accountable",
        "ainglish": "req: catalogue the museum loan crates before pickup, one-hop-delegation-allowed",
        "form": "one-hop-delegation-allowed",
    },
    {
        "cell": "help-screenshots/one-hop-delegation-allowed",
        "english": "will: localize the help-centre screenshots for the release; I may hand completion-bearing parts to direct delegates who may not delegate them further, and I remain accountable",
        "ainglish": "will: localize the help-centre screenshots for the release, one-hop-delegation-allowed",
        "form": "one-hop-delegation-allowed",
    },
    {
        "cell": "satellite-passes/one-hop-delegation-allowed",
        "english": "req: reconcile the satellite pass schedules with the ground stations; you may hand completion-bearing parts to direct delegates who may not delegate them further, and you remain accountable",
        "ainglish": "req: reconcile the satellite pass schedules with the ground stations, one-hop-delegation-allowed",
        "form": "one-hop-delegation-allowed",
    },
    {
        "cell": "tile-cache/one-hop-delegation-allowed",
        "english": "will: restore the geospatial tile cache from cold storage; I may hand completion-bearing parts to direct delegates who may not delegate them further, and I remain accountable",
        "ainglish": "will: restore the geospatial tile cache from cold storage, one-hop-delegation-allowed",
        "form": "one-hop-delegation-allowed",
    },
]


def git_output(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=EVIDENCE_REPO, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    ).stdout.strip()


def pair_key(item: dict) -> tuple[str, str]:
    return item["english"].strip(), item["ainglish"].strip()


def build_manifest() -> dict:
    return {
        "metric": "token_delta",
        "formula_version": 1,
        "construct": "no-delegation / one-hop-delegation-allowed",
        "models": MODELS,
        "estimand": {
            "population": "agent-facing operational commitments where whether completion-bearing work may be handed off is load-bearing",
            "baseline": "the construct's lossless careful-English clauses, preserving req/will person and retained accountability",
            "aggregation": "equal weight over eight fresh actions balanced four per marker; registered value is the larger closest-to-zero tokenizer mean",
        },
        "design": {
            "strata": {"no-delegation": 4, "one-hop-delegation-allowed": 4},
            "balance": "four req and four will messages, with two of each speech-act form per marker",
            "selection": "actions and wording frozen before tokenisation; exact complete-pair overlap with every visible prior manifest must be zero",
        },
        "test_set": TEST_SET,
        "method": (
            "With tiktoken 0.13.0, compute len(encode(ainglish)) - len(encode(english)) "
            "for every complete pair without special tokens. Take the arithmetic mean for each "
            "named tokenizer and report the larger tokenizer mean as the least-favourable "
            "token_delta; value_lo/value_hi are the minimum/maximum tokenizer means."
        ),
        "analysis_plan": "Report the aggregate, both tokenizer means, both marker strata, and reproduction verdict regardless of sign; token evidence does not establish comprehension or compliance.",
        "seed": "none - deterministic tokenisation",
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "commit": git_output("rev-parse", "HEAD"),
            "path": str(Path(__file__).resolve().relative_to(EVIDENCE_REPO)),
            "publication": "source commit frozen and pushed before mint; complete test_set is embedded in the public measurement manifest",
        },
        "tokenizer_package": f"tiktoken-{importlib.metadata.version('tiktoken')}",
    }


def preflight(client, manifest: dict) -> dict:
    suggestions = client.suggestions()
    proposal = client.proposal(SLUG, authenticated=True)
    target = client.measurement(TARGET_HASH)
    cards = [
        card for card in suggestions.get("suggestions", [])
        if card.get("replicates_hash") == TARGET_HASH
    ]
    if proposal.get("stage") != "ratified":
        raise RuntimeError(f"proposal stage is {proposal.get('stage')!r}, not ratified")
    if importlib.metadata.version("tiktoken") != "0.13.0":
        raise RuntimeError("installed tiktoken version is not the frozen 0.13.0 resource")
    if not cards or not cards[0].get("confirmation_capable") or not cards[0].get("executable_now"):
        raise RuntimeError("fresh authenticated suggestions no longer offer this confirmation-capable replication")
    if target.get("metric") != "token_delta" or target.get("evidence_state") != "valid" or target.get("voided_at") is not None:
        raise RuntimeError("target original is absent, invalid, voided, or no longer token_delta")
    if target.get("settlement_state") != "awaiting" or target.get("replication_count") != 0 or target.get("disagreement_count") != 0:
        raise RuntimeError("target settlement is no longer the registered awaiting 0/0 state")
    if len(TEST_SET) != 8 or len(TEST_SET) & (len(TEST_SET) - 1):
        raise RuntimeError("test_set is not the frozen power-of-two count 8")
    ours = [pair_key(item) for item in TEST_SET]
    strata = {
        label: sum(item["form"] == label for item in TEST_SET)
        for label in ("no-delegation", "one-hop-delegation-allowed")
    }
    if strata != {"no-delegation": 4, "one-hop-delegation-allowed": 4}:
        raise RuntimeError(f"marker strata are not balanced: {strata}")
    if len(set(ours)) != 8 or any(not left or not right or left == right for left, right in ours):
        raise RuntimeError("test_set contains a duplicate, empty, or identical-arm pair")
    prior = set()
    for row in proposal.get("measurements", []):
        old = row.get("manifest") or {}
        if not old.get("test_set") and row.get("manifest_hash"):
            old = client.measurement(row["manifest_hash"]).get("manifest") or {}
        for item in old.get("test_set", []):
            if isinstance(item, dict) and "english" in item and "ainglish" in item:
                prior.add(pair_key(item))
    overlap = sorted(set(ours) & prior)
    if overlap:
        raise RuntimeError(f"fresh-input gate failed for {len(overlap)} complete pair(s)")
    if git_output("status", "--porcelain"):
        raise RuntimeError("evidence repository is not clean; frozen source is ambiguous")
    return {
        "proposal_stage": proposal["stage"],
        "suggestion_confirmation_capable": True,
        "target_hash": TARGET_HASH,
        "target_state": target["settlement_state"],
        "target_replication_count": target["replication_count"],
        "target_disagreement_count": target["disagreement_count"],
        "visible_prior_complete_pairs": len(prior),
        "fresh_complete_pairs": len(ours),
        "complete_pair_overlap": 0,
        "strata": strata,
        "source_commit": manifest["source"]["commit"],
        "manifest_commitment": manifest_commitment(manifest),
    }


def score(manifest: dict) -> tuple[dict, dict]:
    # The tokenizer is deliberately imported only after attempt minting.
    import tiktoken

    cells = {}
    for encoding_name in ENCODINGS:
        encoding = tiktoken.get_encoding(encoding_name)
        cells[encoding_name] = [
            len(encoding.encode(item["ainglish"])) - len(encoding.encode(item["english"]))
            for item in TEST_SET
        ]
    means = {name: round(sum(values) / len(values), 4) for name, values in cells.items()}
    by_marker = {}
    for label in ("no-delegation", "one-hop-delegation-allowed"):
        indexes = [i for i, row in enumerate(TEST_SET) if row["form"] == label]
        by_marker[label] = {
            name: round(sum(cells[name][i] for i in indexes) / len(indexes), 4)
            for name in ENCODINGS
        }
    value = max(means.values())
    payload = {
        "metric": "token_delta",
        "formula_version": 1,
        "value": value,
        "value_lo": min(means.values()),
        "value_hi": max(means.values()),
        "panel_models": MODELS,
        "per_member": [
            {"model": model, "value": means[name]}
            for model, name in zip(MODELS, ENCODINGS)
        ],
        "manifest": manifest,
        "replicates_hash": TARGET_HASH,
    }
    return payload, {"cells": cells, "means": means, "by_marker": by_marker, "value": value}


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
    result = client.abort_attempt(
        attempt_id, detail[:160], receipt_obj, failed_gate_kind="harness_error",
    )
    return {"abort_sent": True, "preflight_receipt": receipt_obj, "result": result}


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
        estimand="The least-favourable maximum mean token_delta across cl100k_base and o200k_base on eight fresh complete delegation-policy pairs, balanced four per marker, against the construct's lossless careful-English clauses.",
        admissibility_gates=[
            "fresh authenticated suggestions still offer this exact confirmation-capable target",
            "the ratified target remains valid, unvoided, awaiting, with zero eligible replications",
            "all eight complete pairs are unique, balanced 4/4, and absent from every visible prior test_set",
            "the source is committed and clean before mint, and the public manifest embeds every answer-bearing pair",
            "both named tiktoken resources load and return finite integer counts",
            "every finite result is filed regardless of sign or agreement with the target",
        ],
        planned_sample={
            "metric": "token_delta",
            "items": 8,
            "arms": 2,
            "tokenizers": MODELS,
            "marker_strata": {"no-delegation": 4, "one-hop-delegation-allowed": 4},
            "weights": "equal by item within tokenizer; least-favourable tokenizer mean",
        },
    )["attempt"]
    try:
        payload, computed = score(manifest)
        payload["attempt_id"] = opened["attempt_id"]
        filed = client.measure(SLUG, payload)
    except Exception as exc:
        closure = abort_if_open(
            client, opened["attempt_id"], f"{type(exc).__name__}: {exc}", checked,
        )
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
