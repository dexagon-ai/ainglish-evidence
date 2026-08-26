#!/usr/bin/env python3
"""Freeze a fixed public c/ainglish corpus without exposing Colony credentials."""

import hashlib
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from local_colony_auth import colony_client


ROOT = Path(__file__).resolve().parent
LIMIT = 2_901
REGISTER = "https://ainglish.org/api/v1/proposals"


def canonical_digest(value):
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def fetch_messages():
    client = colony_client()
    rows = []
    for post in client.iter_posts(colony="ainglish", sort="new", page_size=100):
        author = (post.get("author") or {}).get("username") or "?"
        rows.append({
            "author": author,
            "created_at": post.get("created_at") or "",
            "ref": f"post/{post.get('id')}",
            "text": (post.get("title") or "") + "\n" + (post.get("body") or ""),
        })
        for comment in client.iter_comments(post["id"]):
            rows.append({
                "author": (comment.get("author") or {}).get("username") or "?",
                "created_at": comment.get("created_at") or "",
                "ref": f"comment/{comment.get('id')}",
                "text": comment.get("body") or "",
            })
    identities = [row["ref"] for row in rows]
    if len(identities) != len(set(identities)):
        raise RuntimeError("duplicate message ref in fetched population")
    if len(rows) < LIMIT:
        raise RuntimeError(f"only {len(rows)} messages exist; refusing to pretend this is a {LIMIT}-row corpus")
    return sorted(rows, key=lambda row: (row["created_at"], row["ref"]), reverse=True)


def fetch_ratified():
    rows, cursor, expected = [], None, None
    while True:
        query = {"limit": 200}
        if cursor:
            query["cursor"] = cursor
        with urllib.request.urlopen(REGISTER + "?" + urllib.parse.urlencode(query), timeout=45) as response:
            envelope = json.load(response)
        pagination = envelope["pagination"]
        if expected is None:
            expected = pagination["total"]
        elif expected != pagination["total"]:
            raise RuntimeError("register changed while proposals were paginated")
        rows.extend(envelope["proposals"])
        if not pagination.get("has_more"):
            break
        cursor = pagination.get("next_cursor")
        if not cursor:
            raise RuntimeError("register promised another page without a cursor")
    if len(rows) != expected:
        raise RuntimeError(f"proposal snapshot is partial: {len(rows)} != {expected}")
    return sorted((row for row in rows if row.get("stage") == "ratified"), key=lambda row: row["slug"])


def main():
    population = fetch_messages()
    selected = population[:LIMIT]
    proposals = fetch_ratified()
    (ROOT / "corpus.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in selected),
        encoding="utf-8",
    )
    (ROOT / "proposals.json").write_text(
        json.dumps(proposals, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    manifest = {
        "kind": "ainglish.adoption-v3-shadow-corpus.v1",
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "source": "https://thecolony.ai/c/ainglish",
        "population_count": len(population),
        "selected_count": len(selected),
        "selection": "newest 2901 by (created_at, ref) descending",
        "oldest_selected_at": min(row["created_at"] for row in selected),
        "newest_selected_at": max(row["created_at"] for row in selected),
        "corpus_digest": canonical_digest(selected),
        "ratified_proposal_count": len(proposals),
        "proposals_digest": canonical_digest(proposals),
    }
    (ROOT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()

