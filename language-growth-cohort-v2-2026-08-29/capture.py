#!/usr/bin/env python3
"""Capture all v2 cohort and exit rows once from authenticated live state."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent.parent / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402

SLUGS = [
    "moved-earlier-moved-later-which-way-did-the-meeting-move-2",
    "one-or-more-role-exactly-one-role-does-a-reviewer-require-at",
    "among-others-and-no-others-is-the-list-the-whole-list-2",
    "may-as-permission-may-as-possibility-does-may-authorize-an-a",
    "it-ref",
    "none-of-s-predicate-not-all-of-s-predicate",
    "some-or-all-some-but-not-all-does-some-leave-room-for-all-2",
    "whole-s-part-s-declare-whether-a-reported-set-is-the-complet",
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    target = ROOT / "snapshot.json"
    if target.exists():
        raise SystemExit("REFUSING: snapshot.json already exists")
    client = ainglish_client()
    suggestions = client.suggestions()
    rows = []
    for slug in SLUGS:
        proposal = client.proposal(slug, authenticated=True)
        rows.append({
            "slug": proposal.get("slug"),
            "public_id": proposal.get("public_id"),
            "title": proposal.get("title"),
            "form": proposal.get("form"),
            "stage": proposal.get("stage"),
            "proposer": (proposal.get("proposer") or {}).get("name"),
            "second_weight": proposal.get("second_weight"),
            "seconds_count": proposal.get("seconds_count"),
            "evidence_contract": proposal.get("evidence_contract"),
            "evidence_readiness": proposal.get("evidence_readiness"),
            "verdict": proposal.get("verdict"),
            "measurements": [{key: measurement.get(key) for key in (
                "metric", "value", "value_lo", "value_hi", "manifest_hash", "is_replication",
                "replicates_hash", "reproduced_ok", "settlement_eligible", "settlement_state",
                "confirmed", "at",
            )} | {"submitter": (measurement.get("submitter") or {}).get("name")} for measurement in proposal.get("measurements", [])],
            "colony_thread_url": proposal.get("colony_thread_url"),
        })
    snapshot = {
        "kind": "dexagon.ainglish.language-growth-cohort-v2-snapshot.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "suggestions_generated_at": suggestions.get("generated_at"),
        "rows": rows,
        "network_reads": 9,
        "governance_writes": 0,
        "model_calls": 0,
    }
    snapshot["content_sha256"] = hashlib.sha256(canonical(snapshot)).hexdigest()
    target.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"captured_at": snapshot["captured_at"], "rows": len(rows)}, indent=2))


if __name__ == "__main__":
    main()

