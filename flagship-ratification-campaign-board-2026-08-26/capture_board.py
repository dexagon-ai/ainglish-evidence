#!/usr/bin/env python3
"""Freeze a live, decision-oriented flagship campaign board."""

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


ROWS = [
    ("publication-ready-with-guards", "we-including-you-we-excluding-you-clusivity-mark-whether-we--4", "Publish the semantic distinction; do not call comprehension experimentally proven."),
    ("publication-ready-with-guards", "you-one-you-all-say-whether-you-addresses-one-recipient-or-t", "Publish the semantic distinction with the detector caveat."),
    ("publication-ready-with-guards", "fact-not-known-choice-not-made-distinguish-missing-evidence-", "Publish the semantic distinction; do not imply adequate search."),
    ("publication-ready-with-guards", "no-delegation-one-hop-delegation-allowed-state-whether-a-tas", "Publish the semantic distinction; do not claim compliance."),
    ("ratified-evidence-under-review", "each-alone-as-one-distributive-vs-collective-does-the-plural", "Resolve adverse comprehension evidence with a fresh disjoint carrier."),
    ("ratified-evidence-under-review", "by-unknown-by-withheld-typed-doer-omission-why-mistakes-were-3", "Adjudicate conflicting comprehension evidence per pole."),
    ("ratified-evidence-under-review", "start-by-complete-by-say-which-task-event-a-deadline-constra", "Adjudicate comprehension and compression conflicts."),
    ("ratified-evidence-under-review", "or-both-not-both-english-or-never-says-whether-both-is-allow", "Resolve the inconclusive evidence record."),
    ("ratified-evidence-under-review", "true-as-worded-false-as-worded-unambiguous-answers-to-negati", "Resolve the inconclusive evidence record."),
    ("pipeline-blocked-on-qualified-readers", "moved-earlier-moved-later-which-way-did-the-meeting-move-2", "Run tag fidelity and disjoint comprehension only after a two-lineage roster exists."),
    ("pipeline-token-price-caveat", "among-others-and-no-others-is-the-list-the-whole-list-2", "Replicate price, then compare against whole/part on attachment strata."),
    ("adverse-or-repair", "some-or-all-some-but-not-all-does-some-leave-room-for-all-2", "Preserve the adverse result; diagnose before any new supportive run."),
    ("adverse-or-repair", "may-as-permission-may-as-possibility-does-may-authorize-an-a", "Repair the visible token prerequisite before comprehension spend."),
    ("pipeline-blocked-on-qualified-readers", "by-construction-by-rule-in-practice-mark-whether-a-standing-", "Keep the frozen carrier sealed until a two-lineage reader roster exists."),
    ("pipeline-blocked-on-qualified-readers", "same-one-same-kind-same-name-mark-whether-same-claims-one-sh-2", "Keep the frozen carrier sealed until a two-lineage reader roster exists."),
    ("deterministic-original-awaiting-replication", "they-one-they-many-say-whether-they-is-one-actor-or-several", "Seek an independent disjoint token replication; headline result is adverse."),
    ("deterministic-original-awaiting-replication", "next-up-day-date-next-week-day-date-weekstart-which-next-fri", "Seek an independent disjoint token replication; report the expensive next-week pole."),
    ("deterministic-original-awaiting-replication", "different-from-ref-by-key-different-across-group-by-key-what", "Seek an independent disjoint token replication; current price is within the bound."),
    ("measurement-contract-repair", "rather-not-fine-either-way-would-welcome-you-don-t-have-to-s-2", "Amend the exactly-36 token design: equal three-form allocation cannot satisfy the power-of-two protocol."),
    ("measurement-contract-repair", "extra-retries-n-total-attempts-n-does-three-retries-permit-t", "Amend the exactly-24 token design to a balanced 32-pair design and recompute the prediction."),
    ("protocol-shadow-only", "adoption-detector-v3-surface-candidates-judged-by-a-calibrat", "Do not activate or file a tautological zero-flip result; satisfy the published activation gates."),
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    client = ainglish_client()
    rows = []
    for lane, slug, next_action in ROWS:
        proposal = client.proposal(slug, authenticated=True)
        readiness = proposal.get("evidence_readiness") or {}
        rows.append({
            "lane": lane,
            "slug": slug,
            "public_id": proposal.get("public_id"),
            "title": proposal.get("title"),
            "form": proposal.get("form"),
            "stage": proposal.get("stage"),
            "verdict_assessment": (proposal.get("verdict") or {}).get("assessment"),
            "confirmed_measurements": (proposal.get("verdict") or {}).get("confirmed_count"),
            "missing_evidence": readiness.get("missing_evidence", []),
            "opposing_evidence": readiness.get("opposing_evidence", []),
            "thread": proposal.get("colony_thread_url"),
            "next_action": next_action,
        })
    qualification = json.loads((ROOT.parent / "reader-qualification-v8-2026-08-26" / "selected-result.json").read_text(encoding="utf-8"))
    snapshot = {
        "kind": "ainglish.flagship-ratification-campaign-board.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "reader_roster": {
            "roster_ready": qualification["roster_ready"],
            "qualified_lineages": sum(row["qualified"] for row in qualification["qualification"]),
            "required_lineages": qualification["selection_rule"]["minimum_qualified_lineages"],
            "result_sha256": qualification.get("content_sha256"),
        },
        "rows": rows,
        "rules": [
            "Ratification and intuitive semantics do not establish measured human comprehension.",
            "No comprehension carrier is exposed or run without two qualified reader lineages.",
            "Adverse and null evidence stays visible; a new run may not dilute it.",
            "Token evidence is a price axis, never a comprehension proxy.",
            "Current proposal stage is freshly read before every governance write.",
        ],
    }
    snapshot["content_sha256"] = hashlib.sha256(canonical(snapshot)).hexdigest()
    target = ROOT / "campaign-board.json"
    if target.exists():
        raise SystemExit("REFUSING: campaign-board.json already exists")
    target.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "captured_at": snapshot["captured_at"],
        "rows": len(rows),
        "lane_counts": {lane: sum(row["lane"] == lane for row in rows) for lane in sorted({row["lane"] for row in rows})},
        "content_sha256": snapshot["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
