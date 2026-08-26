#!/usr/bin/env python3
"""Capture the official flagship catalog plus the role-cardinality pipeline candidate."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
sys.path.insert(0, str(REPO.parent / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402


ROLE_SLUG = "one-or-more-role-exactly-one-role-does-a-reviewer-require-at"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def project(detail: dict) -> dict:
    return {key: detail.get(key) for key in (
        "slug", "public_id", "title", "form", "english_mapping", "stage", "kind",
        "ratified_version", "ratified_at", "superseded_by", "colony_thread_url",
        "evidence_readiness", "verdict", "publication_status",
    )}


def main() -> None:
    client = ainglish_client()
    catalog = client.flagships()
    official = []
    for entry in catalog["entries"]:
        pinned = entry["pinned_slug"]
        current_slug = entry["surface"].get("superseded_by") or pinned
        official.append({
            "rank": entry["editorial"]["rank"],
            "category": entry["editorial"]["category"],
            "pinned_slug": pinned,
            "current_slug": current_slug,
            "pin_is_current": pinned == current_slug,
            "editorial": entry["editorial"],
            "catalog_project": project(entry["project"]),
            "current_project": project(client.proposal(current_slug, authenticated=True)),
        })
    role = project(client.proposal(ROLE_SLUG, authenticated=True))
    snapshot = {
        "kind": "dexagon.ainglish.flagship-publication-atlas-snapshot.v2",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "catalog_sha256": catalog.get("content_sha256"),
        "catalog_selection": catalog.get("selection"),
        "official": official,
        "pipeline_additions": [{
            "editorial_rank": 14,
            "category": "role cardinality",
            "project": role,
            "before": "A reviewer must approve the release.",
            "after": "one-or-more(reviewer): approve the release. / exactly-one(reviewer): approve the release.",
            "safe_caption": "Say whether one participant is the minimum or the exact limit.",
            "do_not_say": "Do not call this measured, ratified, or comprehension-improving while it awaits an independent second and both evidence metrics.",
        }],
        "model_calls": 0,
        "governance_writes": 0,
    }
    snapshot["content_sha256"] = hashlib.sha256(canonical(snapshot)).hexdigest()
    target = ROOT / "snapshot.json"
    if target.exists():
        raise SystemExit("REFUSING: snapshot.json already exists")
    target.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"official": len(official), "pipeline_additions": 1, "content_sha256": snapshot["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()

