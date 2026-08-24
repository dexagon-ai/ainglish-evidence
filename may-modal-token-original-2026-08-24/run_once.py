#!/usr/bin/env python3
"""Mint, run, and file the frozen may-as-* token-delta prerequisite once."""

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


SLUG = "may-as-permission-may-as-possibility-does-may-authorize-an-a"
TOKENIZERS = ["cl100k_base", "o200k_base"]
TEST_SET = [
    {
        "force": "permission",
        "ainglish": "The export worker may-as-permission transmit customer data.",
        "english": "The export worker is permitted to transmit customer data.",
        "allowed_to": "The export worker is allowed-to transmit customer data.",
    },
    {
        "force": "permission",
        "ainglish": "The release bot may-as-permission publish the signed package.",
        "english": "The release bot is permitted to publish the signed package.",
        "allowed_to": "The release bot is allowed-to publish the signed package.",
    },
    {
        "force": "permission",
        "ainglish": "The auditor may-as-permission inspect the sealed logs.",
        "english": "The auditor is permitted to inspect the sealed logs.",
        "allowed_to": "The auditor is allowed-to inspect the sealed logs.",
    },
    {
        "force": "permission",
        "ainglish": "The backup service may-as-permission read the archive.",
        "english": "The backup service is permitted to read the archive.",
        "allowed_to": "The backup service is allowed-to read the archive.",
    },
    {
        "force": "permission",
        "ainglish": "The contractor may-as-permission rotate the staging keys.",
        "english": "The contractor is permitted to rotate the staging keys.",
        "allowed_to": "The contractor is allowed-to rotate the staging keys.",
    },
    {
        "force": "permission",
        "ainglish": "The router may-as-permission forward emergency traffic.",
        "english": "The router is permitted to forward emergency traffic.",
        "allowed_to": "The router is allowed-to forward emergency traffic.",
    },
    {
        "force": "permission",
        "ainglish": "The maintainer may-as-permission restart the payment queue.",
        "english": "The maintainer is permitted to restart the payment queue.",
        "allowed_to": "The maintainer is allowed-to restart the payment queue.",
    },
    {
        "force": "permission",
        "ainglish": "The reviewer may-as-permission disclose the incident summary.",
        "english": "The reviewer is permitted to disclose the incident summary.",
        "allowed_to": "The reviewer is allowed-to disclose the incident summary.",
    },
    {
        "force": "possibility",
        "ainglish": "The export worker may-as-possibility transmit customer data.",
        "english": "The export worker might transmit customer data.",
    },
    {
        "force": "possibility",
        "ainglish": "A checksum collision may-as-possibility corrupt the archive.",
        "english": "A checksum collision might corrupt the archive.",
    },
    {
        "force": "possibility",
        "ainglish": "The cooling pump may-as-possibility fail during restart.",
        "english": "The cooling pump might fail during restart.",
    },
    {
        "force": "possibility",
        "ainglish": "The delayed webhook may-as-possibility arrive after the timeout.",
        "english": "The delayed webhook might arrive after the timeout.",
    },
    {
        "force": "possibility",
        "ainglish": "The revoked credential may-as-possibility authenticate through a stale replica.",
        "english": "The revoked credential might authenticate through a stale replica.",
    },
    {
        "force": "possibility",
        "ainglish": "The invoice total may-as-possibility change after the currency refresh.",
        "english": "The invoice total might change after the currency refresh.",
    },
    {
        "force": "possibility",
        "ainglish": "The storage shard may-as-possibility recover without replay.",
        "english": "The storage shard might recover without replay.",
    },
    {
        "force": "possibility",
        "ainglish": "The sensor drift may-as-possibility trigger an emergency shutdown.",
        "english": "The sensor drift might trigger an emergency shutdown.",
    },
]


def git_output(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=EVIDENCE_REPO, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    ).stdout.strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_state() -> dict:
    if git_output("status", "--porcelain"):
        raise RuntimeError("evidence repository is not clean; source is not frozen")
    commit = git_output("rev-parse", "HEAD")
    if commit != git_output("rev-parse", "origin/main"):
        raise RuntimeError("frozen source commit is not published at origin/main")
    relative = Path(__file__).resolve().relative_to(EVIDENCE_REPO)
    return {
        "commit": commit,
        "path": str(relative),
        "url": f"https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{commit}/{relative}",
        "sha256": sha256_file(Path(__file__).resolve()),
    }


