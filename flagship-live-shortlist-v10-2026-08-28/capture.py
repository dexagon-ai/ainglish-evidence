#!/usr/bin/env python3
"""Freeze the complete live language-evidence work surface for flagship ranking."""

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


SECTIONS = ("needs_evidence_completion", "needs_measurement")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    target = ROOT / "snapshot.json"
    if target.exists():
        raise SystemExit("REFUSING: snapshot.json already exists")

    client = ainglish_client()
    queue = client.queue()
    rows: list[dict] = []
    seen: set[str] = set()
    for section in SECTIONS:
        for queue_row in queue.get(section, []):
            if queue_row.get("kind") == "protocol":
                continue
            slug = queue_row["slug"]
            if slug in seen:
                continue
            seen.add(slug)
            proposal = client.proposal(slug, authenticated=True)
            rows.append({
                "queue_section": section,
                "queue": queue_row,
                "proposal": proposal,
            })

    snapshot = {
        "kind": "dexagon.ainglish.flagship-live-work-surface.v10",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "queue_kind": queue.get("kind"),
        "queue_population": queue.get("population"),
        "sections": list(SECTIONS),
        "language_rows": rows,
        "excluded_protocol_rows": sum(
            row.get("kind") == "protocol"
            for section in SECTIONS
            for row in queue.get(section, [])
        ),
        "governance_writes": 0,
        "model_calls": 0,
    }
    snapshot["content_sha256"] = hashlib.sha256(canonical(snapshot)).hexdigest()
    target.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "captured_at": snapshot["captured_at"],
        "language_rows": len(rows),
        "excluded_protocol_rows": snapshot["excluded_protocol_rows"],
        "content_sha256": snapshot["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
