#!/usr/bin/env python3
"""Freeze the live flagship catalog and the work surfaces that can advance it."""

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


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    output = ROOT / "snapshot.json"
    if output.exists():
        raise SystemExit("REFUSING: snapshot.json already exists")
    client = ainglish_client()
    flagships = client.flagships()
    suggestions = client.suggestions()
    queue = client.queue()
    participation = client.participation()
    snapshot = {
        "kind": "dexagon.ainglish.flagship-census.snapshot.v7",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "sources": {
            "flagships": "/api/v1/flagships",
            "suggestions": "/api/v1/me/suggestions",
            "queue": "/api/v1/queue",
            "participation": "/api/v1/participation",
        },
        "catalog_content_sha256": flagships["content_sha256"],
        "selection": flagships["selection"],
        "entries": flagships["entries"],
        "work_surface": {
            "generated_at": suggestions["generated_at"],
            "tiers": suggestions["tiers"],
            "suggestions": suggestions["suggestions"],
            "blocked_suggestions": suggestions["blocked_suggestions"],
        },
        "queue_counts": {key: len(queue[key]) for key in (
            "needs_second", "needs_measurement", "needs_evidence_completion", "needs_vote",
            "needs_gate_clearance", "needs_recertification",
        )},
        "participation_scarcity": participation["scarcity"],
        "claim_boundaries": [
            "Editorial intuitiveness is explicit site-builder judgement, not a human-study result.",
            "A semantic contrast can be displayed with a claim guard before comprehension is established.",
            "Ratification, comprehension evidence, independent settlement, and observed adoption remain separate axes.",
            "No composite score is treated as a ratification or publication gate.",
        ],
        "model_calls": 0,
        "model_downloads": 0,
        "governance_writes": 0,
    }
    snapshot["content_sha256"] = hashlib.sha256(canonical(snapshot)).hexdigest()
    output.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "captured_at": snapshot["captured_at"],
        "entries": len(snapshot["entries"]),
        "catalog_content_sha256": snapshot["catalog_content_sha256"],
        "content_sha256": snapshot["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
