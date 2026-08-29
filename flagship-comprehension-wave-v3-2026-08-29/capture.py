#!/usr/bin/env python3
"""Capture the authenticated live state this frozen wave was designed against."""

from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path

from local_colony_auth import ainglish_client


ROOT = Path(__file__).resolve().parent
PROGRESSION = [
    "they-one-they-many-say-whether-they-is-one-actor-or-several",
    "among-others-and-no-others-is-the-list-the-whole-list-2",
    "one-or-more-role-exactly-one-role-does-a-reviewer-require-at",
    "repeat-event-restore-state",
    "test-run-t-test-passed-t-did-tested-mean-the-check-happened-",
    "p-ack-as-receipt-r-p-ack-as-agreement-r",
]
FLAGSHIPS = [
    "we-including-you-we-excluding-you-clusivity-mark-whether-we--4",
    "you-one-you-all-say-whether-you-addresses-one-recipient-or-t",
    "fact-not-known-choice-not-made-distinguish-missing-evidence-",
    "no-delegation-one-hop-delegation-allowed-state-whether-a-tas",
    "text-fixed-ref-meaning-fixed-ref-declare-which-invariants-a-",
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def measurement_summary(row: dict) -> dict:
    return {
        "manifest_hash": row.get("manifest_hash"),
        "metric": row.get("metric"),
        "value": row.get("value"),
        "is_replication": row.get("is_replication"),
        "replicates_hash": row.get("replicates_hash"),
        "confirmed": row.get("confirmed"),
        "reproduced_ok": row.get("reproduced_ok"),
        "settlement_eligible": row.get("settlement_eligible"),
        "settlement_state": row.get("settlement_state"),
        "counts_toward_verdict": row.get("counts_toward_verdict"),
        "evidence_state": row.get("evidence_state"),
        "voided_at": row.get("voided_at"),
    }


def proposal_summary(proposal: dict) -> dict:
    return {
        "slug": proposal["slug"],
        "public_id": proposal["public_id"],
        "title": proposal["title"],
        "stage": proposal["stage"],
        "publication_status": proposal.get("publication_status"),
        "form": proposal["form"],
        "english_mapping_sha256": hashlib.sha256(proposal["english_mapping"].encode()).hexdigest(),
        "evidence_contract": proposal.get("evidence_contract"),
        "evidence_readiness": proposal.get("evidence_readiness"),
        "verdict": proposal.get("verdict"),
        "ratified_version": proposal.get("ratified_version"),
        "ratified_at": proposal.get("ratified_at"),
        "measurements": [measurement_summary(row) for row in proposal.get("measurements", [])],
    }


def main() -> None:
    target = ROOT / "live-receipt.json"
    if target.exists():
        raise SystemExit("REFUSING: live receipt already frozen")

    client = ainglish_client()
    suggestions = client.suggestions()
    selected = set(PROGRESSION)
    proposal_rows = {slug: proposal_summary(client.proposal(slug)) for slug in PROGRESSION + FLAGSHIPS}
    receipt = {
        "kind": "dexagon.ainglish.flagship-comprehension-wave-v3.live-receipt",
        "captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "register_suggestions_generated_at": suggestions.get("generated_at"),
        "budgets": suggestions.get("budgets"),
        "selected_suggestions": [
            {
                key: row.get(key)
                for key in (
                    "tier", "action", "slug", "stage", "title", "why",
                    "replicates_hash", "confirmation_capable", "executable_now",
                )
            }
            for row in suggestions.get("suggestions", [])
            if row.get("slug") in selected
        ],
        "progression": {slug: proposal_rows[slug] for slug in PROGRESSION},
        "ratified_flagships": {slug: proposal_rows[slug] for slug in FLAGSHIPS},
        "reader_gate": {
            "state": "closed",
            "required": "two distinct base-model lineages passing one fresh common construct-free holdout",
            "observed": "Qwen v10-general failed reference resolution at 5/8; no second qualified lineage is available",
        },
        "model_calls": 0,
        "governance_writes": 0,
    }
    receipt["content_sha256"] = hashlib.sha256(canonical(receipt)).hexdigest()
    target.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "captured_at": receipt["captured_at"],
        "progression_stages": {slug: row["stage"] for slug, row in receipt["progression"].items()},
        "flagship_stages": {slug: row["stage"] for slug, row in receipt["ratified_flagships"].items()},
        "content_sha256": receipt["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
