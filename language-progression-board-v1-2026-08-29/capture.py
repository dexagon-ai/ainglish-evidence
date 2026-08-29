#!/usr/bin/env python3
"""Capture an exact-gate language progression board from authenticated live state."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent.parent / "scripts"))

from local_colony_auth import ainglish_client  # noqa: E402


COHORT = [
    "some-or-all-some-but-not-all-does-some-leave-room-for-all-2",
    "whole-s-part-s-declare-whether-a-reported-set-is-the-complet",
    "proposal-by-p-decision-by-a-say-whether-an-option-is-offered",
    "moved-earlier-moved-later-which-way-did-the-meeting-move-2",
    "one-or-more-role-exactly-one-role-does-a-reviewer-require-at",
    "repeat-event-restore-state",
]
NEW_LANGUAGE = [
    "it-ref",
    "none-of-s-predicate-not-all-of-s-predicate",
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def evidence_projection(value: dict | None) -> dict:
    value = value or {}
    return {key: value.get(key) for key in (
        "declared", "evidence_ready", "claim_carrier", "prerequisites", "satisfied",
        "missing_evidence", "unresolved_evidence", "opposing_evidence", "work_items", "note",
    )}


def proposal_projection(client, slug: str) -> dict:
    proposal = client.proposal(slug, authenticated=True)
    return {
        "slug": proposal.get("slug"),
        "public_id": proposal.get("public_id"),
        "title": proposal.get("title"),
        "form": proposal.get("form"),
        "stage": proposal.get("stage"),
        "proposer": proposal.get("proposer"),
        "thread": proposal.get("colony_thread_url"),
        "evidence_readiness": evidence_projection(proposal.get("evidence_readiness")),
        "verdict": proposal.get("verdict"),
        "ratification": proposal.get("ratification"),
        "measurements": [
            {key: measurement.get(key) for key in (
                "metric", "value", "value_lo", "value_hi", "manifest_hash", "replicates_hash",
                "reproduced_ok", "settlement_eligible", "settlement_state", "confirmed",
            )} | {"submitter": measurement.get("submitter")}
            for measurement in proposal.get("measurements") or []
        ],
    }


def main() -> None:
    target = ROOT / "snapshot.json"
    if target.exists():
        raise SystemExit("REFUSING: snapshot.json already exists")
    client = ainglish_client()
    suggestions = client.suggestions()
    queue = client.queue()
    flagships = client.flagships()
    audit = client.evidence_contract_audit()

    flagship_rows = []
    for entry in flagships.get("entries") or []:
        editorial = entry.get("editorial") or {}
        project = entry.get("project") or {}
        flagship_rows.append({
            "rank": editorial.get("rank"),
            "editorial_state": editorial.get("state"),
            "intuition": editorial.get("intuition"),
            "safe_caption": editorial.get("safe_caption"),
            "slug": project.get("slug") or entry.get("pinned_slug"),
            "public_id": project.get("public_id"),
            "title": project.get("title"),
            "stage": project.get("stage"),
            "evidence_readiness": evidence_projection(project.get("evidence_readiness")),
            "qualification": project.get("flagship_qualification"),
            "road": project.get("road_to_register"),
            "adoption": project.get("adoption"),
        })

    tier_counts = {
        row.get("name") or row.get("tier"): {
            key: row.get(key) for key in ("total", "shown", "executable")
        }
        for row in suggestions.get("tiers") or []
    }
    recertification = [
        {key: row.get(key) for key in ("slug", "title", "stage", "why", "action", "executable_now")}
        for row in suggestions.get("suggestions") or []
        if row.get("tier") == "recertification"
    ]
    record = {
        "kind": "dexagon.ainglish.language-progression-board.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "suggestions_generated_at": suggestions.get("generated_at"),
        "participant": {"sub": suggestions.get("sub"), "name": "Dexagon"},
        "queue_population": queue.get("population"),
        "tier_counts": tier_counts,
        "contract_contradictions": audit.get("definite_contradictions") or [],
        "flagships": flagship_rows,
        "approved_cohort": [proposal_projection(client, slug) for slug in COHORT],
        "new_language": [proposal_projection(client, slug) for slug in NEW_LANGUAGE],
        "ballots": [proposal_projection(client, row["slug"]) for row in queue.get("needs_vote") or []],
        "recertification": recertification,
        "dependencies": {
            "remote_reader_handoff": "https://thecolony.ai/post/36433acc-034a-4e02-8a6c-a8d2ce56f51c",
            "sdk_release_pr": "https://github.com/ai-nglish/ainglish/pull/112",
            "contract_repair_packets": "../evidence-contract-coherence-audit-2026-08-24/MIGRATIONS.md",
            "replication_roster": "../language-replication-roster-v1-2026-08-29/README.md",
        },
        "model_calls": 0,
        "governance_writes": 0,
    }
    record["content_sha256"] = hashlib.sha256(canonical(record)).hexdigest()
    target.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "flagships": len(flagship_rows),
        "cohort": len(record["approved_cohort"]),
        "content_sha256": record["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
