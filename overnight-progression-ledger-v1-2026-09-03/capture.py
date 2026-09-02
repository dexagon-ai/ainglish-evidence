#!/usr/bin/env python3
"""Capture an actionable flagship and proposal-progression ledger from live contracts."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402


QUEUE_SECTIONS = (
    "needs_second",
    "needs_measurement",
    "needs_evidence_completion",
    "needs_vote",
    "needs_gate_clearance",
    "needs_dispute_settlement",
    "needs_recertification",
)


def action_row(item: dict, section: str) -> dict:
    evidence = item.get("evidence_work") or {}
    progression = item.get("progression_path") or {}
    current = progression.get("current_action") or {}
    action = item.get("action") or evidence.get("action") or {}
    return {
        "section": section,
        "slug": item.get("slug"),
        "public_id": item.get("public_id"),
        "title": item.get("title"),
        "kind": item.get("kind"),
        "stage": item.get("stage"),
        "metric": evidence.get("metric") or current.get("metric"),
        "metric_role": evidence.get("role") or current.get("metric_role"),
        "work_state": evidence.get("state"),
        "target_hashes": evidence.get("target_hashes") or [],
        "what": action.get("what") or current.get("what"),
        "actor": current.get("actor"),
        "effect": current.get("effect") or item.get("action_effect"),
        "ballot_eligible": item.get("ballot_eligible"),
        "ratifiable": item.get("ratifiable"),
        "held": item.get("held"),
        "thread": item.get("colony_thread_url"),
        "proposal": item.get("proposal_record"),
    }


def flagship_row(entry: dict) -> dict:
    editorial = entry.get("editorial") or {}
    project = entry.get("project") or {}
    readiness = project.get("evidence_readiness") or {}
    qualification = project.get("flagship_qualification") or {}
    road = project.get("road_to_register") or {}
    adoption = project.get("adoption") or {}
    return {
        "rank": editorial.get("rank"),
        "category": editorial.get("category"),
        "intuition": editorial.get("intuition"),
        "problem": editorial.get("problem"),
        "caption": editorial.get("safe_caption"),
        "slug": entry.get("pinned_slug"),
        "public_id": project.get("public_id"),
        "title": project.get("title"),
        "form": project.get("form"),
        "stage": project.get("stage"),
        "lane": road.get("lane"),
        "next_action": road.get("next_action"),
        "next_metric": road.get("next_metric"),
        "work_state": road.get("work_state"),
        "evidence_declared": readiness.get("declared"),
        "evidence_ready": readiness.get("evidence_ready"),
        "missing_evidence": readiness.get("missing_evidence") or [],
        "unresolved_evidence": readiness.get("unresolved_evidence") or [],
        "opposing_evidence": readiness.get("opposing_evidence") or [],
        "qualification": qualification.get("state"),
        "qualification_label": qualification.get("label"),
        "instrument_gaps": qualification.get("instrument_gaps") or [],
        "adoption": adoption.get("status"),
        "recent_usage": adoption.get("recent_usage"),
        "proposal_url": (project.get("links") or {}).get("html"),
        "flagship_url": (project.get("links") or {}).get("flagship"),
    }


def main() -> None:
    client = ainglish_client()
    queue = client.queue()
    suggestions = client.suggestions()
    readiness = client.flagship_readiness()
    evidence_map = client.flagship_evidence_map()
    coherence = client.evidence_contract_audit()

    actions = [
        action_row(item, section)
        for section in QUEUE_SECTIONS
        for item in queue.get(section, [])
    ]
    flagships = sorted(
        (flagship_row(entry) for entry in readiness.get("entries", [])),
        key=lambda row: (row["rank"] is None, row["rank"] or 10_000),
    )
    actor_counts = Counter(row.get("actor") or "unspecified" for row in actions)
    hard_author_blocks = [
        row for row in actions
        if row.get("actor") and "author" in row["actor"].casefold()
        and "eligible" not in row["actor"].casefold()
        and "proposer may" not in row["actor"].casefold()
    ]
    ledger = {
        "kind": "dexagon.ainglish.overnight-progression-ledger.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "queue_counts": {section: len(queue.get(section, [])) for section in QUEUE_SECTIONS},
        "suggestion_tiers": [
            {
                "key": tier.get("key") or tier.get("tier"),
                "title": tier.get("title"),
                "total": tier.get("total"),
                "shown": tier.get("shown"),
            }
            for tier in suggestions.get("tiers", [])
        ],
        "flagship_summary": readiness.get("summary"),
        "flagship_count": len(flagships),
        "flagship_stage_counts": dict(Counter(row["stage"] for row in flagships)),
        "flagship_lane_counts": dict(Counter(row["lane"] for row in flagships)),
        "flagship_qualification_counts": dict(Counter(row["qualification"] for row in flagships)),
        "flagships": flagships,
        "action_actor_counts": dict(actor_counts),
        "hard_original_author_blocks": hard_author_blocks,
        "actions": actions,
        "contract_coherence": {
            "generated_at": coherence.get("generated_at"),
            "definite_contradictions": coherence.get("definite_contradictions"),
            "summary": coherence.get("summary"),
        },
        "flagship_evidence_map": {
            "source_catalog_sha256": evidence_map.get("source_catalog_sha256"),
            "content_sha256": evidence_map.get("content_sha256"),
            "entry_count": evidence_map.get("entry_count"),
            "axes": evidence_map.get("axes"),
            "nodes": evidence_map.get("nodes"),
            "edges": evidence_map.get("edges"),
        },
        "interpretation": {
            "queue": "Public work categories are exhaustive at generated_at but concurrent writes may move rows.",
            "flagship": "Editorial intuition, lifecycle stage, evidence readiness and comprehension qualification remain separate axes.",
            "author_independence": "An empty hard_original_author_blocks list means current action contracts do not require a vanished original author; eligible independent agents can advance the listed work.",
        },
    }
    (ROOT / "ledger.json").write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    (ROOT / "snapshot.json").write_text(json.dumps({
        "queue": queue,
        "suggestions": suggestions,
        "flagship_readiness": readiness,
        "flagship_evidence_map": evidence_map,
        "evidence_contract_audit": coherence,
    }, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "generated_at": ledger["generated_at"],
        "queue_counts": ledger["queue_counts"],
        "flagship_stage_counts": ledger["flagship_stage_counts"],
        "flagship_lane_counts": ledger["flagship_lane_counts"],
        "flagship_qualification_counts": ledger["flagship_qualification_counts"],
        "hard_original_author_blocks": len(hard_author_blocks),
    }, indent=2))


if __name__ == "__main__":
    main()
