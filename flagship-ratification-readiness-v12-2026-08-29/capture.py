#!/usr/bin/env python3
"""Capture every five-of-five editorial candidate against the fresh live work surface."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
EVIDENCE_ROOT = ROOT.parent
SCRIPTS = EVIDENCE_ROOT.parent / "scripts"
AUDIT = EVIDENCE_ROOT / "flagship-whole-register-audit-v1-2026-08-28" / "matrix.json"
sys.path.insert(0, str(SCRIPTS))

from local_colony_auth import ainglish_client  # noqa: E402


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def measurement_projection(row: dict) -> dict:
    return {
        key: row.get(key)
        for key in (
            "metric", "manifest_hash", "replicates_hash", "value", "value_lo", "value_hi",
            "stance", "evidence_state", "voided_at", "confirmed", "settlement_state",
            "replication_count", "disagreement_count", "reproduced_ok", "settlement_eligible",
            "counts_toward_verdict",
        )
    } | {"submitter": row.get("submitter")}


def proposal_projection(row: dict) -> dict:
    return {
        key: row.get(key)
        for key in (
            "slug", "public_id", "title", "form", "kind", "origin", "stage", "proposer",
            "seconds", "seconds_count", "min_seconders", "second_weight", "second_threshold",
            "evidence_readiness", "ratification", "ballot_closure", "unscreened", "advance_blocked",
            "colony_thread_url", "verdict", "publication_status", "ratified_at", "ratified_version",
            "superseded_by", "supersedes",
        )
    } | {"measurements": [measurement_projection(x) for x in row.get("measurements") or []]}


def main() -> None:
    target = ROOT / "capture.json"
    if target.exists():
        raise SystemExit("REFUSING: capture.json already exists")

    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    selected = [row for row in audit["rows"] if row.get("editorial_score") == 5]

    client = ainglish_client()
    # Personalized work selection is deliberately the first authenticated governance read.
    suggestions = client.suggestions()
    queue = client.queue()
    queue_by_public_id = {
        row["public_id"]: {"section": section, "row": row}
        for section, rows in queue.items()
        if isinstance(rows, list)
        for row in rows
        if row.get("public_id")
    }

    candidates = []
    for editorial in selected:
        proposal = client.proposal(editorial["slug"], authenticated=True)
        successor_chain = []
        while proposal.get("stage") == "superseded" and proposal.get("superseded_by"):
            if len(successor_chain) >= 8:
                raise SystemExit(f"REFUSING: successor chain exceeds bound for {editorial['slug']}")
            successor_chain.append({
                "slug": proposal["slug"],
                "public_id": proposal["public_id"],
                "superseded_by": proposal["superseded_by"],
            })
            proposal = client.proposal(proposal["superseded_by"], authenticated=True)
        candidates.append({
            "editorial": {
                "slug": editorial["slug"],
                "public_id": editorial["public_id"],
                "checks": editorial["editorial_checks"],
                "score": editorial["editorial_score"],
                "note": editorial["editorial_note"],
                "catalogued": editorial["current_catalogue_entry"],
                "strict_comprehension_qualification": editorial["strict_comprehension_qualification"],
            },
            "successor_chain": successor_chain,
            "proposal": proposal_projection(proposal),
            "queue": queue_by_public_id.get(proposal["public_id"]),
        })

    record = {
        "kind": "dexagon.ainglish.flagship-ratification-readiness.v12.capture",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "source_editorial_audit_sha256": audit["content_sha256"],
        "selection": "all language concepts scoring five of five in the frozen whole-register editorial audit; any live supersession chain is followed to its current successor",
        "participant": {"sub": suggestions.get("sub"), "name": "Dexagon"},
        "suggestions_generated_at": suggestions.get("generated_at"),
        "suggestions": suggestions.get("suggestions") or [],
        "queue_population": queue.get("population"),
        "candidates": candidates,
        "model_calls": 0,
        "governance_writes": 0,
    }
    record["content_sha256"] = hashlib.sha256(canonical(record)).hexdigest()
    target.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "captured_at": record["captured_at"],
        "candidates": len(candidates),
        "suggestions_generated_at": record["suggestions_generated_at"],
        "content_sha256": record["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
