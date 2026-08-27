#!/usr/bin/env python3
"""Capture a live flagship-quality matrix without governance writes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from local_colony_auth import ainglish_client


ROOT = Path(__file__).resolve().parent
EDITORIAL = {
    "we-including-you-we-excluding-you-clusivity-mark-whether-we--4": ("we-including-you / we-excluding-you", [1, 1, 1, 1, 1]),
    "you-one-you-all-say-whether-you-addresses-one-recipient-or-t": ("you-one / you-all", [1, 1, 1, 1, 1]),
    "fact-not-known-choice-not-made-distinguish-missing-evidence-": ("fact-not-known / choice-not-made", [1, 1, 1, 1, 1]),
    "no-delegation-one-hop-delegation-allowed-state-whether-a-tas": ("no-delegation / one-hop-delegation-allowed", [1, 1, 1, 1, 1]),
    "moved-earlier-moved-later-which-way-did-the-meeting-move-2": ("moved-earlier / moved-later", [1, 1, 1, 1, 1]),
    "among-others-and-no-others-is-the-list-the-whole-list-2": ("among-others / and-no-others", [1, 1, 1, 1, 1]),
    "one-or-more-role-exactly-one-role-does-a-reviewer-require-at": ("one-or-more(<role>) / exactly-one(<role>)", [1, 1, 1, 1, 1]),
    "repeat-event-restore-state-did-again-repeat-the-action-or-on-4": ("repeat-event / restore-state(<S>)", [1, 1, 0, 1, 1]),
}
CHECKS = ["five_second_contrast", "familiar_ambiguity", "symmetric_forms", "visible_payoff", "clean_seam"]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    client = ainglish_client()
    rows = []
    for slug, (form, checks) in EDITORIAL.items():
        envelope = client.proposal(slug)
        proposal = envelope.get("proposal", envelope)
        measurements = proposal.get("measurements", envelope.get("measurements", []))
        confirmed_comprehension = [
            row for row in measurements
            if row.get("metric") == "comprehension_accuracy_delta" and row.get("confirmed")
        ]
        contract = proposal.get("evidence_contract") or {}
        claim_carriers = contract.get("claim_carrier", [])
        prerequisites = contract.get("prerequisites", [])
        declared_complete = bool(proposal.get("evidence_contract_status", {}).get("complete"))
        stage = proposal.get("stage")
        editorial_pass = all(checks)
        rows.append({
            "slug": proposal["slug"],
            "form": form,
            "stage": stage,
            "editorial_checks": dict(zip(CHECKS, map(bool, checks))),
            "editorial_score": sum(checks),
            "deterministic_ratifiable": bool((proposal.get("deterministic") or {}).get("ratifiable")),
            "evidence_contract": {
                "claim_carrier": claim_carriers,
                "prerequisites": prerequisites,
                "served_complete": declared_complete,
            },
            "confirmed_comprehension_rows": len(confirmed_comprehension),
            "form_safe_settlement": all(row.get("stratum_results") for row in confirmed_comprehension) if confirmed_comprehension else False,
            "publication_lane": (
                "ratified-showcase" if stage == "ratified" and editorial_pass
                else "pipeline-preview" if editorial_pass
                else "research-preview"
            ),
            "do_not_say": (
                "Do not call this a ratified entry." if stage != "ratified"
                else "Do not call editorial intuitiveness experimentally proven comprehension."
            ),
        })
    snapshot = {
        "kind": "dexagon.ainglish.flagship-quality-matrix.v4",
        "captured_at": "2026-08-27T07:55:00Z",
        "checks": CHECKS,
        "rows": rows,
        "claim_boundary": "Editorial quality, governance stage, evidence qualification, form-safe settlement, and publication lane are separate facts.",
        "network_writes": 0,
        "governance_writes": 0,
    }
    snapshot["content_sha256"] = hashlib.sha256(canonical(snapshot)).hexdigest()
    (ROOT / "matrix.json").write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(snapshot, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
