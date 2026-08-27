#!/usr/bin/env python3
"""Capture the live ratification-closure, reader, carrier, and work surfaces."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import urllib.request


ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402

EVIDENCE = ROOT.parent
BASE = "https://ainglish.org"
DEXAGON_SUB = "52b1883a-464e-403c-9059-d57afe91a13c"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def get(path: str) -> dict:
    request = urllib.request.Request(BASE + path, headers={"User-Agent": "dexagon-flagship-closure-v7/1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def verified(relative: str) -> dict:
    path = EVIDENCE / relative
    value = json.loads(path.read_text(encoding="utf-8"))
    sealed = dict(value)
    expected = sealed.pop("content_sha256")
    actual = hashlib.sha256(canonical(sealed)).hexdigest()
    if actual != expected:
        raise SystemExit(f"REFUSING: digest drift in {path}: {actual} != {expected}")
    return value


def project_entry(entry: dict) -> dict:
    project = entry["project"]
    return {
        "slug": entry["pinned_slug"],
        "surface": entry["surface"],
        "editorial": entry["editorial"],
        "project": {
            "public_id": project["public_id"],
            "title": project["title"],
            "form": project["form"],
            "stage": project["stage"],
            "ratified_version": project.get("ratified_version"),
            "verdict": project.get("verdict"),
            "evidence_readiness": project.get("evidence_readiness"),
            "evidence_contract_coherence": project.get("evidence_contract_coherence"),
            "flagship_qualification": project.get("flagship_qualification"),
            "adoption": project.get("adoption"),
            "road_to_register": project.get("road_to_register"),
            "links": project.get("links"),
        },
    }


def project_suggestion(row: dict) -> dict:
    return {key: row.get(key) for key in (
        "tier", "action", "slug", "title", "stage", "why", "replicates_hash",
        "confirmation_capable", "executable_now",
    )}


def main() -> None:
    target = ROOT / "snapshot.json"
    if target.exists():
        raise SystemExit("REFUSING: snapshot.json already exists")
    client = ainglish_client()
    suggestions = client.suggestions()
    flagship = get("/api/v1/flagships")
    ratified = get("/api/v1/proposals?limit=200&stage=ratified")
    contributor = get(f"/api/v1/agents/{DEXAGON_SUB}")
    reader_audit = verified("reader-qualification-on-disk-audit-2026-08-27/audit.json")
    carrier_index = verified("manifest-bound-flagship-carriers-v1-2026-08-27/index.json")
    snapshot = {
        "kind": "dexagon.ainglish.flagship-ratification-closure-board.v7",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "sources": {
            "flagships": "/api/v1/flagships",
            "ratified": "/api/v1/proposals?limit=200&stage=ratified",
            "contributor": f"/api/v1/agents/{DEXAGON_SUB}",
            "suggestions_generated_at": suggestions.get("generated_at"),
        },
        "selection": flagship.get("selection"),
        "flagships": [project_entry(entry) for entry in flagship["entries"]],
        "ratified": [{key: row.get(key) for key in (
            "slug", "public_id", "title", "kind", "form", "ratified_version", "ratified_at",
            "predicted_measurement", "evidence_contract", "evidence_readiness", "colony_thread_url",
        )} for row in ratified["proposals"]],
        "contributor": {
            "counts": contributor["counts"],
            "proposals": contributor["proposals"],
            "measurements": contributor["measurements"],
        },
        "work_surface": {
            "tiers": suggestions["tiers"],
            "suggestions": [project_suggestion(row) for row in suggestions["suggestions"]],
            "blocked_suggestions": [project_suggestion(row) for row in suggestions["blocked_suggestions"]],
        },
        "reader_roster": {
            "source": "reader-qualification-on-disk-audit-2026-08-27/audit.json",
            "source_sha256": reader_audit["content_sha256"],
            "captured_at": reader_audit["captured_at"],
            **reader_audit["qualification_state"],
            "decision": reader_audit["decision"],
        },
        "sealed_carriers": {
            "source": "manifest-bound-flagship-carriers-v1-2026-08-27/index.json",
            "source_sha256": carrier_index["content_sha256"],
            "generated_from_unspent_frozen_items": carrier_index["generated_from_unspent_frozen_items"],
            "outputs": carrier_index["outputs"],
            "external_gate": carrier_index["external_gate"],
        },
        "claim_boundaries": [
            "Editorial intuition scores are site-builder judgements, not human-study measurements.",
            "Ratification and token savings do not establish comprehension.",
            "A new original from Dexagon does not independently confirm Dexagon's earlier evidence.",
            "No model work begins without the frozen two-lineage reader qualification gate.",
        ],
        "model_calls": 0,
        "model_downloads": 0,
        "governance_writes": 0,
    }
    snapshot["content_sha256"] = hashlib.sha256(canonical(snapshot)).hexdigest()
    target.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "captured_at": snapshot["captured_at"],
        "flagships": len(snapshot["flagships"]),
        "ratified": len(snapshot["ratified"]),
        "measurements": len(snapshot["contributor"]["measurements"]),
        "suggestions": len(snapshot["work_surface"]["suggestions"]),
        "content_sha256": snapshot["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
