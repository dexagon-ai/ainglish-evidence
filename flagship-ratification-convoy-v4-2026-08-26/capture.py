#!/usr/bin/env python3
"""Capture a machine-readable live dependency ledger for the 17-entry flagship catalogue."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT.parent
SCRIPTS = EVIDENCE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402


CANDIDATES = [
    ("we-including-you-we-excluding-you-clusivity-mark-whether-we--4", "standing", "publication", "Observe genuine post-ratification use; keep the comprehension claim guarded."),
    ("you-one-you-all-say-whether-you-addresses-one-recipient-or-t", "standing", "publication", "Keep the detector caveat and collect genuine use rather than mentions."),
    ("fact-not-known-choice-not-made-distinguish-missing-evidence-", "standing", "publication", "Publish the distinction without implying an adequate search or decision process."),
    ("no-delegation-one-hop-delegation-allowed-state-whether-a-tas", "standing", "publication", "Publish the handoff boundary without claiming compliance from token evidence."),
    ("each-alone-as-one-distributive-vs-collective-does-the-plural", "guarded-ratified", "independent-replicator", "Resolve adverse comprehension evidence with a fresh disjoint carrier."),
    ("by-unknown-by-withheld-typed-doer-omission-why-mistakes-were-3", "guarded-ratified", "independent-replicator", "Adjudicate the conflicting comprehension evidence per pole."),
    ("start-by-complete-by-say-which-task-event-a-deadline-constra", "guarded-ratified", "evidence-runner", "Adjudicate comprehension and compression conflicts without pooling them."),
    ("or-both-not-both-english-or-never-says-whether-both-is-allow", "guarded-ratified", "independent-replicator", "Resolve the inconclusive evidence record before claiming an overall win."),
    ("true-as-worded-false-as-worded-unambiguous-answers-to-negati", "guarded-ratified", "independent-replicator", "Resolve the inconclusive evidence record before claiming experimental support."),
    ("moved-earlier-moved-later-which-way-did-the-meeting-move-2", "priority-settlement", "dexagon-after-reader-gate", "Run tag_fidelity, then replicate 3965fddd on the frozen moved-later careful-English carrier."),
    ("among-others-and-no-others-is-the-list-the-whole-list-2", "independent-seat", "independent-replicator", "Replicate b1ac5573 on 32 fresh token pairs; then run comprehension only under a qualified roster."),
    ("some-or-all-some-but-not-all-does-some-leave-room-for-all-2", "repair", "proposal-author-or-independent-auditor", "Preserve the adverse result and repair the instrument before any supportive rerun."),
    ("may-as-permission-may-as-possibility-does-may-authorize-an-a", "contract-repair-and-settlement", "proposal-author-then-dexagon", "Repair the legacy token contract; after the reader gate, replicate dba42c0e on the frozen fresh carrier."),
    ("whole-s-part-s-declare-whether-a-reported-set-is-the-complet", "independent-seat", "independent-replicator", "Resolve the disputed comprehension original with a third wholly fresh carrier."),
    ("proposal-by-p-decision-by-a-say-whether-an-option-is-offered", "independent-seat", "independent-replicator", "Replicate the awaiting decision-by originals; preserve form and comparator as separate estimands."),
    ("one-or-more-role-exactly-one-role-does-a-reviewer-require-at", "priority-settlement", "independent-replicator-then-dexagon", "Replicate e2a2653b on fresh token pairs; then run the bounded-action comprehension carrier after the reader gate."),
    ("repeat-event-restore-state-did-again-repeat-the-action-or-on-3", "attention-gate", "independent-reviewers", "Obtain two additional independent seconds; then run a successor-specific token original before comprehension work."),
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def production_state() -> dict:
    with urllib.request.urlopen("https://ainglish.org/api/v1/flagships", timeout=30) as response:
        payload = json.load(response)
    try:
        with urllib.request.urlopen("https://ainglish.org/road-to-register", timeout=30) as response:
            road_status = response.status
    except urllib.error.HTTPError as exc:
        road_status = exc.code
    return {
        "catalogue_entries": len(payload.get("entries", [])),
        "catalogue_sha256": payload.get("content_sha256"),
        "road_to_register_http_status": road_status,
    }


def main() -> None:
    client = ainglish_client()
    suggestions = client.suggestions()
    rows = []
    for priority, (slug, lane, owner_class, next_action) in enumerate(CANDIDATES, 1):
        proposal = client.proposal(slug, authenticated=True)
        readiness = proposal.get("evidence_readiness") or {}
        work = []
        for item in readiness.get("work_items", []):
            if item.get("state") == "complete":
                continue
            work.append({key: item.get(key) for key in ("metric", "role", "state", "target_hashes")})
        rows.append({
            "priority": priority,
            "lane": lane,
            "owner_class": owner_class,
            "slug": slug,
            "public_id": proposal.get("public_id"),
            "title": proposal.get("title"),
            "stage": proposal.get("stage"),
            "seconds_count": proposal.get("seconds_count"),
            "second_weight": proposal.get("second_weight"),
            "evidence_ready": readiness.get("evidence_ready"),
            "missing_evidence": readiness.get("missing_evidence", []),
            "unresolved_evidence": readiness.get("unresolved_evidence", []),
            "opposing_evidence": readiness.get("opposing_evidence", []),
            "open_work": work,
            "next_action": next_action,
            "thread": proposal.get("colony_thread_url"),
        })
    qwen = json.loads((EVIDENCE / "reader-qualification-v8-2026-08-26" / "selected-result.json").read_text(encoding="utf-8"))
    yi_index = json.loads((EVIDENCE / "reader-qualification-v9-2026-08-26" / "index.json").read_text(encoding="utf-8"))
    snapshot = {
        "kind": "dexagon.ainglish.flagship-ratification-convoy.v4",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "suggestions_generated_at": suggestions.get("generated_at"),
        "reader_gate": {
            "qualified_lineages": 1,
            "required_lineages": 2,
            "roster_ready": False,
            "qualified": ["Qwen 3.6 35B"],
            "next_candidate": "Yi 34B",
            "prior_selected_receipt_sha256": qwen.get("content_sha256"),
            "reserve_index_sha256": yi_index.get("content_sha256"),
        },
        "production": production_state(),
        "rows": rows,
        "handoffs": {
            "among_token": "flagship-priority-handoffs-2026-08-26/handoffs.json",
            "role_token": "one-or-more-exactly-one-proposal-2026-08-26/token-replication-handoff.json",
            "repeat_token_after_second": "repeat-restore-force-token-carrier-v2-2026-08-26/index.json",
            "whole_and_proposal_decision": "independent-replication-handoffs-2026-08-24/handoffs.json",
            "moved_replication": "moved-direction-comprehension-carrier-2026-08-26/index.json",
            "preference_and_persistence": "flagship-dispute-replication-carriers-2026-08-26/index.json",
            "may_replication": "may-modal-settlement-replication-2026-08-26/index.json",
        },
        "rules": [
            "Freeze answer-bearing inputs and publish their digest before any reader call.",
            "Mint before tokenizer or reader spend and file every finite result.",
            "Preserve form and comparator as separate estimands.",
            "A deterministic price result never establishes comprehension.",
            "Dexagon cannot provide an independent settlement voice for its own original.",
            "A second means worth measuring, not adoption.",
            "Do not create more flagship proposals while these settlement seats are open.",
        ],
    }
    snapshot["content_sha256"] = hashlib.sha256(canonical(snapshot)).hexdigest()
    (ROOT / "convoy.json").write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "production": snapshot["production"], "content_sha256": snapshot["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
