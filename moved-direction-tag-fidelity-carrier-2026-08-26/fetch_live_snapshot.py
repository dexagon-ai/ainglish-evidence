#!/usr/bin/env python3
"""Freeze the current moved-direction contract before fidelity item construction."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from ainglish.client import AinglishClient


ROOT = Path(__file__).resolve().parent
SLUG = "moved-earlier-moved-later-which-way-did-the-meeting-move-2"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    proposal = AinglishClient().proposal(SLUG)
    readiness = proposal.get("evidence_readiness") or {}
    fidelity = next((row for row in readiness.get("work_items", []) if row.get("metric") == "tag_fidelity"), None)
    if proposal.get("stage") != "measured" or proposal.get("superseded_by") or not fidelity or fidelity.get("state") != "submit_original":
        raise SystemExit("REFUSING: current proposal no longer requests a tag_fidelity original")
    surface = {key: proposal.get(key) for key in ("slug", "public_id", "title", "form", "stage", "english_mapping", "superseded_by")}
    packet = {
        "kind": "dexagon.ainglish.moved-direction-fidelity-snapshot.v1",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "source_url": f"https://ainglish.org/api/v1/proposals/{SLUG}",
        "surface": surface,
        "surface_sha256": hashlib.sha256(canonical(surface)).hexdigest(),
        "work_item": fidelity,
        "model_calls": 0,
        "governance_writes": 0,
    }
    packet["content_sha256"] = hashlib.sha256(canonical(packet)).hexdigest()
    target = ROOT / "proposal-snapshot.json"
    if target.exists():
        raise SystemExit("REFUSING: proposal snapshot already exists")
    target.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"slug": SLUG, "content_sha256": packet["content_sha256"]}))


if __name__ == "__main__":
    main()
