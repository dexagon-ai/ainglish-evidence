#!/usr/bin/env python3
"""Capture the live non-runnable legacy dispute decision lane."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from ainglish.client import AinglishClient


ROOT = Path(__file__).resolve().parent


def main() -> None:
    client = AinglishClient()
    triage = client.dispute_triage()
    rows = []
    for target in triage.get("targets") or []:
        if target.get("resolution_class") != "contract_decision":
            continue
        proposal = client.proposal(target["slug"])
        reconstruction = target.get("reconstruction") or {}
        route = target.get("triage_route") or {}
        source = reconstruction.get("source_contract") or {}
        rows.append({
            "public_id": target.get("public_id"),
            "slug": target.get("slug"),
            "title": target.get("proposal_title"),
            "stage": proposal.get("stage"),
            "proposer": proposal.get("proposer"),
            "colony_thread_url": proposal.get("colony_thread_url"),
            "metric": target.get("metric"),
            "manifest_hash": target.get("manifest_hash"),
            "source_attempt_id": source.get("attempt_id"),
            "agreement_count": target.get("agreement_count"),
            "disagreement_count": target.get("disagreement_count"),
            "route": route.get("key"),
            "resolution_class": target.get("resolution_class"),
            "may_mint_measurement": route.get("may_mint_measurement"),
            "blocked_by": route.get("blocked_by"),
            "next_action": route.get("next_action"),
            "completion_receipt": route.get("completion_receipt"),
            "truth_boundary": reconstruction.get("truth_boundary"),
        })
    rows.sort(key=lambda row: (row["slug"], row["manifest_hash"]))
    assert len(rows) == 3, f"expected exactly three live contract decisions, found {len(rows)}"
    assert all(row["may_mint_measurement"] is False for row in rows)
    snapshot = {
        "kind": "dexagon.ainglish.legacy-dispute-decision-docket.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "source": "GET /api/v1/disputes/triage plus each public proposal record",
        "triage_summary": triage.get("summary"),
        "decision_count": len(rows),
        "decisions": rows,
    }
    (ROOT / "snapshot.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"decision_count": len(rows), "targets": [{"slug": row["slug"], "manifest_hash": row["manifest_hash"], "blocked_by": row["blocked_by"]} for row in rows]}, indent=2))


if __name__ == "__main__":
    main()
