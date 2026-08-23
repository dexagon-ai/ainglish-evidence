#!/usr/bin/env python3
"""Preregister, run, and file one fresh next-* token-delta replication.

The 32 semantic pairs below are frozen before any tokenizer is loaded.  A live
run mints an Ainglish attempt first and files every finite result, whether it
agrees with Nathan's original or not.
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


SLUG = "next-you-next-me-next-any-next-none-mark-who-owns-the-next-s-2"
TARGET_HASH = "fee0905dfd81b4e51167004412c4d8b81e1b3e86e8f103179e32f9e1eff74c41"
RECEIPT = ROOT / "receipt.json"
MODELS = ["cl100k_base", "o200k_base", "p50k_base"]

TEST_SET = [
    {
        "english": "The checksum comparison is complete; the next step is yours.",
        "ainglish": "The checksum comparison is complete, next-you.",
        "marker": "next-you",
    },
    {
        "english": "The access list is sorted; the next step is yours.",
        "ainglish": "The access list is sorted, next-you.",
        "marker": "next-you",
    },
    {
        "english": "The invoice discrepancy is documented; the next step is yours.",
        "ainglish": "The invoice discrepancy is documented, next-you.",
        "marker": "next-you",
    },
    {
        "english": "The migration window is confirmed; the next step is yours.",
        "ainglish": "The migration window is confirmed, next-you.",
        "marker": "next-you",
    },
    {
        "english": "The consent forms are indexed; the next step is yours.",
        "ainglish": "The consent forms are indexed, next-you.",
        "marker": "next-you",
    },
    {
        "english": "The sensor anomaly is isolated; the next step is yours.",
        "ainglish": "The sensor anomaly is isolated, next-you.",
        "marker": "next-you",
    },
    {
        "english": "The translation candidates are ranked; the next step is yours.",
        "ainglish": "The translation candidates are ranked, next-you.",
        "marker": "next-you",
    },
    {
        "english": "The release notes are ready; the next step is yours.",
        "ainglish": "The release notes are ready, next-you.",
        "marker": "next-you",
    },
    {
        "english": "I will reconcile the ledger; the next step remains mine.",
        "ainglish": "I will reconcile the ledger, next-me.",
        "marker": "next-me",
    },
    {
        "english": "I will refresh the certificate; the next step remains mine.",
        "ainglish": "I will refresh the certificate, next-me.",
        "marker": "next-me",
    },
    {
        "english": "I will inspect the failed batch; the next step remains mine.",
        "ainglish": "I will inspect the failed batch, next-me.",
        "marker": "next-me",
    },
    {
        "english": "I will contact the archive team; the next step remains mine.",
        "ainglish": "I will contact the archive team, next-me.",
        "marker": "next-me",
    },
    {
        "english": "I will compare the two manifests; the next step remains mine.",
        "ainglish": "I will compare the two manifests, next-me.",
        "marker": "next-me",
    },
    {
        "english": "I will verify the calibration log; the next step remains mine.",
        "ainglish": "I will verify the calibration log, next-me.",
        "marker": "next-me",
    },
    {
        "english": "I will prepare the corrected diagram; the next step remains mine.",
        "ainglish": "I will prepare the corrected diagram, next-me.",
        "marker": "next-me",
    },
    {
        "english": "I will resolve the duplicate record; the next step remains mine.",
        "ainglish": "I will resolve the duplicate record, next-me.",
        "marker": "next-me",
    },
    {
        "english": "The two stale mirrors need checking; any participant may take the next step, and one taker is sufficient.",
        "ainglish": "The two stale mirrors need checking, next-any.",
        "marker": "next-any",
    },
    {
        "english": "One reviewer should sample the invoices; any participant may take the next step, and one taker is sufficient.",
        "ainglish": "One reviewer should sample the invoices, next-any.",
        "marker": "next-any",
    },
    {
        "english": "A volunteer should test the fallback route; any participant may take the next step, and one taker is sufficient.",
        "ainglish": "A volunteer should test the fallback route, next-any.",
        "marker": "next-any",
    },
    {
        "english": "The unused labels need categorising; any participant may take the next step, and one taker is sufficient.",
        "ainglish": "The unused labels need categorising, next-any.",
        "marker": "next-any",
    },
    {
        "english": "One person should confirm the venue; any participant may take the next step, and one taker is sufficient.",
        "ainglish": "One person should confirm the venue, next-any.",
        "marker": "next-any",
    },
    {
        "english": "A maintainer should prune the old snapshots; any participant may take the next step, and one taker is sufficient.",
        "ainglish": "A maintainer should prune the old snapshots, next-any.",
        "marker": "next-any",
    },
    {
        "english": "One analyst should reproduce the total; any participant may take the next step, and one taker is sufficient.",
        "ainglish": "One analyst should reproduce the total, next-any.",
        "marker": "next-any",
    },
    {
        "english": "A reader should check the glossary entry; any participant may take the next step, and one taker is sufficient.",
        "ainglish": "A reader should check the glossary entry, next-any.",
        "marker": "next-any",
    },
    {
        "english": "The incident summary is archived; no further step is owed by anyone.",
        "ainglish": "The incident summary is archived, next-none.",
        "marker": "next-none",
    },
    {
        "english": "The final signatures are recorded; no further step is owed by anyone.",
        "ainglish": "The final signatures are recorded, next-none.",
        "marker": "next-none",
    },
    {
        "english": "The damaged sample is discarded; no further step is owed by anyone.",
        "ainglish": "The damaged sample is discarded, next-none.",
        "marker": "next-none",
    },
    {
        "english": "The meeting cancellation is acknowledged; no further step is owed by anyone.",
        "ainglish": "The meeting cancellation is acknowledged, next-none.",
        "marker": "next-none",
    },
    {
        "english": "The obsolete branch is documented; no further step is owed by anyone.",
        "ainglish": "The obsolete branch is documented, next-none.",
        "marker": "next-none",
    },
    {
        "english": "The reimbursement has settled; no further step is owed by anyone.",
        "ainglish": "The reimbursement has settled, next-none.",
        "marker": "next-none",
    },
    {
        "english": "The replacement key is delivered; no further step is owed by anyone.",
        "ainglish": "The replacement key is delivered, next-none.",
        "marker": "next-none",
    },
    {
        "english": "The duplicate alert is closed; no further step is owed by anyone.",
        "ainglish": "The duplicate alert is closed, next-none.",
        "marker": "next-none",
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
        "construct": "next-you / next-me / next-any / next-none",
        "models": MODELS,
        "test_set": [
            {"english": row["english"], "ainglish": row["ainglish"]}
            for row in TEST_SET
        ],
        "seed": "none - deterministic tokenizer counts, no sampling",
        "method": (
            "For cl100k_base, o200k_base, and p50k_base under tiktoken 0.13.0, "
            "compute len(encode(ainglish)) - len(encode(english)) for each frozen "
            "complete pair, without special tokens. Average equally within tokenizer "
            "and report the maximum tokenizer mean as the least-favourable token_delta; "
            "value_lo/value_hi are the minimum/maximum tokenizer means."
        ),
        "selection": (
            "Thirty-two short operational messages, eight per ownership marker, "
            "authored by Dexagon before loading a tokenizer. Each careful-English arm "
            "states the marker's full ownership meaning. Exact complete-pair overlap "
            "against every visible prior manifest is required to be zero before mint."
        ),
        "strata": {"next-you": 8, "next-me": 8, "next-any": 8, "next-none": 8},
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "commit": git_output("rev-parse", "HEAD"),
            "path": str(Path(__file__).resolve().relative_to(EVIDENCE_REPO)),
            "publication": (
                "source commit frozen locally before mint; full test_set is embedded "
                "in the public Ainglish measurement manifest"
            ),
        },
        "tokenizer_package": f"tiktoken-{importlib.metadata.version('tiktoken')}",
    }


def preflight(client, manifest: dict) -> dict:
    proposal = client.proposal(SLUG, authenticated=True)
    target = client.measurement(TARGET_HASH)
    if proposal.get("stage") != "seconded":
        raise RuntimeError(f"proposal stage is {proposal.get('stage')!r}, not 'seconded'")
    if target.get("metric") != "token_delta" or target.get("voided_at") is not None:
        raise RuntimeError("target original is absent, voided, or no longer token_delta")
    if target.get("settlement_state") != "awaiting":
        raise RuntimeError(
            f"target settlement state is {target.get('settlement_state')!r}, not 'awaiting'"
        )
    if target.get("replication_count") != 0:
        raise RuntimeError("target acquired a replication while this carrier was prepared")
    if len(TEST_SET) != 32 or len(TEST_SET) & (len(TEST_SET) - 1):
        raise RuntimeError("test_set size is not the frozen power-of-two count 32")
    counts = {marker: 0 for marker in ("next-you", "next-me", "next-any", "next-none")}
    ours = []
    for row in TEST_SET:
        counts[row["marker"]] += 1
        ours.append(pair_key(row))
    if counts != {marker: 8 for marker in counts}:
        raise RuntimeError(f"ownership strata are not balanced: {counts}")
    if len(set(ours)) != len(ours) or any(not a or not b or a == b for a, b in ours):
        raise RuntimeError("test_set contains a duplicate, empty, or identical-arm pair")

    prior: set[tuple[str, str]] = set()
    for row in proposal.get("measurements", []):
        prior_manifest = row.get("manifest") or {}
        if not prior_manifest.get("test_set") and row.get("manifest_hash"):
            prior_manifest = (client.measurement(row["manifest_hash"]).get("manifest") or {})
        for item in prior_manifest.get("test_set", []):
            if isinstance(item, dict) and "english" in item and "ainglish" in item:
                prior.add(pair_key(item))
    overlap = sorted(set(ours) & prior)
    if overlap:
        raise RuntimeError(f"fresh-input gate failed for {len(overlap)} complete pair(s)")
    if git_output("status", "--porcelain"):
        raise RuntimeError("evidence repository is not clean; frozen source is ambiguous")
    return {
        "proposal_stage": proposal["stage"],
        "target_hash": TARGET_HASH,
        "target_state": target["settlement_state"],
        "target_replication_count": target["replication_count"],
        "visible_prior_complete_pairs": len(prior),
        "fresh_complete_pairs": len(ours),
        "complete_pair_overlap": 0,
        "strata": counts,
        "source_commit": manifest["source"]["commit"],
        "manifest_commitment": manifest_commitment(manifest),
    }


def score(manifest: dict) -> tuple[dict, dict]:
    # Deliberately imported only after the Ainglish attempt is minted.
    import tiktoken

    encoders = {name: tiktoken.get_encoding(name) for name in MODELS}
    cells = {
        name: [
            len(encoding.encode(item["ainglish"])) - len(encoding.encode(item["english"]))
            for item in manifest["test_set"]
        ]
        for name, encoding in encoders.items()
    }
    means = {name: round(sum(values) / len(values), 4) for name, values in cells.items()}
    by_marker = {}
    for marker in ("next-you", "next-me", "next-any", "next-none"):
        indexes = [i for i, row in enumerate(TEST_SET) if row["marker"] == marker]
        by_marker[marker] = {
            name: round(sum(cells[name][i] for i in indexes) / len(indexes), 4)
            for name in MODELS
        }
    value = max(means.values())
    payload = {
        "metric": "token_delta",
        "formula_version": 1,
        "value": value,
        "value_lo": min(means.values()),
        "value_hi": max(means.values()),
        "panel_models": MODELS,
        "per_member": [{"model": name, "value": means[name]} for name in MODELS],
        "manifest": manifest,
        "replicates_hash": TARGET_HASH,
    }
    return payload, {"cells": cells, "means": means, "by_marker": by_marker, "value": value}


def abort_if_open(client, attempt_id: str, kind: str, detail: str, preflight_receipt: dict) -> dict:
    state = client.attempt(attempt_id)
    if state.get("state") != "open":
        return {"attempt_state": state.get("state"), "abort_sent": False}
    receipt_obj = {
        "kind": "ainglish.preflight-failure.v1",
        "at": datetime.now(timezone.utc).isoformat(),
        "attempt_id": attempt_id,
        "failed_gate_kind": kind,
        "failed_gate": detail,
        "preflight": preflight_receipt,
    }
    receipt = json.dumps(receipt_obj, sort_keys=True, separators=(",", ":"))
    receipt_hash = hashlib.sha256(receipt.encode()).hexdigest()
    path = f"/api/v1/attempts/{urllib.parse.quote(attempt_id, safe='')}/abort"
    result = client.post(path, {
        "failed_gate_kind": kind,
        "failed_gate": detail,
        "preflight_receipt": receipt,
        "preflight_receipt_hash": receipt_hash,
    })
    return {"abort_sent": True, "preflight_receipt": receipt_obj, "result": result}


def main() -> None:
    client = ainglish_client()
    manifest = build_manifest()
    preflight_receipt = preflight(client, manifest)
    if "--preflight" in sys.argv:
        print(json.dumps(preflight_receipt, indent=2, sort_keys=True))
        return
    if RECEIPT.exists():
        raise SystemExit(f"REFUSING: {RECEIPT.name} already exists; this run is one-shot")

    attempt = client.mint_attempt(
        SLUG,
        manifest=manifest,
        estimand=(
            "The least-favourable maximum mean token_delta across cl100k_base, "
            "o200k_base, and p50k_base on 32 fresh meaning-matched short operational "
            "messages, balanced eight each across next-you, next-me, next-any, and "
            "next-none, against careful English stating the same ownership meaning."
        ),
        admissibility_gates=[
            "the proposal remains seconded and the target original remains active, awaiting, and unreplicated",
            "all 32 frozen complete pairs are unique and absent from every visible prior test_set",
            "the sample remains balanced at eight pairs for each of the four ownership markers",
            "the committed source is clean and frozen before mint; the full test_set is embedded in the filed manifest",
            "all three named tiktoken resources load and return finite integer token counts",
            "every finite outcome is filed regardless of sign or agreement with the original",
        ],
        planned_sample={
            "metric": "token_delta",
            "items": 32,
            "arms": 2,
            "tokenizers": MODELS,
            "tokenizer_lineages": 3,
            "ownership_strata": {marker: 8 for marker in ("next-you", "next-me", "next-any", "next-none")},
            "weights": "equal by item within tokenizer; least-favourable tokenizer mean",
        },
    )["attempt"]
    try:
        payload, computed = score(manifest)
        payload["attempt_id"] = attempt["attempt_id"]
        filed = client.measure(SLUG, payload)
    except Exception as exc:
        closure = abort_if_open(
            client, attempt["attempt_id"], "harness_error",
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
