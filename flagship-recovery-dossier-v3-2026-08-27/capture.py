#!/usr/bin/env python3
"""Capture the eight active flagship rows, their evidence, routing, and thread tails."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent.parent / "scripts"))
from local_colony_auth import ainglish_client, colony_client  # noqa: E402


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def measurement(value: dict) -> dict:
    submitter = value.get("submitter") or {}
    return {key: value.get(key) for key in (
        "metric", "value", "value_lo", "value_hi", "manifest_hash", "is_replication",
        "replicates_hash", "input_disjointness", "reproduced_ok", "settlement_eligible",
        "settlement_state", "confirmed", "evidence_state", "at",
    )} | {"submitter": submitter.get("name")}


def comment(value: dict) -> dict:
    author = value.get("author") or {}
    body = value.get("body") or value.get("safe_text") or ""
    return {
        "id": value.get("id"),
        "author": author.get("display_name") or author.get("username"),
        "created_at": value.get("created_at"),
        "body_sha256": hashlib.sha256(body.encode()).hexdigest(),
        "excerpt": body[:800],
    }


def main() -> None:
    target = ROOT / "snapshot.json"
    if target.exists():
        raise SystemExit("REFUSING: snapshot.json already exists")
    ainglish = ainglish_client()
    colony = colony_client()
    catalog = ainglish.flagships()
    suggestions = ainglish.suggestions()
    routed = suggestions.get("suggestions", [])
    active_entries = [entry for entry in catalog["entries"] if entry["project"]["stage"] != "ratified"]
    assert len(active_entries) == 8
    rows = []
    for entry in active_entries:
        pinned = entry["pinned_slug"]
        current_slug = entry["surface"].get("superseded_by") or pinned
        detail = ainglish.proposal(current_slug, authenticated=True)
        thread_url = detail.get("colony_thread_url") or ""
        post_id = urlparse(thread_url).path.rsplit("/", 1)[-1] if "/post/" in thread_url else None
        comments = colony.get_all_comments(post_id) if post_id else []
        rows.append({
            "rank": entry["editorial"]["rank"],
            "slug": current_slug,
            "public_id": detail.get("public_id"),
            "title": detail.get("title"),
            "form": detail.get("form"),
            "stage": detail.get("stage"),
            "proposer": (detail.get("proposer") or {}).get("name"),
            "evidence_contract": detail.get("evidence_contract"),
            "evidence_readiness": detail.get("evidence_readiness"),
            "verdict": detail.get("verdict"),
            "measurements": [measurement(value) for value in detail.get("measurements", [])],
            "measurer_independence": detail.get("measurer_independence"),
            "thread": {
                "url": thread_url,
                "post_id": post_id,
                "comment_count": len(comments),
                "tail": [comment(value) for value in comments[-5:]],
            },
            "routed_actions": [value for value in routed if (
                value.get("proposal_slug") or value.get("slug")
            ) == current_slug],
        })
    assert [row["rank"] for row in rows] == list(range(10, 18))
    snapshot = {
        "kind": "dexagon.ainglish.active-flagship-recovery-snapshot.v3",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "catalog_content_sha256": catalog.get("content_sha256"),
        "suggestions_generated_at": suggestions.get("generated_at"),
        "rows": rows,
        "network_reads": 18,
        "network_writes": 0,
        "governance_writes": 0,
        "model_calls": 0,
    }
    snapshot["content_sha256"] = hashlib.sha256(canonical(snapshot)).hexdigest()
    target.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "captured_at": snapshot["captured_at"],
        "active": len(rows),
        "routed": sum(bool(row["routed_actions"]) for row in rows),
        "content_sha256": snapshot["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
