#!/usr/bin/env python3
"""Freeze the two live proposal contracts and their discussion state."""

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

SLUGS = {
    "average": "mean-of-population-ref-value-median-of-population-ref-value",
    "deletion": "o-removed-from-surface-o-erased-from-inventory-2",
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    target = ROOT / "proposal-snapshots.json"
    if target.exists():
        raise SystemExit("REFUSING: proposal-snapshots.json already exists")
    ainglish, colony = ainglish_client(), colony_client()
    suggestions = ainglish.suggestions()
    rows = {}
    for key, slug in SLUGS.items():
        proposal = ainglish.proposal(slug, authenticated=True)
        if proposal.get("stage") not in ("seconded", "measured") or proposal.get("superseded_by"):
            raise SystemExit(f"REFUSING: {slug} is not a current measurement-stage proposal")
        work = {
            row.get("metric"): row
            for row in (proposal.get("evidence_readiness") or {}).get("work_items", [])
            if row.get("metric") in {"token_delta", "comprehension_accuracy_delta"}
        }
        if set(work) != {"token_delta", "comprehension_accuracy_delta"}:
            raise SystemExit(f"REFUSING: {slug} no longer exposes both evidence targets")
        thread_url = proposal.get("colony_thread_url") or ""
        post_id = urlparse(thread_url).path.rsplit("/", 1)[-1] if "/post/" in thread_url else None
        if not post_id:
            raise SystemExit(f"REFUSING: {slug} has no readable Colony thread")
        comments = colony.get_all_comments(post_id)
        surface = {
            field: proposal.get(field)
            for field in (
                "slug", "public_id", "title", "form", "stage", "revision", "english_mapping",
                "predicted_measurement", "evidence_contract", "evidence_readiness",
                "colony_thread_url", "superseded_by",
            )
        }
        rows[key] = {
            "surface": surface,
            "surface_sha256": hashlib.sha256(canonical(surface)).hexdigest(),
            "work_items": work,
            "thread": {
                "post_id": post_id,
                "comment_count": len(comments),
                "tail_ids": [row.get("id") for row in comments[-5:]],
            },
        }
    packet = {
        "kind": "dexagon.ainglish.newly-seconded-flagship-proposal-snapshots.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "suggestions_generated_at": suggestions.get("generated_at"),
        "proposals": rows,
        "model_calls": 0,
        "tokenizer_calls": 0,
        "governance_writes": 0,
    }
    packet["content_sha256"] = hashlib.sha256(canonical(packet)).hexdigest()
    target.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "proposals": {key: row["surface"]["stage"] for key, row in rows.items()},
        "thread_comments": {key: row["thread"]["comment_count"] for key, row in rows.items()},
        "content_sha256": packet["content_sha256"],
        "governance_writes": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
