#!/usr/bin/env python3
"""Capture the flagship campaign matrix and freeze targeted semantic review pairs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT.parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402


TARGETS = {
    "flagship": [
        "may-as-permission-may-as-possibility-does-may-authorize-an-a",
        "moved-earlier-moved-later-which-way-did-the-meeting-move",
        "rather-not-fine-either-way-would-welcome-you-don-t-have-to-s-2",
    ],
    "modal": [
        "may-not-as-prohibition-may-not-as-possibility-forbidden-or-p",
        "must-as-rule-must-as-inference-does-must-impose-a-requiremen",
        "should-as-rule-should-as-forecast-is-should-a-norm-or-an-exp",
        "able-to-allowed-to-splitting-can-capability-is-not-permissio",
        "will-as-promise-will-as-plan-will-as-forecast-mark-whether-a-2",
    ],
    "operational": [
        "attempt-ensure-say-whether-the-instruction-tolerates-failure",
        "in-parallel-in-sequence-say-whether-listed-actions-may-overl-2",
        "all-or-nothing-keep-successes-say-what-survives-when-part-of-2",
        "this-once-from-now-on-does-this-instruction-apply-to-this-ta",
        "twice-weekly-every-two-weeks-split-biweekly-into-its-two-inc",
    ],
}
PAIRS = [
    ("may-as-permission-may-as-possibility-does-may-authorize-an-a", "may-not-as-prohibition-may-not-as-possibility-forbidden-or-p", "positive and negated modal-force coverage"),
    ("may-as-permission-may-as-possibility-does-may-authorize-an-a", "able-to-allowed-to-splitting-can-capability-is-not-permissio", "permission surface overlap"),
    ("may-not-as-prohibition-may-not-as-possibility-forbidden-or-p", "rather-not-fine-either-way-would-welcome-you-don-t-have-to-s-2", "prohibition versus preference after obligation release"),
    ("must-as-rule-must-as-inference-does-must-impose-a-requiremen", "should-as-rule-should-as-forecast-is-should-a-norm-or-an-exp", "norm strength and epistemic-force boundary"),
    ("should-as-rule-should-as-forecast-is-should-a-norm-or-an-exp", "will-as-promise-will-as-plan-will-as-forecast-mark-whether-a-2", "forecast semantics across modal families"),
    ("may-as-permission-may-as-possibility-does-may-authorize-an-a", "will-as-promise-will-as-plan-will-as-forecast-mark-whether-a-2", "possibility versus future forecast"),
    ("attempt-ensure-say-whether-the-instruction-tolerates-failure", "all-or-nothing-keep-successes-say-what-survives-when-part-of-2", "failure tolerance versus retained effects"),
    ("in-parallel-in-sequence-say-whether-listed-actions-may-overl-2", "all-or-nothing-keep-successes-say-what-survives-when-part-of-2", "execution order versus batch retention"),
    ("this-once-from-now-on-does-this-instruction-apply-to-this-ta", "attempt-ensure-say-whether-the-instruction-tolerates-failure", "directive persistence versus failure tolerance"),
    ("moved-earlier-moved-later-which-way-did-the-meeting-move", "twice-weekly-every-two-weeks-split-biweekly-into-its-two-inc", "reschedule direction versus recurrence cadence"),
    ("this-once-from-now-on-does-this-instruction-apply-to-this-ta", "will-as-promise-will-as-plan-will-as-forecast-mark-whether-a-2", "standing directive versus future-statement force"),
    ("rather-not-fine-either-way-would-welcome-you-don-t-have-to-s-2", "attempt-ensure-say-whether-the-instruction-tolerates-failure", "sender preference versus executor failure tolerance"),
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def status_for(row: dict) -> tuple[str, str]:
    readiness = row.get("evidence_readiness") or {}
    contract = row.get("evidence_contract")
    if row.get("stage") == "proposed":
        return "stage_blocked", "needs additional independent seconds before measurements"
    if contract is None:
        return "contract_blocked", "legacy row has no evidence contract; define carrier and prerequisites before GPU spend"
    if readiness.get("opposing_evidence"):
        return "prerequisite_opposes", "resolve or amend the opposing prerequisite before claim-carrier spend"
    if readiness.get("unresolved_evidence"):
        return "prerequisite_unresolved", "obtain independent different-input settlement before claim-carrier spend"
    missing = readiness.get("missing_evidence") or []
    prereqs = contract.get("prerequisites") or []
    prereq_names = {item if isinstance(item, str) else item.get("metric") for item in prereqs}
    if prereq_names & set(missing):
        return "prerequisite_missing", "run and settle the declared prerequisite before claim-carrier spend"
    if readiness.get("claim_carrier") and set(readiness.get("claim_carrier", [])) & set(missing):
        return "carrier_ready", "claim carrier is the next eligible scientific campaign"
    return "adjudication_needed", "existing evidence needs settlement or contract-level interpretation"


def compact(proposal: dict, group: str) -> dict:
    readiness = proposal.get("evidence_readiness") or {}
    state, next_action = status_for(proposal)
    return {
        "group": group, "slug": proposal["slug"], "public_id": proposal.get("public_id"),
        "title": proposal.get("title"), "stage": proposal.get("stage"),
        "proposer": (proposal.get("proposer") or {}).get("name"),
        "second_weight": proposal.get("second_weight"), "second_threshold": proposal.get("second_threshold"),
        "form": proposal.get("form"), "english_mapping": proposal.get("english_mapping"),
        "evidence_contract": proposal.get("evidence_contract"),
        "evidence_readiness": {
            key: readiness.get(key) for key in ("claim_carrier", "prerequisites", "satisfied", "missing_evidence", "unresolved_evidence", "opposing_evidence", "note")
        },
        "measurements": [
            {key: metric.get(key) for key in ("manifest_hash", "metric", "value", "settlement_state", "confirmed", "is_replication")}
            for metric in proposal.get("measurements", [])
        ],
        "supersedes": proposal.get("supersedes"), "superseded_by": proposal.get("superseded_by"),
        "pipeline_state": state, "next_action": next_action,
    }


def surface(row: dict) -> dict:
    return {
        "slug": row["slug"], "title": row["title"], "form": row.get("form"),
        "english_mapping": row.get("english_mapping"), "stage": row.get("stage"),
        "constraints": {"evidence_contract": row.get("evidence_contract"), "supersedes": row.get("supersedes")},
    }


def main() -> None:
    snapshot_path = ROOT / "live-snapshot.json"
    candidates_path = ROOT / "semantic-candidates.json"
    if snapshot_path.exists() or candidates_path.exists():
        raise SystemExit("REFUSING: frozen outputs already exist")
    client = ainglish_client()
    suggestions = client.suggestions()
    rows = []
    details = {}
    for group, slugs in TARGETS.items():
        for slug in slugs:
            proposal = client.proposal(slug, authenticated=True)
            details[slug] = proposal
            rows.append(compact(proposal, group))
    snapshot = {
        "kind": "dexagon.ainglish.flagship-pipeline-snapshot.v1",
        "suggestions_generated_at": suggestions.get("generated_at"),
        "budgets": suggestions.get("budgets"), "rows": rows,
        "interpretation": "Live readiness snapshot. It does not alter lifecycle or assert that a GPU-blocked proposal lacks merit.",
    }
    snapshot["content_sha256"] = hashlib.sha256(canonical(snapshot)).hexdigest()
    snapshot_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    candidates = []
    for left, right, question in PAIRS:
        payload = {"left": surface(details[left]), "right": surface(details[right]), "review_question": question}
        payload["pair_id"] = hashlib.sha256(canonical(payload)).hexdigest()[:16]
        candidates.append(payload)
    packet = {
        "kind": "dexagon.ainglish.flagship-semantic-candidates.v1", "snapshot_sha256": snapshot["content_sha256"],
        "candidates": candidates,
        "interpretation": "Targeted review routing only; every result must remain review_required and unasserted.",
    }
    packet["content_sha256"] = hashlib.sha256(canonical(packet)).hexdigest()
    candidates_path.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"snapshot": snapshot["content_sha256"], "rows": len(rows), "candidates": len(candidates), "candidate_digest": packet["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
