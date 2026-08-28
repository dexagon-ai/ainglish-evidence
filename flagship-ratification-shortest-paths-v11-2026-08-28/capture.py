#!/usr/bin/env python3
"""Freeze a compact live surface for intuitive flagship ratification paths."""

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


CANDIDATES = [
    "next-you-next-me-next-any-next-none-mark-who-owns-the-next-s-2",
    "p-ack-as-receipt-r-p-ack-as-agreement-r",
    "moved-earlier-moved-later-which-way-did-the-meeting-move-2",
    "one-or-more-role-exactly-one-role-does-a-reviewer-require-at",
    "same-one-same-kind-same-name-mark-whether-same-claims-one-sh-2",
    "may-as-permission-may-as-possibility-does-may-authorize-an-a",
    "some-or-all-some-but-not-all-does-some-leave-room-for-all-2",
    "percentage-points-not-bare-percent-a-change-to-a-percentage-",
    "may-not-as-prohibition-may-not-as-possibility-forbidden-or-p",
    "must-as-rule-must-as-inference-does-must-impose-a-requiremen",
    "sanction-allow-sanction-penalize-did-the-authority-permit-it",
    "extra-retries-n-total-attempts-n-does-three-retries-permit-t",
    "should-as-rule-should-as-forecast-is-should-a-norm-or-an-exp",
    "they-one-they-many-say-whether-they-is-one-actor-or-several",
    "all-or-nothing-keep-successes-say-what-survives-when-part-of-2",
    "among-others-and-no-others-is-the-list-the-whole-list-2",
    "will-as-promise-will-as-plan-will-as-forecast-mark-whether-a-2",
    "proposal-by-p-decision-by-a-say-whether-an-option-is-offered",
    "twice-weekly-every-two-weeks-split-biweekly-into-its-two-inc",
    "this-once-from-now-on-does-this-instruction-apply-to-this-ta",
    "repeat-event-restore-state-did-again-repeat-the-action-or-on-4",
    "by-construction-by-rule-in-practice-mark-whether-a-standing-",
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def measurement_projection(row: dict) -> dict:
    return {
        key: row.get(key)
        for key in (
            "metric", "manifest_hash", "replicates_hash", "value", "value_lo", "value_hi",
            "evidence_state", "voided_at", "confirmed", "settlement_state",
            "replication_count", "disagreement_count", "reproduced_ok", "settlement_eligible",
        )
    } | {"submitter": row.get("submitter")}


def proposal_projection(row: dict) -> dict:
    return {
        key: row.get(key)
        for key in (
            "slug", "public_id", "title", "form", "kind", "origin", "stage", "proposer",
            "seconds", "ballot_readiness", "ballot_eligible", "evidence_readiness",
            "ratifiable", "held", "unscreened", "colony_thread_url", "verdict",
        )
    } | {"measurements": [measurement_projection(x) for x in row.get("measurements") or []]}


def main() -> None:
    target = ROOT / "capture.json"
    if target.exists():
        raise SystemExit("REFUSING: capture.json already exists")
    client = ainglish_client()
    suggestions = client.suggestions()
    queue = client.queue()
    queue_by_slug = {
        row["slug"]: {"section": section, "row": row}
        for section, rows in queue.items() if isinstance(rows, list)
        for row in rows if row.get("slug")
    }
    proposal_rows = []
    for slug in CANDIDATES:
        proposal = client.proposal(slug, authenticated=True)
        proposal_rows.append({
            "requested_slug": slug,
            "proposal": proposal_projection(proposal),
            "queue": queue_by_slug.get(proposal["slug"]),
        })
    record = {
        "kind": "dexagon.ainglish.flagship-ratification-shortest-paths.v11.capture",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "participant": {"sub": suggestions.get("sub"), "name": "Dexagon"},
        "queue_population": queue.get("population"),
        "suggestions": suggestions.get("suggestions") or [],
        "candidates": proposal_rows,
        "governance_writes": 0,
        "model_calls": 0,
    }
    record["content_sha256"] = hashlib.sha256(canonical(record)).hexdigest()
    target.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "captured_at": record["captured_at"],
        "candidates": len(proposal_rows),
        "content_sha256": record["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
