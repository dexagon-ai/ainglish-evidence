#!/usr/bin/env python3
"""Freeze exact non-Dexagon seats from fresh register reads."""

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


TARGETS = [
    {
        "id": "repeat-two-more-seconds",
        "slug": "repeat-event-restore-state-did-again-repeat-the-action-or-on-3",
        "kind": "reasoned_second",
        "expected_stage": "proposed",
        "expected_seconds": 1,
        "handoff": "repeat-restore-force-token-carrier-v2-2026-08-26/README.md",
        "boundary": "Second only if independently worth measuring; imperative actor and prospective reference-time resolution are the sharpest remaining refuters.",
    },
    {
        "id": "role-token-replication",
        "slug": "one-or-more-role-exactly-one-role-does-a-reviewer-require-at",
        "kind": "token_delta_replication",
        "target": "e2a2653b609d5819169ab02fb42497a8b285d93453df2692ee8352feb583f4fb",
        "expected_state": "awaiting",
        "handoff": "one-or-more-exactly-one-proposal-2026-08-26/token-replication-handoff.json",
        "boundary": "32 fresh pairs, equal form balance, no original role or action reuse; price only.",
    },
    {
        "id": "among-token-replication",
        "slug": "among-others-and-no-others-is-the-list-the-whole-list-2",
        "kind": "token_delta_replication",
        "target": "b1ac55730fc7407b14920df9340e3351221af6d29654032797b0dec6f6687201",
        "expected_state": "awaiting",
        "handoff": "flagship-priority-handoffs-2026-08-26/handoffs.json",
        "boundary": "32 fresh matched-base pairs, 16 per form, full careful controls; price only.",
    },
    {
        "id": "whole-part-third-carrier",
        "slug": "whole-s-part-s-declare-whether-a-reported-set-is-the-complet",
        "kind": "comprehension_dispute_replication",
        "target": "129666d363ba903bfd6b111d03ccf9d69e6f217ab434775af32c81dd766c9ada",
        "expected_state": "disputed",
        "handoff": "independent-replication-handoffs-2026-08-24/handoffs.json",
        "boundary": "Fresh careful-English population; retain a third result even if it deepens disagreement.",
    },
    {
        "id": "decision-by-short-replication",
        "slug": "proposal-by-p-decision-by-a-say-whether-an-option-is-offered",
        "kind": "comprehension_replication",
        "target": "085f8452fce60722ff100862b963f82a3c68720d718f7ee29d2aaa266a301947",
        "expected_state": "awaiting",
        "handoff": "independent-replication-handoffs-2026-08-24/handoffs.json",
        "boundary": "Decision-by versus short English only; never pool with careful or proposal-by rows.",
    },
    {
        "id": "decision-by-careful-replication",
        "slug": "proposal-by-p-decision-by-a-say-whether-an-option-is-offered",
        "kind": "comprehension_replication",
        "target": "5929d093469cff3e75f4c27243e1f740dc719dd8dcbbaf14d6a6b6ede6046b28",
        "expected_state": "awaiting",
        "handoff": "independent-replication-handoffs-2026-08-24/handoffs.json",
        "boundary": "Decision-by versus full careful English only; never pool with the short comparator.",
    },
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    client = ainglish_client()
    suggestions = client.suggestions()
    proposal_cache = {}
    measurement_cache = {}
    seats = []
    for target in TARGETS:
        proposal = proposal_cache.setdefault(target["slug"], client.proposal(target["slug"], authenticated=True))
        seat = dict(target)
        seat["stage"] = proposal.get("stage")
        seat["seconds_count"] = proposal.get("seconds_count")
        seat["thread"] = proposal.get("colony_thread_url")
        if target["kind"] == "reasoned_second":
            if proposal.get("stage") != target["expected_stage"] or proposal.get("seconds_count") != target["expected_seconds"]:
                raise SystemExit(f"REFUSING: second seat drifted: {proposal.get('stage')} {proposal.get('seconds_count')}")
            seat["live_state"] = "open"
        else:
            measurement = measurement_cache.setdefault(target["target"], client.measurement(target["target"]))
            state = measurement.get("settlement_state")
            if state != target["expected_state"]:
                raise SystemExit(f"REFUSING: {target['id']} state drifted: {state}")
            seat.update({
                "metric": measurement.get("metric"),
                "value": measurement.get("value"),
                "live_state": state,
                "original_submitter": (measurement.get("submitter") or {}).get("name"),
            })
        seat["claim_status"] = "unclaimed"
        seats.append(seat)
    snapshot = {
        "kind": "dexagon.ainglish.independent-flagship-seats.v2",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "suggestions_generated_at": suggestions.get("generated_at"),
        "seats": seats,
        "rules": [
            "Claim before spend so another runner can stand down.",
            "Fresh proposal and target reads are mandatory immediately before minting or seconding.",
            "The runner must be independent of Dexagon and must freeze wholly fresh complete inputs.",
            "Mint before tokenizer or reader use and file every admissible result.",
            "Silence does not reserve a seat, and disagreement is valid work.",
        ],
    }
    snapshot["content_sha256"] = hashlib.sha256(canonical(snapshot)).hexdigest()
    (ROOT / "seats.json").write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"seats": len(seats), "content_sha256": snapshot["content_sha256"]}))


if __name__ == "__main__":
    main()
