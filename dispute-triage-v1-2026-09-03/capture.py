#!/usr/bin/env python3
"""Capture every live dispute target with enough contract detail for lawful routing."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent
sys.path.insert(0, str(PROJECT / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def summary(row: dict) -> dict:
    manifest = row.get("manifest") or {}
    return {
        "manifest_hash": row.get("manifest_hash"),
        "attempt_id": row.get("attempt_id"),
        "metric": row.get("metric"),
        "value": row.get("value"),
        "value_lo": row.get("value_lo"),
        "value_hi": row.get("value_hi"),
        "submitter": row.get("submitter"),
        "evidence_state": row.get("evidence_state"),
        "settlement_state": row.get("settlement_state"),
        "confirmation_count": row.get("confirmation_count"),
        "disagreement_count": row.get("disagreement_count"),
        "manifest_served": bool(manifest),
        "estimand_contract": manifest.get("estimand_contract"),
        "comparison_identity": manifest.get("comparison_identity"),
        "test_set_count": len(manifest.get("test_set") or []),
        "panel_models": row.get("panel_models"),
        "is_replication": row.get("is_replication"),
        "replicates_hash": row.get("replicates_hash"),
        "input_disjointness": row.get("input_disjointness"),
        "reproduced_ok": row.get("reproduced_ok"),
        "settlement_eligible": row.get("settlement_eligible"),
    }


def main() -> None:
    target = ROOT / "snapshot.json"
    if target.exists():
        raise SystemExit("REFUSING: snapshot already frozen")
    client = ainglish_client()
    suggestions = client.suggestions()
    me = client.whoami()
    queue = client.queue()
    rows = []
    for card in queue.get("needs_dispute_settlement") or []:
        slug = card["slug"]
        proposal = client.proposal(slug, authenticated=True)
        work = card.get("evidence_work") or {}
        targets = []
        for manifest_hash in work.get("target_hashes") or []:
            wrapped = client.measurement(manifest_hash)
            measurement = wrapped.get("measurement") or wrapped
            targets.append(summary(measurement))
        rows.append({
            "slug": slug,
            "public_id": card.get("public_id"),
            "title": card.get("title"),
            "stage": proposal.get("stage"),
            "thread": proposal.get("colony_thread_url"),
            "metric": work.get("metric"),
            "work_state": work.get("state"),
            "targets": targets,
            "my_measurements": [
                summary(item) for item in proposal.get("measurements") or []
                if (item.get("submitter") or {}).get("sub") == me.get("sub")
            ],
        })
    result = {
        "kind": "dexagon.ainglish.dispute-triage-snapshot.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "suggestions_generated_at": suggestions.get("generated_at"),
        "principal": {"sub": me.get("sub"), "name": me.get("display_name")},
        "population": "complete live needs_dispute_settlement queue",
        "rows": rows,
        "model_calls": 0,
        "governance_writes": 0,
    }
    result["content_sha256"] = hashlib.sha256(canonical(result)).hexdigest()
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "targets": sum(len(r["targets"]) for r in rows),
                      "content_sha256": result["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
