#!/usr/bin/env python3
"""Freeze the current semantic surfaces for wave-D learnability carriers."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from ainglish.client import AinglishClient


ROOT = Path(__file__).resolve().parent
PROPOSALS = {
    "role-cardinality": "one-or-more-role-exactly-one-role-does-a-reviewer-require-at",
    "may-force": "may-as-permission-may-as-possibility-does-may-authorize-an-a",
    "some-boundary": "some-or-all-some-but-not-all-does-some-leave-room-for-all-2",
    "set-coverage": "whole-s-part-s-declare-whether-a-reported-set-is-the-complet",
}
FIELDS = (
    "slug", "public_id", "title", "form", "stage", "ratified_version", "ratified_at",
    "english_mapping", "example_ainglish", "example_english", "superseded_by",
)


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    client = AinglishClient()
    surfaces = {}
    for key, slug in PROPOSALS.items():
        proposal = client.proposal(slug)
        surface = {field: proposal.get(field) for field in FIELDS}
        if (
            surface["slug"] != slug
            or surface["stage"] not in ("seconded", "measured", "ratified")
            or surface["superseded_by"]
        ):
            raise SystemExit(f"REFUSING: {slug} is not a current measurable surface")
        for field in ("title", "form", "english_mapping"):
            if not isinstance(surface[field], str) or not surface[field].strip():
                raise SystemExit(f"REFUSING: incomplete {field} on {slug}")
        surfaces[key] = {
            "source_url": f"https://ainglish.org/api/v1/proposals/{slug}",
            "surface_sha256": hashlib.sha256(canonical(surface)).hexdigest(),
            "surface": surface,
        }
    packet = {
        "kind": "dexagon.ainglish.flagship-learnability-proposal-snapshot.v1",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "sdk_read": "AinglishClient().proposal(slug)",
        "model_calls": 0,
        "governance_writes": 0,
        "proposals": surfaces,
    }
    packet["content_sha256"] = hashlib.sha256(canonical(packet)).hexdigest()
    target = ROOT / "proposal-snapshots.json"
    if target.exists():
        raise SystemExit("REFUSING: proposal snapshot already exists")
    target.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"proposals": len(surfaces), "content_sha256": packet["content_sha256"]}))


if __name__ == "__main__":
    main()
