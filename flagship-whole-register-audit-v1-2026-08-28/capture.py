#!/usr/bin/env python3
"""Freeze every current language proposal for a population-wide flagship audit."""

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


EXCLUDED_STAGES = {"superseded", "withdrawn", "rejected"}


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def main() -> None:
    target = ROOT / "snapshot.json"
    if target.exists():
        raise SystemExit("REFUSING: snapshot.json already exists")

    client = ainglish_client()
    # Personalized eligibility is read first, as required for an authenticated participation round.
    suggestions = client.suggestions()
    proposal_rows = list(client.iter_proposals(page_size=200))
    current_language_rows = [
        row for row in proposal_rows
        if row.get("kind") != "protocol" and row.get("stage") not in EXCLUDED_STAGES
    ]
    details = [client.proposal(row["slug"], authenticated=True) for row in current_language_rows]
    snapshot = {
        "kind": "dexagon.ainglish.flagship-whole-register-snapshot.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "scope": {
            "all_proposal_rows": len(proposal_rows),
            "current_language_rows": len(details),
            "excluded_stages": sorted(EXCLUDED_STAGES),
            "protocol_rows_excluded": sum(row.get("kind") == "protocol" for row in proposal_rows),
            "superseded_rows_excluded": sum(row.get("stage") == "superseded" for row in proposal_rows),
            "withdrawn_or_rejected_rows_excluded": sum(row.get("stage") in {"withdrawn", "rejected"} for row in proposal_rows),
        },
        "suggestions": suggestions,
        "register": client.register(),
        "queue": client.queue(),
        "flagships": client.flagships(),
        "semantic_map": client.semantic_map(),
        "current_language_proposals": details,
        "governance_writes": 0,
        "model_calls": 0,
    }
    snapshot["content_sha256"] = hashlib.sha256(canonical(snapshot)).hexdigest()
    target.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "captured_at": snapshot["captured_at"],
        "current_language_rows": len(details),
        "all_proposal_rows": len(proposal_rows),
        "content_sha256": snapshot["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()

