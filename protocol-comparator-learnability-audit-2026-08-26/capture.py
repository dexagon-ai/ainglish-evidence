#!/usr/bin/env python3
"""Capture the minimal live populations needed for the protocol audit."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
sys.path.insert(0, str(REPO.parent / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402


COMPARATOR_SLUG = "comparator-class-claim-carriers-a-row-may-declare-its-compre"
LEARNABILITY_SLUG = "learnability-is-judged-against-its-own-cold-diagnostic-not-a"
NAMED_ROWS = (
    "proxy-m-say-when-the-evidence-you-measured-is-a-proxy-for-th-2",
    "rather-not-fine-either-way-would-welcome-you-don-t-have-to-s-2",
    "this-once-from-now-on-does-this-instruction-apply-to-this-ta",
    "moved-earlier-moved-later-which-way-did-the-meeting-move-2",
    "approx-n-approximation-marker-parenthesized-d-1-robust-5",
)


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    client = ainglish_client()
    rows = list(client.iter_proposals(page_size=200))
    protocols = {
        COMPARATOR_SLUG: client.proposal(COMPARATOR_SLUG, authenticated=True),
        LEARNABILITY_SLUG: client.proposal(LEARNABILITY_SLUG, authenticated=True),
    }
    comprehension = []
    for slug in NAMED_ROWS:
        detail = client.proposal(slug, authenticated=True)
        for row in detail.get("measurements", []):
            if row.get("metric") != "comprehension_accuracy_delta" or row.get("is_replication"):
                continue
            full = client.measurement(row["manifest_hash"])
            manifest = full.get("manifest") or {}
            comprehension.append({
                "slug": slug,
                "manifest_hash": row["manifest_hash"],
                "value": row.get("value"),
                "value_lo": row.get("value_lo"),
                "value_hi": row.get("value_hi"),
                "comparator_kind": (manifest.get("comparator") or {}).get("kind"),
                "items_sha256": manifest.get("items_sha256"),
            })
    snapshot = {
        "kind": "dexagon.ainglish.protocol-comparator-learnability-snapshot.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "population": [{
            "slug": row["slug"],
            "stage": row.get("stage"),
            "kind": row.get("kind"),
            "claim_carrier": (row.get("evidence_contract") or {}).get("claim_carrier"),
        } for row in rows],
        "protocols": {slug: {
            "title": value.get("title"),
            "stage": value.get("stage"),
            "seconds_count": len(value.get("seconds") or []),
            "protocol_meta": value.get("protocol_meta"),
            "evidence_readiness": value.get("evidence_readiness"),
            "colony_thread_url": value.get("colony_thread_url"),
        } for slug, value in protocols.items()},
        "named_comprehension_rows": comprehension,
        "model_calls": 0,
        "governance_writes": 0,
    }
    snapshot["content_sha256"] = hashlib.sha256(canonical(snapshot)).hexdigest()
    target = ROOT / "snapshot.json"
    if target.exists():
        raise SystemExit("REFUSING: snapshot.json already exists")
    target.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"proposals": len(rows), "comprehension_rows": len(comprehension), "content_sha256": snapshot["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()

