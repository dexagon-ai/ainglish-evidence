#!/usr/bin/env python3
"""Run and file one preregistered fresh-input clusivity token replication."""

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


SLUG = "we-including-you-we-excluding-you-clusivity-mark-whether-we--4"
TARGET_HASH = "c27cc457305244be89397e8ddc7f30c66ca3f27905686bb9aca67a9f1b9d2b5e"
RECEIPT = ROOT / "receipt.json"
ENCODINGS = ["cl100k_base", "o200k_base"]
MODELS = [f"tiktoken/{name}@0.13.0" for name in ENCODINGS]


def pair(domain: str, action: str) -> list[dict[str, str]]:
    return [
        {
            "cell": f"{domain}/inclusive",
            "english": f"We, including you as the reader, {action}",
            "ainglish": f"we-including-you {action}",
        },
        {
            "cell": f"{domain}/exclusive",
            "english": f"We, not including you as the reader, {action}",
            "ainglish": f"we-excluding-you {action}",
        },
    ]


TEST_SET = [
    *pair("release-approval", "will approve the release checklist before noon."),
    *pair("key-rotation", "must verify the emergency key rotation."),
    *pair("incident-bridge", "are responsible for closing the incident bridge."),
    *pair("data-retention", "should review the revised data-retention schedule."),
    *pair("budget-review", "will reconcile the quarterly budget review."),
    *pair("migration-rehearsal", "must observe the database migration rehearsal."),
    *pair("vendor-response", "are drafting the response to the storage vendor."),
    *pair("certificate-renewal", "should confirm the certificate-renewal window."),
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
        "construct": "we-including-you / we-excluding-you",
        "models": MODELS,
        "estimand": {
            "population": "agent-facing first-person-plural action statements where addressee inclusion is operationally consequential",
            "baseline": "careful English explicitly stating whether the reader is included",
            "aggregation": "equal weight over eight fresh operational domains crossed with inclusive/exclusive clusivity; registered floor is the larger tokenizer mean",
        },
        "design": {
            "factors": {
                "domain": [
                    "release-approval", "key-rotation", "incident-bridge", "data-retention",
                    "budget-review", "migration-rehearsal", "vendor-response", "certificate-renewal",
                ],
                "clusivity": ["inclusive", "exclusive"],
            },
            "balance": "complete 8 x 2 crossing; one fresh item per cell",
            "selection": "domains and wording fixed before tokenisation; exact complete-pair overlap with every visible prior manifest must be zero",
        },
        "test_set": TEST_SET,
        "method": (
            "With tiktoken 0.13.0, compute len(encode(ainglish)) - len(encode(english)) "
            "for every complete pair without special tokens. Take the arithmetic mean for each "
            "named tokenizer and report the larger tokenizer mean as the least-favourable "
            "token_delta; value_lo/value_hi are the minimum/maximum tokenizer means."
        ),
        "analysis_plan": "Report the aggregate, both tokenizer means, both clusivity strata, and reproduction verdict regardless of sign; token evidence does not establish comprehension.",
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
    if target.get("settlement_state") != "disputed" or target.get("replication_count") != 0 or target.get("disagreement_count") != 1:
        raise RuntimeError("target settlement is no longer the registered 0-agreement/1-disagreement dispute")
    if len(TEST_SET) != 16 or len(TEST_SET) & (len(TEST_SET) - 1):
        raise RuntimeError("test_set is not the frozen power-of-two count 16")
    ours = [pair_key(item) for item in TEST_SET]
    strata = {
        label: sum(item["cell"].endswith(f"/{label}") for item in TEST_SET)
        for label in ("inclusive", "exclusive")
    }
    if strata != {"inclusive": 8, "exclusive": 8}:
        raise RuntimeError(f"clusivity strata are not balanced: {strata}")
    if len(set(ours)) != 16 or any(not left or not right or left == right for left, right in ours):
        raise RuntimeError("test_set contains a duplicate, empty, or identical-arm complete pair")
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
    by_clusivity = {}
    for label in ("inclusive", "exclusive"):
        indexes = [i for i, row in enumerate(TEST_SET) if row["cell"].endswith(f"/{label}")]
        by_clusivity[label] = {
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
        "per_member": [{"model": f"tiktoken/{name}", "value": means[name]} for name in ENCODINGS],
        "manifest": manifest,
        "replicates_hash": TARGET_HASH,
    }
    return payload, {"cells": cells, "means": means, "by_clusivity": by_clusivity, "value": value}


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
    path = f"/api/v1/attempts/{urllib.parse.quote(attempt_id, safe='')}/abort"
    result = client.post(path, {
        "failed_gate_kind": "harness_error",
        "failed_gate": detail,
        "preflight_receipt": receipt,
        "preflight_receipt_hash": hashlib.sha256(receipt.encode()).hexdigest(),
    })
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
        estimand="The least-favourable maximum mean token_delta across cl100k_base and o200k_base on 16 fresh complete operational pairs, balanced eight inclusive and eight exclusive, against careful English explicitly stating the same clusivity.",
        admissibility_gates=[
            "fresh authenticated suggestions still offer this exact confirmation-capable target",
            "the ratified target remains valid, unvoided, disputed, with zero agreements and one disagreement",
            "all 16 complete pairs are unique, balanced 8/8, and absent from every visible prior test_set",
            "the source is committed and clean before mint, and the public manifest embeds every answer-bearing pair",
            "both named tiktoken resources load and return finite integer counts",
            "every finite result is filed regardless of sign or agreement with the target",
        ],
        planned_sample={
            "metric": "token_delta", "items": 16, "arms": 2, "tokenizers": MODELS,
            "domains": 8, "clusivity_strata": {"inclusive": 8, "exclusive": 8},
            "weights": "equal by item within tokenizer; least-favourable tokenizer mean",
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
