#!/usr/bin/env python3
"""Verify the three byte-pinned external-reader handoffs offline."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
SPECS = {
    "role_cardinality": {
        "template": "manifest-bound-flagship-carriers-v1-2026-08-27/role-cardinality.template.json",
        "template_sha256": "8e9add0795434540451f98ae5e420b4cc765f59eea6f934fad3b327a806990f7",
        "items_sha256": "ebbed57d556ef537535c8d0ec9f845ed2e7bf0846a14070bd79858dd5b8e08a2",
        "scientific": 480, "calibration": 12, "strata": 48, "replicates_hash": None,
    },
    "repeat_restore": {
        "template": "manifest-bound-flagship-carriers-v1-2026-08-27/repeat-restore.template.json",
        "template_sha256": "788f8ee5fc4e6255280b3a7f24fc0bb38518d34404defad35523fe472812c5e0",
        "items_sha256": "9581fd995419464b3407566bb74d727b0bfd71885e1887083452f120a4d03fdf",
        "scientific": 256, "calibration": 8, "strata": 16, "replicates_hash": None,
    },
    "persistence_replication": {
        "template": "manifest-bound-settlement-replications-v1-2026-08-28/persistence.template.json",
        "template_sha256": "a9faee9d7004e1d068863f2755905de9826ae9d00ebf45517a3f04c0f55ef874",
        "items_sha256": "2b5f59fc9bbdd358380fa744ed01332abcb1b5c195088ab4ac0176cd2fee511b",
        "scientific": 140, "calibration": 8, "strata": 1,
        "replicates_hash": "b4284015daf019e10b2bf4a7643c4341d6576859a57ae40d7c99ae0a1ced546c",
    },
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    result = {}
    for name, spec in SPECS.items():
        path = REPO / spec["template"]
        template = json.loads(path.read_text(encoding="utf-8"))
        unsigned = dict(template)
        seal = unsigned.pop("content_sha256")
        assert hashlib.sha256(canonical(unsigned)).hexdigest() == seal == spec["template_sha256"]
        artifact = template["items_artifact"]
        items_packet = json.loads((path.parent / artifact["file"]).read_text(encoding="utf-8"))
        assert items_packet["items"] == template["items"]
        assert hashlib.sha256(canonical(template["items"])).hexdigest() == artifact["items_sha256"] == spec["items_sha256"]
        assert artifact["published_url"].startswith("https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/")
        scientific = sum(not row.get("calibration") for row in template["items"])
        calibration = sum(bool(row.get("calibration")) for row in template["items"])
        assert (scientific, calibration, len(template["settlement_strata"])) == (spec["scientific"], spec["calibration"], spec["strata"])
        assert template.get("replicates_hash") == spec["replicates_hash"]
        if name == "persistence_replication":
            forbidden = {value.casefold() for value in template["reader_independence"]["forbidden_lineage_fragments"]}
            assert forbidden == {"qwen", "gemma", "ornith"}
        result[name] = {
            "template_sha256": seal,
            "items_sha256": artifact["items_sha256"],
            "published_item_binding": True,
            "scientific": scientific,
            "calibration": calibration,
            "strata": len(template["settlement_strata"]),
        }
    print(json.dumps({
        "status": "ready_when_external_panel_qualifies",
        "handoffs": result,
        "model_calls": 0, "api_calls": 0, "governance_writes": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
