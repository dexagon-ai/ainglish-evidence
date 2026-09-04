#!/usr/bin/env python3
"""Freeze a fresh token replication without loading a tokenizer."""

from __future__ import annotations

import json
from pathlib import Path

from ainglish.client import AinglishClient, manifest_commitment
from ainglish.token_measurement import prepare


ROOT = Path(__file__).resolve().parent
SLUG = "dispatched-transport-delivered-witness-say-which-transit-eve"
TARGET = "f4ad52b176c68b733641eb90d518e8c705aa9537626c9afad83151e806df97f1"
MODELS = ["cl100k_base", "o200k_base", "p50k_base"]

PAIRS = [
    (
        "I handed the incident summary to the Matrix transport at 18:20 UTC; I have no evidence that the recipient received it.",
        "dispatched(matrix): the incident summary at 18:20 UTC.",
    ),
    (
        "Our service handed the invoice to the print-mail provider; we do not know whether it arrived at the customer.",
        "dispatched(print-mail-provider): the customer invoice.",
    ),
    (
        "I handed the job result to the callback transport; its acceptance identifier does not show arrival at the recipient.",
        "dispatched(callback-transport): the job result.",
    ),
    (
        "The worker handed the alert to the pager gateway; nobody on the recipient side has witnessed its arrival.",
        "dispatched(pager-gateway): the alert.",
    ),
    (
        "I handed the patch archive to the SFTP transport; I have no evidence that it reached the maintainer.",
        "dispatched(sftp-transport): the patch archive.",
    ),
    (
        "Our relay accepted custody of the audit export; we do not know whether the destination received it.",
        "dispatched(our-relay): the audit export.",
    ),
    (
        "I handed the notification to the SMS gateway; its provider receipt confirms custody but not recipient arrival.",
        "dispatched(sms-gateway): the notification.",
    ),
    (
        "The publisher handed the event to the MQTT broker; no subscriber-side receipt is available.",
        "dispatched(mqtt-broker): the event.",
    ),
    (
        "The recipient's mail server witnessed the compliance report arrive in the recipient mailbox.",
        "delivered(recipient-mail-server): the compliance report.",
    ),
    (
        "The destination webhook witnessed the signed payload arrive at the recipient endpoint.",
        "delivered(destination-webhook): the signed payload.",
    ),
    (
        "The recipient's inbox agent witnessed the scheduling notice arrive in the recipient inbox.",
        "delivered(recipient-inbox-agent): the scheduling notice.",
    ),
    (
        "The receiving SFTP server witnessed the backup archive arrive at the recipient account.",
        "delivered(receiving-sftp-server): the backup archive.",
    ),
    (
        "The customer portal witnessed the refund statement arrive in the customer's document store.",
        "delivered(customer-portal): the refund statement.",
    ),
    (
        "The downstream queue consumer witnessed the order event arrive in the recipient queue.",
        "delivered(downstream-queue-consumer): the order event.",
    ),
    (
        "The partner's API witnessed the revocation notice arrive at the partner endpoint.",
        "delivered(partner-api): the revocation notice.",
    ),
    (
        "The recipient witnessed the contract copy arrive and confirmed that arrival to us.",
        "delivered(recipient): the contract copy.",
    ),
]


def pair_set(manifest: dict) -> set[tuple[str, str]]:
    return {
        (row.get("english"), row.get("ainglish"))
        for row in manifest.get("test_set") or []
        if isinstance(row, dict)
    }


def main() -> None:
    client = AinglishClient()
    target_envelope = client.measurement(TARGET)
    target = target_envelope.get("measurement", target_envelope)
    target_manifest = target.get("manifest") or {}
    if manifest_commitment(target_manifest) != TARGET:
        raise SystemExit("REFUSING: target manifest no longer hashes to the named target")
    if target.get("metric") != "token_delta" or target_manifest.get("models") != MODELS:
        raise SystemExit("REFUSING: target metric or tokenizer roster changed")

    proposal = client.proposal(SLUG)
    fresh = set(PAIRS)
    if len(fresh) != 16:
        raise SystemExit("REFUSING: expected 16 unique complete pairs")
    prior: set[tuple[str, str]] = set()
    for row in proposal.get("measurements") or []:
        manifest = row.get("manifest")
        if not isinstance(manifest, dict) and row.get("manifest_hash"):
            detail = client.measurement(row["manifest_hash"])
            manifest = detail.get("measurement", detail).get("manifest")
        if isinstance(manifest, dict):
            prior |= pair_set(manifest)
    if fresh & prior:
        raise SystemExit("REFUSING: fresh complete-pair overlap detected")

    manifest = {
        "kind": "dexagon.ainglish.dispatched-delivered-token-replication.v1",
        "metric": "token_delta",
        "construct": "dispatched / delivered",
        "models": MODELS,
        "test_set": [
            {"english": english, "ainglish": ainglish}
            for english, ainglish in PAIRS
        ],
        "estimand_contract": {
            "kind": "ainglish.estimand-shadow.v1",
            "unit_span": "complete message",
            "contrast": "Ainglish form versus its complete careful-English meaning",
            "population": "16 frozen fresh transit-status reports balanced 8/8 across dispatched and delivered",
            "aggregation": {
                "reducer": "least_favourable",
                "rule": "equal pair mean, then maximum tokenizer mean (least-favourable)",
            },
            "governance_effect": "report_only",
        },
        "replicates_hash": TARGET,
        "method": "Canonical SDK two-phase token runner; freeze before tokenizer loading and file every finite direction once.",
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "path": "dispatched-delivered-token-replication-v1-2026-09-04/build.py",
        },
        "evidentiary_limit": "Present tokenizer cost under complete semantic comparators; not comprehension, adoption, or future Ainglish-aware tokenizer cost.",
    }
    spec = {"manifest": manifest, "replication_target_manifest": target_manifest}
    plan = prepare(spec)
    (ROOT / "spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "target": TARGET,
        "target_value": target.get("value"),
        "fresh_pair_count": len(fresh),
        "prior_pair_count": len(prior),
        "overlap": 0,
        "manifest_commitment": plan["manifest_commitment"],
    }, indent=2))


if __name__ == "__main__":
    main()
