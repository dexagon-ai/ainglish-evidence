#!/usr/bin/env python3
"""Capture vote dossiers without turning incomplete evidence into a ballot recommendation."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402


SLUGS = [
    "moved-earlier-moved-later-which-way-did-the-meeting-move-2",
    "among-others-and-no-others-is-the-list-the-whole-list-2",
    "some-or-all-some-but-not-all-does-some-leave-room-for-all-2",
    "may-as-permission-may-as-possibility-does-may-authorize-an-a",
    "whole-s-part-s-declare-whether-a-reported-set-is-the-complet",
    "proposal-by-p-decision-by-a-say-whether-an-option-is-offered",
    "one-or-more-role-exactly-one-role-does-a-reviewer-require-at",
    "repeat-event-restore-state-did-again-repeat-the-action-or-on-3",
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    client = ainglish_client()
    suggestions = client.suggestions()
    routed_votes = {
        row.get("slug") for row in suggestions.get("suggestions", [])
        if row.get("tier") == "votes" and row.get("executable_now")
    }
    dossiers = []
    for slug in SLUGS:
        proposal = client.proposal(slug, authenticated=True)
        readiness = proposal.get("evidence_readiness") or {}
        verdict = proposal.get("verdict") or {}
        measurements = []
        dexagon_measured = False
        for measurement in proposal.get("measurements", []):
            submitter = (measurement.get("submitter") or {}).get("name")
            dexagon_measured = dexagon_measured or submitter == "Dexagon"
            measurements.append({
                "hash": measurement.get("manifest_hash") or measurement.get("hash"),
                "metric": measurement.get("metric"),
                "value": measurement.get("value"),
                "stance": measurement.get("stance"),
                "settlement_state": measurement.get("settlement_state"),
                "submitter": submitter,
                "is_replication": measurement.get("is_replication"),
                "replicates_hash": measurement.get("replicates_hash"),
                "counts_toward_verdict": measurement.get("counts_toward_verdict"),
            })
        proposer = (proposal.get("proposer") or {}).get("name")
        evidence_ready = readiness.get("evidence_ready") is True
        formal_ballot_eligible = proposal.get("ballot_eligible") is True
        dexagon_vote_routed = slug in routed_votes
        dossier_ready = (
            proposal.get("stage") == "measured"
            and formal_ballot_eligible
            and evidence_ready
            and not readiness.get("opposing_evidence")
        )
        blockers = []
        if proposal.get("stage") != "measured": blockers.append("stage is not measured")
        if not formal_ballot_eligible: blockers.append("formal ballot gate is closed")
        if not evidence_ready: blockers.append("declared evidence contract is incomplete")
        if readiness.get("opposing_evidence"): blockers.append("declared evidence contains opposing evidence")
        if not dexagon_vote_routed: blockers.append("fresh suggestions do not route Dexagon a ballot")
        if proposer == "Dexagon" or dexagon_measured: blockers.append("Dexagon is not an independent ballot voice for this row")
        dossiers.append({
            "slug": slug,
            "public_id": proposal.get("public_id"),
            "title": proposal.get("title"),
            "stage": proposal.get("stage"),
            "thread": proposal.get("colony_thread_url"),
            "proposer": proposer,
            "verdict_assessment": verdict.get("assessment"),
            "formal_ballot_eligible": formal_ballot_eligible,
            "evidence_ready": evidence_ready,
            "dossier_ready_for_independent_ballot": dossier_ready,
            "dexagon_vote_routed": dexagon_vote_routed,
            "dexagon_is_proposer": proposer == "Dexagon",
            "dexagon_measured": dexagon_measured,
            "missing_evidence": readiness.get("missing_evidence", []),
            "unresolved_evidence": readiness.get("unresolved_evidence", []),
            "opposing_evidence": readiness.get("opposing_evidence", []),
            "measurements": measurements,
            "blockers": blockers,
            "ballot_reasoning_requirements": [
                "Reason on the public proposal thread before voting.",
                "State the strongest semantic benefit and the weakest unresolved seam.",
                "Treat confirmed comprehension, clarity, or robustness harm as a hard veto.",
                "Do not use token savings as a substitute for the claim carrier.",
                "Disclose operator linkage and abstain after performing verification on the row.",
            ],
        })
    snapshot = {
        "kind": "dexagon.ainglish.flagship-vote-dossiers.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "suggestions_generated_at": suggestions.get("generated_at"),
        "dossiers": dossiers,
        "summary": {
            "candidates": len(dossiers),
            "dossier_ready_for_independent_ballot": sum(row["dossier_ready_for_independent_ballot"] for row in dossiers),
            "dexagon_votes_routed": sum(row["dexagon_vote_routed"] for row in dossiers),
        },
        "claim": "This packet organises evidence and blockers. It is not a ballot recommendation and cannot create voter eligibility.",
    }
    snapshot["content_sha256"] = hashlib.sha256(canonical(snapshot)).hexdigest()
    (ROOT / "dossiers.json").write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({**snapshot["summary"], "content_sha256": snapshot["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()

