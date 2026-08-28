#!/usr/bin/env python3
"""Capture the five live replication targets without opening their item bytes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402


TARGETS = {
    "moved_later": (
        "moved-earlier-moved-later-which-way-did-the-meeting-move-2",
        "3965fddd5d31ea9f9948a113dd549cd84bac61223b61941ec69bde0b0d326635",
    ),
    "moved_earlier": (
        "moved-earlier-moved-later-which-way-did-the-meeting-move-2",
        "b755d553d4c1f890a54833731a841aef8fa40348d2f641b6ec42b3d1f571813c",
    ),
    "may": (
        "may-as-permission-may-as-possibility-does-may-authorize-an-a",
        "dba42c0e48b623502fb370067cf080a1b639a2bb621318400217f1f3d79b3e83",
    ),
    "preference": (
        "rather-not-fine-either-way-would-welcome-you-don-t-have-to-s-2",
        "b661b02842052ced7bc148b50fd4194c6084fbc27f1f70e22e45dd6af88e3d7d",
    ),
    "persistence": (
        "this-once-from-now-on-does-this-instruction-apply-to-this-ta",
        "b4284015daf019e10b2bf4a7643c4341d6576859a57ae40d7c99ae0a1ced546c",
    ),
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    client = ainglish_client()
    suggestions = client.suggestions()
    proposals = {}
    targets = {}
    for name, (slug, target_hash) in TARGETS.items():
        proposal = proposals.setdefault(slug, client.proposal(slug, authenticated=True))
        measurement = client.measurement(target_hash)
        manifest = measurement.get("manifest") or {}
        work = [
            row for row in (proposal.get("evidence_readiness") or {}).get("work_items", [])
            if row.get("metric") == "comprehension_accuracy_delta"
            and target_hash in (row.get("target_hashes") or [])
        ]
        if (
            proposal.get("stage") not in {"seconded", "measured"}
            or proposal.get("superseded_by")
            or measurement.get("metric") != "comprehension_accuracy_delta"
            or measurement.get("settlement_state") != "awaiting"
            or len(work) != 1
            or work[0].get("state") != "replicate_original"
        ):
            raise SystemExit(f"REFUSING: live replication target drift for {name}")
        targets[name] = {
            "slug": slug,
            "proposal_stage": proposal["stage"],
            "manifest_hash": target_hash,
            "metric": measurement["metric"],
            "value": measurement.get("value"),
            "settlement_state": measurement["settlement_state"],
            "replication_count": measurement.get("replication_count"),
            "construct": manifest.get("construct"),
            "comparator": manifest.get("comparator"),
            "item_counts": manifest.get("item_counts"),
            "models": manifest.get("models"),
            "original_panel_family_fragments": ["qwen", "gemma", "ornith"],
            "work_state": work[0]["state"],
        }
    document = {
        "kind": "dexagon.ainglish.settlement-replication-target-snapshot.v1",
        "suggestions_generated_at": suggestions.get("generated_at"),
        "targets": targets,
        "answer_bearing_original_manifests_opened": False,
    }
    document["content_sha256"] = hashlib.sha256(canonical(document)).hexdigest()
    target = ROOT / "snapshot.json"
    target.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "targets": len(targets),
        "content_sha256": document["content_sha256"],
        "suggestions_generated_at": document["suggestions_generated_at"],
    }, indent=2))


if __name__ == "__main__":
    main()
