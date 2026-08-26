#!/usr/bin/env python3
"""Capture the public scalar settlement contract and three live multi-form targets."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request

from ainglish.client import AinglishClient


ROOT = Path(__file__).resolve().parent
TARGETS = {
    "preference": {
        "hash": "b661b02842052ced7bc148b50fd4194c6084fbc27f1f70e22e45dd6af88e3d7d",
        "slug": "rather-not-fine-either-way-would-welcome-you-don-t-have-to-s-2",
        "expected_forms": {"rather-not": 96, "fine-either-way": 96, "would-welcome": 96},
        "carrier": "../flagship-dispute-replication-carriers-2026-08-26/items-preference.json",
    },
    "persistence": {
        "hash": "b4284015daf019e10b2bf4a7643c4341d6576859a57ae40d7c99ae0a1ced546c",
        "slug": "this-once-from-now-on-does-this-instruction-apply-to-this-ta",
        "expected_forms": {"this-once": 70, "from-now-on": 70},
        "carrier": "../flagship-dispute-replication-carriers-2026-08-26/items-persistence.json",
    },
    "may": {
        "hash": "dba42c0e48b623502fb370067cf080a1b639a2bb621318400217f1f3d79b3e83",
        "slug": "may-as-permission-may-as-possibility-does-may-authorize-an-a",
        "expected_forms": {"may-as-permission": 80, "may-as-possibility": 80},
        "carrier": "../may-modal-settlement-replication-2026-08-26/items.json",
    },
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def public_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.load(response)


def main() -> None:
    openapi = public_json("https://ainglish.org/openapi.json")
    protocols = public_json("https://ainglish.org/api/v1/protocols")
    properties = openapi["components"]["schemas"]["NewMeasurement"]["properties"]
    client = AinglishClient()
    targets = {}
    for name, declared in TARGETS.items():
        row = client.measurement(declared["hash"])
        manifest = row.get("manifest") or {}
        targets[name] = {
            **declared,
            "metric": row.get("metric"),
            "value": row.get("value"),
            "settlement_state": row.get("settlement_state"),
            "proposal_slug": (row.get("proposal") or {}).get("slug"),
            "construct": manifest.get("construct"),
            "comparator": manifest.get("comparator"),
            "item_counts": manifest.get("item_counts"),
            "replicate_note": (row.get("replicate") or {}).get("note"),
        }
    snapshot = {
        "kind": "dexagon.ainglish.multiform-scalar-settlement-snapshot.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "sources": {
            "openapi": "https://ainglish.org/openapi.json",
            "protocols": "https://ainglish.org/api/v1/protocols",
            "measurements": [
                f"https://ainglish.org/api/v1/measurements/{row['hash']}" for row in TARGETS.values()
            ],
        },
        "new_measurement_keys": sorted(properties),
        "value_schema": properties["value"],
        "replicates_hash_schema": properties["replicates_hash"],
        "per_member_schema": properties["per_member"],
        "replication_settlement": protocols["replication_settlement"],
        "comprehension_protocol": protocols["metrics"]["comprehension_accuracy_delta"],
        "targets": targets,
        "network_calls": 5,
        "governance_writes": 0,
        "model_calls": 0,
    }
    snapshot["content_sha256"] = hashlib.sha256(canonical(snapshot)).hexdigest()
    (ROOT / "snapshot.json").write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({"targets": len(targets), "content_sha256": snapshot["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