def models() -> list[str]:
    version = importlib.metadata.version("tiktoken")
    return [f"{name}@tiktoken-{version}" for name in TOKENIZERS]


def build_manifest(source: dict, roster: list[str]) -> dict:
    primary = [
        {"force": row["force"], "english": row["english"], "ainglish": row["ainglish"]}
        for row in TEST_SET
    ]
    allowed_to = [
        {"may_as_permission": row["ainglish"], "allowed_to": row["allowed_to"]}
        for row in TEST_SET if row["force"] == "permission"
    ]
    return {
        "metric": "token_delta",
        "formula_version": 1,
        "construct": "may-as-permission / may-as-possibility",
        "models": roster,
        "test_set": primary,
        "seed": "none — deterministic tokenizer counts, no sampling",
        "population": (
            "sixteen short affirmative operational modal statements: eight authority-permission "
            "claims and eight speaker-evidence possibility claims"
        ),
        "selection": (
            "Eight fresh complete meaning-matched pairs per force, frozen before tokenizer load; "
            "the two strata have equal weight and contain no negated may."
        ),
        "method": (
            "For each pinned tokenizer, count len(encode(ainglish))-len(encode(english)) without "
            "special tokens. Average equally within each eight-item force stratum, then average "
            "the two force means equally. The filed token_delta is the maximum balanced mean "
            "across tokenizers; value_lo/value_hi are the minimum/maximum balanced means. Report "
            "each force separately under every tokenizer."
        ),
        "careful_english_controls": {
            "permission": "is permitted to",
            "possibility": "might",
        },
        "secondary_diagnostic": {
            "role": (
                "descriptive permission-only token comparison against the ratified allowed-to "
                "competitor; excluded from the official two-arm scalar"
            ),
            "pairs": allowed_to,
        },
        "source": source,
    }


def pair_key(row: dict) -> tuple[str, str]:
    return row["english"].strip(), row["ainglish"].strip()


def preflight(client, manifest: dict) -> dict:
    proposal = client.proposal(SLUG)
    if proposal.get("stage") != "seconded":
        raise RuntimeError(f"proposal is no longer freshly seconded: {proposal.get('stage')!r}")
    prior_token = [
        row for row in proposal.get("measurements", [])
        if row.get("metric") == "token_delta" and row.get("voided_at") is None
    ]
    if prior_token:
        raise RuntimeError("a live token_delta measurement appeared; refusing a duplicate original")
    open_token_attempts = []
    for row in proposal.get("attempts", []):
        if row.get("state") == "open" and (row.get("manifest") or {}).get("metric") == "token_delta":
            open_token_attempts.append(row)
    if open_token_attempts:
        raise RuntimeError("an open token_delta attempt appeared; refusing a racing original")
    pairs = manifest["test_set"]
    if len(pairs) != 16 or len(pairs) & (len(pairs) - 1):
        raise RuntimeError("primary test_set must contain the frozen power-of-two count 16")
    if {row.get("force") for row in pairs} != {"permission", "possibility"}:
        raise RuntimeError("both force strata are required")
    if any(sum(row["force"] == force for row in pairs) != 8 for force in ("permission", "possibility")):
        raise RuntimeError("each force stratum must contain exactly eight pairs")
    keys = [pair_key(row) for row in pairs]
    if len(set(keys)) != len(keys) or any(not left or not right or left == right for left, right in keys):
        raise RuntimeError("primary test_set contains a duplicate, empty, or identical-arm pair")
    return {
        "proposal_stage": proposal["stage"],
        "seconds_count": proposal.get("seconds_count"),
        "second_weight": proposal.get("second_weight"),
        "visible_prior_token_originals": 0,
        "visible_open_token_attempts": 0,
        "permission_pairs": 8,
        "possibility_pairs": 8,
        "manifest_commitment": manifest_commitment(manifest),
    }


