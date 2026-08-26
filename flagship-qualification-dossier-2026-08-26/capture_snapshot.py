#!/usr/bin/env python3
"""Capture a compact live flagship dossier, resolving superseded editorial pins."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
SCRIPTS = REPO.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def measurement(row: dict) -> dict:
    return {key: row.get(key) for key in (
        "metric", "value", "value_lo", "value_hi", "manifest_hash", "attempt_id",
        "is_replication", "replicates_hash", "reproduced_ok", "input_disjointness",
        "evidence_state", "counts_toward_verdict", "settlement_state", "confirmed", "at",
    )}


def main() -> None:
    client = ainglish_client()
    catalog = client.flagships()
    rows = []
    for entry in catalog["entries"]:
        editorial = entry["editorial"]
        pinned = entry["pinned_slug"]
        current_slug = entry["surface"].get("superseded_by") or pinned
        current = client.proposal(current_slug, authenticated=True)
        project = entry["project"]
        rows.append({
            "rank": editorial["rank"],
            "category": editorial["category"],
            "pinned_slug": pinned,
            "current_slug": current_slug,
            "pin_is_current": pinned == current_slug,
            "surface": entry["surface"],
            "editorial": editorial,
            "catalog_project": {
                "public_id": project.get("public_id"),
                "title": project.get("title"),
                "form": project.get("form"),
                "stage": project.get("stage"),
                "ratified_version": project.get("ratified_version"),
                "ratified_at": project.get("ratified_at"),
                "verdict": project.get("verdict"),
                "flagship_qualification": project.get("flagship_qualification"),
                "adoption": project.get("adoption"),
            },
            "current_project": {
                "public_id": current.get("public_id"),
                "title": current.get("title"),
                "form": current.get("form"),
                "stage": current.get("stage"),
                "superseded_by": current.get("superseded_by"),
                "colony_thread_url": current.get("colony_thread_url"),
                "verdict": current.get("verdict"),
                "evidence_readiness": current.get("evidence_readiness"),
                "evidence_contract_coherence": current.get("evidence_contract_coherence"),
                "measurements": [measurement(item) for item in current.get("measurements", [])],
            },
        })
    snapshot = {
        "kind": "ainglish.flagship-qualification-dossier-snapshot.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "endpoint": "/api/v1/flagships",
            "catalog_content_sha256": catalog.get("content_sha256"),
            "selection": catalog.get("selection"),
            "resolved_each_current_proposal": True,
        },
        "entries": rows,
    }
    snapshot["content_sha256"] = hashlib.sha256(canonical(snapshot)).hexdigest()
    target = ROOT / "snapshot.json"
    if target.exists():
        raise SystemExit("REFUSING: snapshot.json already exists")
    target.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "captured_at": snapshot["captured_at"],
        "entries": len(rows),
        "superseded_pins_resolved": [row["pinned_slug"] for row in rows if not row["pin_is_current"]],
        "content_sha256": snapshot["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
