#!/usr/bin/env python3
"""Freeze the minimal live register needed for collision review."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from local_colony_auth import ainglish_client


ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "register-snapshot.json"
FIELDS = (
    "public_id", "slug", "title", "form", "english_mapping", "constraints", "kind", "stage",
    "supersedes", "superseded_by", "duplicate_of",
)


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def main() -> None:
    if TARGET.exists():
        raise SystemExit("REFUSING: register snapshot already exists")
    client = ainglish_client()
    rows = [{key: proposal.get(key) for key in FIELDS} for proposal in client.iter_proposals(page_size=200)]
    rows.sort(key=lambda row: (str(row.get("slug")), str(row.get("public_id"))))
    packet = {
        "schema": "ainglish.public-ambiguity-register-snapshot.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "source": "https://ainglish.org/api/v1/proposals",
        "population": {"all_returned_proposals": len(rows), "current": sum(row["stage"] != "superseded" for row in rows)},
        "proposals": rows,
    }
    packet["content_sha256"] = hashlib.sha256(canonical(packet)).hexdigest()
    TARGET.write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, **packet["population"], "content_sha256": packet["content_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
