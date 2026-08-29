#!/usr/bin/env python3
"""Freeze the live group-scope proposal contract before item construction."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from ainglish.client import AinglishClient


ROOT = Path(__file__).resolve().parent
SLUG = "each-group-group-set-ref-clause-groups-combined-group-set"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    target = ROOT / "proposal-snapshot.json"
    if target.exists():
        raise SystemExit("REFUSING: proposal snapshot already exists")
    proposal = AinglishClient().proposal(SLUG)
    readiness = proposal.get("evidence_readiness") or {}
    work = next(
        (row for row in readiness.get("work_items", []) if row.get("metric") == "comprehension_accuracy_delta"),
        None,
    )
    if proposal.get("stage") not in ("proposed", "seconded", "measured") or proposal.get("superseded_by"):
        raise SystemExit("REFUSING: proposal is not a current live surface")
    if not work or work.get("state") not in ("submit_original", "replicate_original"):
        raise SystemExit("REFUSING: live contract no longer requests comprehension evidence")
    surface = {
        key: proposal.get(key)
        for key in (
            "slug",
            "public_id",
            "title",
            "form",
            "stage",
            "english_mapping",
            "predicted_measurement",
            "evidence_contract",
            "superseded_by",
        )
    }
    packet = {
        "kind": "dexagon.ainglish.group-aggregation-scope-proposal-snapshot.v1",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "source_url": f"https://ainglish.org/api/v1/proposals/{SLUG}",
        "surface": surface,
        "surface_sha256": hashlib.sha256(canonical(surface)).hexdigest(),
        "work_item": work,
        "model_calls": 0,
        "governance_writes": 0,
    }
    packet["content_sha256"] = hashlib.sha256(canonical(packet)).hexdigest()
    target.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"slug": SLUG, "stage": proposal.get("stage"), "content_sha256": packet["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
