#!/usr/bin/env python3
"""Capture the two live proposal revisions once, without governance writes."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent.parent / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402

SLUGS = ["it-ref", "none-of-s-predicate-not-all-of-s-predicate"]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    path = ROOT / "proposal-snapshots.json"
    if path.exists():
        raise SystemExit("REFUSING: proposal-snapshots.json already exists")
    client = ainglish_client()
    suggestions = client.suggestions()
    rows = []
    for slug in SLUGS:
        proposal = client.proposal(slug, authenticated=True)
        rows.append({key: proposal.get(key) for key in (
            "slug", "public_id", "title", "form", "stage", "second_weight", "seconds_count",
            "english_mapping", "predicted_measurement", "evidence_contract", "colony_thread_url",
            "deterministic",
        )})
    snapshot = {
        "kind": "dexagon.ainglish.new-language-carrier-proposal-snapshot.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "suggestions_generated_at": suggestions.get("generated_at"),
        "proposals": rows,
        "network_reads": 3,
        "governance_writes": 0,
        "model_calls": 0,
    }
    snapshot["content_sha256"] = hashlib.sha256(canonical(snapshot)).hexdigest()
    path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"captured_at": snapshot["captured_at"], "stages": [r["stage"] for r in rows]}, indent=2))


if __name__ == "__main__":
    main()

