#!/usr/bin/env python3
"""Freeze proposal surfaces and non-answer-bearing target metadata."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from ainglish.client import AinglishClient


ROOT = Path(__file__).resolve().parent
TARGETS = {
    "preference": {
        "slug": "rather-not-fine-either-way-would-welcome-you-don-t-have-to-s-2",
        "replicates_hash": "b661b02842052ced7bc148b50fd4194c6084fbc27f1f70e22e45dd6af88e3d7d",
        "target_value": -23.44,
        "target_sample": {"real_items": 288, "frames": 72, "forms": 3, "power_strata": 3, "outcomes": 2, "arms": 2},
    },
    "persistence": {
        "slug": "this-once-from-now-on-does-this-instruction-apply-to-this-ta",
        "replicates_hash": "b4284015daf019e10b2bf4a7643c4341d6576859a57ae40d7c99ae0a1ced546c",
        "target_value": -9.67,
        "target_sample": {"real_items": 140, "core": 80, "discordant": 60, "forms": 2, "attachments": 4, "arms": 2},
    },
}
FIELDS = ("slug", "public_id", "title", "form", "stage", "english_mapping", "example_ainglish", "example_english", "superseded_by")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    client = AinglishClient()
    proposals = {}
    for key, target in TARGETS.items():
        proposal = client.proposal(target["slug"])
        surface = {field: proposal.get(field) for field in FIELDS}
        if surface["slug"] != target["slug"] or surface["stage"] not in ("seconded", "measured") or surface["superseded_by"]:
            raise SystemExit(f"REFUSING: {target['slug']} is no longer a current measurable surface")
        proposals[key] = {
            "source_url": f"https://ainglish.org/api/v1/proposals/{target['slug']}",
            "surface": surface,
            "surface_sha256": hashlib.sha256(canonical(surface)).hexdigest(),
            "target_original": {k: v for k, v in target.items() if k != "slug"},
        }
    packet = {
        "kind": "dexagon.ainglish.flagship-dispute-replication-snapshot.v1",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "target_metadata_scope": "public estimand and planned-sample facts only; no original answer-bearing carrier opened",
        "model_calls": 0,
        "governance_writes": 0,
        "proposals": proposals,
    }
    packet["content_sha256"] = hashlib.sha256(canonical(packet)).hexdigest()
    target = ROOT / "proposal-snapshots.json"
    if target.exists():
        raise SystemExit("REFUSING: proposal snapshot already exists")
    target.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"proposals": len(proposals), "content_sha256": packet["content_sha256"]}))


if __name__ == "__main__":
    main()
