#!/usr/bin/env python3
"""Freeze the current semantic proposal surfaces through the public Python SDK."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from ainglish.client import AinglishClient


ROOT = Path(__file__).resolve().parent
PROPOSALS = {
    "each-alone-as-one": "each-alone-as-one-distributive-vs-collective-does-the-plural",
    "you-one-you-all": "you-one-you-all-say-whether-you-addresses-one-recipient-or-t",
    "or-both-not-both": "or-both-not-both-english-or-never-says-whether-both-is-allow",
}
FIELDS = (
    "slug",
    "public_id",
    "title",
    "form",
    "stage",
    "ratified_version",
    "ratified_at",
    "english_mapping",
    "example_ainglish",
    "example_english",
    "superseded_by",
)


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    client = AinglishClient()
    surfaces = {}
    for key, slug in PROPOSALS.items():
        proposal = client.proposal(slug)
        surface = {field: proposal.get(field) for field in FIELDS}
        if surface["slug"] != slug or surface["stage"] != "ratified" or surface["superseded_by"]:
            raise SystemExit(f"REFUSING: {slug} is not the current ratified surface: {surface}")
        required_text = ("title", "form", "english_mapping", "example_ainglish", "example_english")
        if any(not isinstance(surface[field], str) or not surface[field].strip()
               for field in required_text):
            raise SystemExit(f"REFUSING: {slug} has an incomplete semantic surface")
        surfaces[key] = {
            "source_url": f"https://ainglish.org/api/v1/proposals/{slug}",
            "surface_sha256": hashlib.sha256(canonical(surface)).hexdigest(),
            "surface": surface,
        }
    payload = {
        "kind": "dexagon.ainglish.flagship-learnability-proposal-snapshot.v1",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "sdk_read": "AinglishClient().proposal(slug)",
        "model_calls": 0,
        "governance_writes": 0,
        "proposals": surfaces,
    }
    payload["content_sha256"] = hashlib.sha256(canonical(payload)).hexdigest()
    (ROOT / "proposal-snapshots.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"proposals": len(surfaces), "content_sha256": payload["content_sha256"]}))


if __name__ == "__main__":
    main()

