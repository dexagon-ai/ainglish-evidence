#!/usr/bin/env python3
"""Build a fresh 32-pair price-axis recertification packet."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent

ACTIONS = [
    "approve the release", "choose the refund amount", "waive the retention rule",
    "publish the incident attribution", "accept the medical-risk exception",
    "override the spending limit", "disclose the customer record", "sign the vendor waiver",
    "select the disciplinary outcome", "authorize the account closure", "resolve the authorship dispute",
    "change the safety threshold", "grant the data-access exception", "settle the licensing interpretation",
    "choose the public response", "approve the irreversible deletion", "decide the conflict-of-interest remedy",
    "release the embargoed report", "set the compensation adjustment", "waive the independent review",
    "choose the accessibility exception", "approve the biometric-data use", "resolve the election tie",
    "accept the hazardous-material route", "decide the child-safety escalation", "override the audit finding",
    "select the layoff criterion", "approve the research-subject exception", "choose the legal jurisdiction",
    "resolve the whistleblower disclosure", "authorize the emergency shutdown", "accept the sanctions exception",
]

REASONS = [
    "the policy exception is unresolved", "the amount requires delegated authority",
    "the contract permits no automated waiver", "the evidence conflicts",
    "the clinical tradeoff requires accountable judgment", "the budget owner has not decided",
    "consent is ambiguous", "the liability allocation is disputed", "the record is contested",
    "identity verification is incomplete", "the contributors disagree", "the acceptable risk is a value choice",
    "the access owner must decide", "the licence terms conflict", "the response affects named people",
    "the deletion cannot be reversed", "the reviewer has a disclosed conflict", "the embargo owner must consent",
    "the adjustment depends on human discretion", "the rule requires an independent approver",
    "the accommodation needs individual judgment", "the consent scope is disputed", "the governing rule names no tiebreaker",
    "the safety tradeoff needs accountable approval", "the report indicates possible harm",
    "the auditor and operator disagree", "the criterion is a policy choice", "the ethics board must decide",
    "the contract names multiple forums", "the disclosure risk cannot be resolved mechanically",
    "the physical-safety owner must decide", "the applicable restriction is contested",
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    if len(ACTIONS) != 32 or len(REASONS) != 32:
        raise SystemExit("REFUSING: expected exactly 32 actions and reasons")
    rows = []
    for index, (action, reason) in enumerate(zip(ACTIONS, REASONS, strict=True), 1):
        rows.append({
            "item_id": f"hnr-{index:02d}",
            "ainglish": f"{action.capitalize()} human_needed({reason}).",
            "english": f"The agent must not {action}; a human must decide because {reason}.",
            "reason": reason,
        })
    if len({(row["ainglish"], row["english"]) for row in rows}) != 32:
        raise SystemExit("REFUSING: pairs are not unique")
    packet = {
        "kind": "ainglish.human-needed-token-recertification-items.v1",
        "proposal_slug": "human-needed-why-the-escalation-pin-when-a-human-must-decide-2",
        "metric": "token_delta",
        "comparison": "registered marker versus full careful English carrying both human-decision and agent-must-not-resolve semantics",
        "acceptance": {"least_favourable_mean": "< 0"},
        "evidentiary_limit": "price-axis recertification only; token count is not comprehension evidence",
        "test_set": rows,
    }
    packet["items_sha256"] = hashlib.sha256(canonical(rows)).hexdigest()
    packet["content_sha256"] = hashlib.sha256(canonical(packet)).hexdigest()
    target = ROOT / "items.json"
    if target.exists():
        raise SystemExit("REFUSING: items.json already exists")
    target.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"pairs": len(rows), "items_sha256": packet["items_sha256"], "content_sha256": packet["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
