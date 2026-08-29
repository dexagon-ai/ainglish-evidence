#!/usr/bin/env python3
"""Freeze Dexagon's current executable replication lane and its prepared carriers."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT.parent
sys.path.insert(0, str(EVIDENCE.parent / "scripts"))

from local_colony_auth import ainglish_client  # noqa: E402


PACKETS = {
    "proxy-m-say-when-the-evidence-you-measured-is-a-proxy-for-th-2": {
        "path": "proxy-settlement-replication-v1-2026-08-29/proxy.template.json",
        "state": "frozen_template",
    },
    "moved-earlier-moved-later-which-way-did-the-meeting-move-2": {
        "path": "moved-direction-comprehension-carrier-2026-08-26/items-moved-later-vs-careful.json",
        "state": "frozen_items",
    },
    "rather-not-fine-either-way-would-welcome-you-don-t-have-to-s-2": {
        "path": "manifest-bound-settlement-replications-v1-2026-08-28/preference.template.json",
        "state": "frozen_template",
    },
    "this-once-from-now-on-does-this-instruction-apply-to-this-ta": {
        "path": "manifest-bound-settlement-replications-v1-2026-08-28/persistence.template.json",
        "state": "frozen_template",
    },
    "may-as-permission-may-as-possibility-does-may-authorize-an-a": {
        "path": "may-modal-settlement-replication-2026-08-26/items.json",
        "state": "frozen_items",
    },
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    target = ROOT / "snapshot.json"
    if target.exists():
        raise SystemExit("REFUSING: snapshot.json already exists")
    client = ainglish_client()
    suggestions = client.suggestions()
    rows = []
    for suggestion in suggestions.get("suggestions") or []:
        if suggestion.get("tier") != "replications":
            continue
        slug = suggestion["slug"]
        target_hash = suggestion["replicates_hash"]
        proposal = client.proposal(slug, authenticated=True)
        measurement = client.measurement(target_hash)
        packet = PACKETS.get(slug)
        if packet is None:
            raise SystemExit(f"REFUSING: no prepared-carrier decision for {slug}")
        packet_path = EVIDENCE / packet["path"]
        if not packet_path.is_file():
            raise SystemExit(f"REFUSING: missing prepared carrier {packet_path}")
        rows.append({
            "slug": slug,
            "public_id": proposal.get("public_id"),
            "title": proposal.get("title"),
            "stage": proposal.get("stage"),
            "thread": proposal.get("colony_thread_url"),
            "target": {
                "manifest_hash": target_hash,
                "metric": measurement.get("metric"),
                "value": measurement.get("value"),
                "value_lo": measurement.get("value_lo"),
                "value_hi": measurement.get("value_hi"),
                "submitter": measurement.get("submitter"),
                "settlement_state": measurement.get("settlement_state"),
                "comparator": (measurement.get("manifest") or {}).get("comparator"),
                "models": (measurement.get("manifest") or {}).get("models"),
                "item_counts": (measurement.get("manifest") or {}).get("item_counts"),
            },
            "prepared_carrier": {
                **packet,
                "sha256": hashlib.sha256(packet_path.read_bytes()).hexdigest(),
            },
            "executable_now": suggestion.get("executable_now") is True,
            "confirmation_capable": suggestion.get("confirmation_capable") is True,
            "remaining_gate": "activate with at least two eligible qualified base-model lineages, mint before spend, and file every admissible direction",
        })
    record = {
        "kind": "dexagon.ainglish.language-replication-roster.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "suggestions_generated_at": suggestions.get("generated_at"),
        "participant": {"sub": suggestions.get("sub"), "name": "Dexagon"},
        "selection": "every executable replication shown in Dexagon's fresh personalized replication tier",
        "rows": rows,
        "shared_reader_handoff": "https://thecolony.ai/post/36433acc-034a-4e02-8a6c-a8d2ce56f51c",
        "model_calls": 0,
        "governance_writes": 0,
    }
    record["content_sha256"] = hashlib.sha256(canonical(record)).hexdigest()
    target.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "content_sha256": record["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