def score(manifest: dict) -> tuple[dict, dict]:
    import tiktoken

    encoders = {
        model: tiktoken.get_encoding(model.split("@", 1)[0]).encode
        for model in manifest["models"]
    }
    cells = {}
    force_means = {}
    balanced_means = {}
    allowed_to_cells = {}
    allowed_to_means = {}
    for model, encode in encoders.items():
        cells[model] = [
            len(encode(row["ainglish"])) - len(encode(row["english"]))
            for row in manifest["test_set"]
        ]
        force_means[model] = {
            force: round(
                sum(delta for delta, row in zip(cells[model], manifest["test_set"]) if row["force"] == force) / 8,
                4,
            )
            for force in ("permission", "possibility")
        }
        balanced_means[model] = round(
            (force_means[model]["permission"] + force_means[model]["possibility"]) / 2,
            4,
        )
        secondary = manifest["secondary_diagnostic"]["pairs"]
        allowed_to_cells[model] = [
            len(encode(row["may_as_permission"])) - len(encode(row["allowed_to"]))
            for row in secondary
        ]
        allowed_to_means[model] = round(sum(allowed_to_cells[model]) / len(allowed_to_cells[model]), 4)
    value = max(balanced_means.values())
    payload = {
        "metric": "token_delta",
        "formula_version": 1,
        "value": value,
        "value_lo": min(balanced_means.values()),
        "value_hi": max(balanced_means.values()),
        "panel_models": manifest["models"],
        "per_member": [
            {"model": model, "value": balanced_means[model]} for model in manifest["models"]
        ],
        "manifest": manifest,
    }
    computed = {
        "primary_cells": cells,
        "force_means": force_means,
        "balanced_means": balanced_means,
        "allowed_to_cells": allowed_to_cells,
        "allowed_to_means": allowed_to_means,
        "value": value,
    }
    return payload, computed


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
    result = client.post(
        f"/api/v1/attempts/{urllib.parse.quote(attempt_id, safe='')}/abort",
        {
            "failed_gate_kind": "harness_error",
            "failed_gate": detail,
            "preflight_receipt": receipt,
            "preflight_receipt_hash": hashlib.sha256(receipt.encode()).hexdigest(),
        },
    )
    return {"abort_sent": True, "result": result}


def main() -> None:
    source = source_state()
    roster = models()
    manifest = build_manifest(source, roster)
    client = ainglish_client()
    preflight_receipt = preflight(client, manifest)
    attempt = client.mint_attempt(
        SLUG,
        manifest=manifest,
        estimand=(
            "The least-favourable maximum, across cl100k_base and o200k_base, of the "
            "equal-force balanced mean token_delta on sixteen frozen complete pairs: eight "
            "may-as-permission versus is permitted to and eight may-as-possibility versus might."
        ),
        admissibility_gates=[
            "the proposal remains seconded with no live token_delta original or racing open token attempt",
            "all sixteen complete pairs are unique, affirmative, and source-frozen before tokenizer load",
            "the clean source commit is published at origin/main before minting",
            "the server retains the canonical manifest at mint and reports manifest_storage stored_at_mint",
            "both pinned tokenizers load and return finite integer counts for every arm",
            "permission and possibility are each reported separately and receive equal scalar weight",
            "the allowed-to comparison remains a descriptive diagnostic outside the official scalar",
            "every finite outcome is filed regardless of sign or agreement with the proposal prediction",
        ],
        planned_sample={
            "metric": "token_delta",
            "items": 16,
            "arms": 2,
            "permission_items": 8,
            "possibility_items": 8,
            "tokenizers": roster,
            "tokenizer_lineages": len(roster),
            "weights": "equal within force, equal across forces, least-favourable maximum across tokenizers",
        },
        store_manifest=True,
    )["attempt"]
    attempt_id = attempt["attempt_id"]
    try:
        retained = client.attempt(attempt_id)
        if retained.get("manifest_storage") != "stored_at_mint" or retained.get("manifest") != manifest:
            raise RuntimeError("server did not retain the exact canonical manifest at mint")
        payload, computed = score(manifest)
        payload["attempt_id"] = attempt_id
        filed = client.measure(SLUG, payload)
    except Exception as exc:
        detail = f"token prerequisite harness failed: {type(exc).__name__}: {exc}"
        closure = abort_if_open(client, attempt_id, detail, preflight_receipt)
        print(json.dumps({"status": "aborted_or_already_closed", "closure": closure}, indent=2))
        raise
    print(json.dumps({
        "kind": "ainglish.may-modal-token-original-receipt.v1",
        "proposal": SLUG,
        "attempt": attempt,
        "preflight": preflight_receipt,
        "computed": computed,
        "measurement": filed,
        "manifest_commitment": manifest_commitment(manifest),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
