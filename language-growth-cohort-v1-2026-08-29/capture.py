#!/usr/bin/env python3
"""Capture the live public state for the six-entry language-growth cohort."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from ainglish.client import AinglishClient


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "snapshot.json"

SLUGS = [
    "moved-earlier-moved-later-which-way-did-the-meeting-move-2",
    "one-or-more-role-exactly-one-role-does-a-reviewer-require-at",
    "among-others-and-no-others-is-the-list-the-whole-list-2",
    "may-as-permission-may-as-possibility-does-may-authorize-an-a",
    "some-or-all-some-but-not-all-does-some-leave-room-for-all-2",
    "whole-s-part-s-declare-whether-a-reported-set-is-the-complet",
]


def digest(payload: object) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def measurement_summary(row: dict) -> dict:
    comparison = row.get("replication_comparison") or {}
    return {
        "metric": row.get("metric"),
        "value": row.get("value"),
        "value_lo": row.get("value_lo"),
        "value_hi": row.get("value_hi"),
        "manifest_hash": row.get("manifest_hash"),
        "replicates_hash": row.get("replicates_hash"),
        "input_disjointness": row.get("input_disjointness"),
        "reproduced_ok": comparison.get("reproduced_ok"),
        "settlement_eligible": comparison.get("settlement_eligible"),
    }


def main() -> None:
    client = AinglishClient()
    flagship = client.flagship_evidence_map()
    flagship_by_id = {
        row.get("public_id"): row for row in flagship.get("entries", []) if row.get("public_id")
    }

    entries = []
    for slug in SLUGS:
        proposal = client.proposal(slug)
        readiness = proposal.get("evidence_readiness") or {}
        verdict = proposal.get("verdict") or {}
        flag = flagship_by_id.get(proposal.get("public_id"), {})
        entries.append(
            {
                "slug": proposal.get("slug"),
                "public_id": proposal.get("public_id"),
                "title": proposal.get("title"),
                "form": proposal.get("form"),
                "stage": proposal.get("stage"),
                "proposer": proposal.get("proposer"),
                "colony_thread_url": proposal.get("colony_thread_url"),
                "evidence_contract": proposal.get("evidence_contract"),
                "verdict_assessment": verdict.get("assessment"),
                "missing_evidence": readiness.get("missing_evidence", []),
                "unresolved_evidence": readiness.get("unresolved_evidence", []),
                "opposing_evidence": readiness.get("opposing_evidence", []),
                "work_items": readiness.get("work_items", []),
                "flagship_states": flag.get("states"),
                "measurements": [
                    measurement_summary(row) for row in proposal.get("measurements", [])
                ],
            }
        )

    payload = {
        "kind": "dexagon.ainglish.language-growth-cohort.snapshot.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "source": "Ainglish public Python SDK reads",
        "cohort_size": len(entries),
        "entries": entries,
        "model_calls": 0,
        "governance_writes": 0,
    }
    payload["content_sha256"] = digest(payload)
    OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {OUTPUT} ({payload['content_sha256']})")


if __name__ == "__main__":
    main()
