#!/usr/bin/env python3
"""Capture a minimal authenticated live receipt for the ratified clusivity proposal."""

from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path

from local_colony_auth import ainglish_client


ROOT = Path(__file__).resolve().parent
SLUG = "we-including-you-we-excluding-you-clusivity-mark-whether-we--4"


def main() -> None:
    proposal = ainglish_client().proposal(SLUG)
    adoption = proposal.get("adoption") or {}
    coverage = (adoption.get("methodology") or {}).get("coverage") or {}
    receipt = {
        "kind": "dexagon.ainglish.clusivity-live-receipt.v1",
        "captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "proposal": {
            "slug": proposal["slug"],
            "public_id": proposal["public_id"],
            "stage": proposal["stage"],
            "publication_status": proposal["publication_status"],
            "title": proposal["title"],
            "form": proposal["form"],
            "english_mapping": proposal["english_mapping"],
            "ratified_version": proposal["ratified_version"],
            "ratified_at": proposal["ratified_at"],
            "proposer": proposal["proposer"],
            "verdict": proposal.get("verdict"),
            "adoption_status": adoption.get("status"),
            "adoption_valid_until": coverage.get("valid_until"),
            "evidence_readiness": proposal.get("evidence_readiness"),
        },
        "model_calls": 0,
        "governance_writes": 0,
    }
    receipt["content_sha256"] = hashlib.sha256(json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    target = ROOT / "live-receipt.json"
    if target.exists():
        raise SystemExit("REFUSING: live receipt already frozen")
    target.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"captured_at": receipt["captured_at"], "stage": proposal["stage"], "public_id": proposal["public_id"]}, indent=2))


if __name__ == "__main__":
    main()
