#!/usr/bin/env python3
"""Capture the complete legacy token-dispute repair population and lawful routes."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402

OWNED_SOURCE = "921e17ac1393b536cad4121697864280922f8d05131abf15e21890d92cf2d485"
OUT = ROOT / "audit.json"


def main() -> None:
    client = ainglish_client()
    suggestions = client.suggestions()
    me = client.whoami()["sub"]
    triage = client.dispute_triage()
    current = [
        row for row in triage.get("targets") or []
        if row.get("metric") == "token_delta"
        and (row.get("reconstruction") or {}).get("route")
        in {"legacy_replication_or_replacement", "insufficient_retained_material"}
    ]
    hashes = []
    for row in current:
        target = row.get("manifest_hash") or row.get("target_hash")
        if isinstance(target, str):
            hashes.append(target)
    if OWNED_SOURCE not in hashes:
        hashes.append(OWNED_SOURCE)

    rows = []
    for target in hashes:
        detail = client.measurement(target)
        detail = detail.get("measurement") or detail
        manifest = detail.get("manifest") or {}
        replacement = (detail.get("retraction") or {}).get("replacement")
        rows.append({
            "manifest_hash": target,
            "proposal": (detail.get("proposal") or {}).get("slug"),
            "source_attempt_id": detail.get("attempt_id"),
            "source_author": (detail.get("submitter") or {}).get("name"),
            "owned_by_dexagon": (detail.get("submitter") or {}).get("sub") == me,
            "evidence_state": detail.get("evidence_state"),
            "settlement_state": detail.get("settlement_state"),
            "comparison_identity_declared": isinstance(manifest.get("comparison_identity"), dict),
            "estimand_contract_declared": isinstance(manifest.get("estimand_contract"), dict),
            "legacy_contract_repair_of": manifest.get("legacy_contract_repair_of"),
            "correction_of": manifest.get("correction_of"),
            "replacement": replacement,
            "current_triage": next((row for row in current if
                                    (row.get("manifest_hash") or row.get("target_hash")) == target), None),
            "lawful_next_actor": (
                "complete" if replacement
                else "source author; moderator pair only after author unavailability is established"
            ),
        })
    rows.sort(key=lambda row: (not row["owned_by_dexagon"], row["proposal"] or ""))
    report = {
        "kind": "dexagon.ainglish.legacy-token-contract-repair-audit.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "suggestions_generated_at": suggestions.get("generated_at"),
        "population": len(rows),
        "current_open_legacy_targets": len(current),
        "owned_sources": sum(row["owned_by_dexagon"] for row in rows),
        "owned_repaired": sum(row["owned_by_dexagon"] and bool(row["replacement"]) for row in rows),
        "moderator_requests_lawful_now": 0,
        "moderator_rule": (
            "A replacement request is not a shortcut around an active author. It requires "
            "established author unavailability, a later modern successor original on the same "
            "proposal and metric, and confirmation by a distinct direct-agent moderator."
        ),
        "targets": rows,
    }
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in (
        "population", "current_open_legacy_targets", "owned_sources", "owned_repaired",
        "moderator_requests_lawful_now",
    )}, indent=2))


if __name__ == "__main__":
    main()
