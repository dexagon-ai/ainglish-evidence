#!/usr/bin/env python3
"""Freeze a fresh four-stratum only-focus replication without tokenizer exposure."""

from __future__ import annotations

import json
from pathlib import Path

from ainglish.client import AinglishClient, manifest_commitment
from ainglish.token_measurement import prepare


ROOT = Path(__file__).resolve().parent
SLUG = "only-focus-the-weld-spans-the-whole-focused-constituent-2"
TARGET = "4ef4767497f0c887161b25e2b12306dd5eaad4641ab1d16c0be0a239e3ef0fd1"
MODELS = ["cl100k_base", "o200k_base"]

ROWS = {
    "subject": [
        ("only-Soraya approved the exception.", "only Soraya approved the exception."),
        ("only-the-night-auditor opened the archive.", "only the night auditor opened the archive."),
        ("only-four-reviewers signed the decision.", "only four reviewers signed the decision."),
        ("only-our-backup-operator restored the index.", "only our backup operator restored the index."),
        ("only-the-privacy-lead viewed the export.", "only the privacy lead viewed the export."),
        ("only-Kaito acknowledged the warning.", "only Kaito acknowledged the warning."),
        ("only-the-forensics-expert copied the image.", "only the forensics expert copied the image."),
        ("only-Amina received the private appendix.", "only Amina received the private appendix."),
    ],
    "verb": [
        ("I only-renamed the branch.", "I only renamed the branch."),
        ("we only-indexed the new records.", "we only indexed the new records."),
        ("the custodian only-unsealed the envelope.", "the custodian only unsealed the envelope."),
        ("the operator only-restarted the replica.", "the operator only restarted the replica."),
        ("Lina only-tagged the candidate.", "Lina only tagged the candidate."),
        ("the assistant only-summarized the finding.", "the assistant only summarized the finding."),
        ("the clerk only-archived the receipt.", "the clerk only archived the receipt."),
        ("the analyst only-reweighted the sample.", "the analyst only reweighted the sample."),
    ],
    "object-nominal": [
        ("the migration changed only-the-staging-database.", "the migration changed only the staging database."),
        ("we retained only-five-log-shards.", "we retained only five log shards."),
        ("the switch affected only-the-blue-environment.", "the switch affected only the blue environment."),
        ("I revoked only-our-expired-certificate.", "I revoked only our expired certificate."),
        ("the reviewer inspected only-the-archived-ledger.", "the reviewer inspected only the archived ledger."),
        ("the correction replaced only-the-last-two-rows.", "the correction replaced only the last two rows."),
        ("the repair mounted only-the-recovery-partition.", "the repair mounted only the recovery partition."),
        ("the suite regenerated only-six-test-fixtures.", "the suite regenerated only six test fixtures."),
    ],
    "adjunct": [
        ("the release advances only-after-validation.", "the release advances only after validation."),
        ("the fault appears only-under-load.", "the fault appears only under load."),
        ("the exporter reads only-from-the-mirror.", "the exporter reads only from the mirror."),
        ("the override exists only-for-emergency-use.", "the override exists only for emergency use."),
        ("the seal opens only-with-a-witness.", "the seal opens only with a witness."),
        ("the temporary route remains only-until-sunset.", "the temporary route remains only until sunset."),
        ("the console is staffed only-during-business-hours.", "the console is staffed only during business hours."),
        ("the heartbeat travels only-on-the-secondary-link.", "the heartbeat travels only on the secondary link."),
    ],
}


def pair_set(manifest: dict) -> set[tuple[str, str]]:
    return {
        (row.get("english"), row.get("ainglish"))
        for row in manifest.get("test_set") or []
        if isinstance(row, dict)
    }


def main() -> None:
    client = AinglishClient()
    envelope = client.measurement(TARGET)
    target = envelope.get("measurement", envelope)
    target_manifest = target.get("manifest") or {}
    if manifest_commitment(target_manifest) != TARGET:
        raise SystemExit("REFUSING: target manifest commitment changed")
    if target.get("metric") != "token_delta" or target_manifest.get("models") != MODELS:
        raise SystemExit("REFUSING: target metric or tokenizer roster changed")
    if [row.get("id") for row in target_manifest.get("settlement_strata") or []] != list(ROWS):
        raise SystemExit("REFUSING: target settlement strata changed")

    test_set = [
        {"stratum": stratum, "ainglish": ainglish, "english": english}
        for stratum, pairs in ROWS.items()
        for ainglish, english in pairs
    ]
    fresh = {(row["english"], row["ainglish"]) for row in test_set}
    if len(test_set) != 32 or len(fresh) != 32:
        raise SystemExit("REFUSING: expected 32 unique complete pairs")
    proposal = client.proposal(SLUG)
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
        "kind": "dexagon.ainglish.only-focus-token-replication.v1",
        "metric": "token_delta",
        "construct": "only-<focus>",
        "models": MODELS,
        "test_set": test_set,
        "settlement_strata": [{"id": stratum, "weight": 1} for stratum in ROWS],
        "estimand_contract": {
            "kind": "ainglish.estimand-shadow.v1",
            "unit_span": "complete sentence",
            "contrast": "hyphen-welded only-<focus> versus bare only at the identical focus site",
            "population": "32 fresh sentences balanced eight each across subject, verb, object-nominal and adjunct focus",
            "aggregation": {
                "reducer": "least_favourable",
                "rule": "equal item mean per stratum, equal stratum mean per tokenizer, then maximum tokenizer mean",
            },
            "governance_effect": "report_only",
        },
        "replicates_hash": TARGET,
        "method": "Canonical SDK two-phase token runner; freeze before tokenizer loading and file every finite direction once.",
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "path": "only-focus-token-replication-v1-2026-09-04/build.py",
        },
        "evidentiary_limit": "Current token cost of the focus weld against bare only; not comprehension or future Ainglish-aware tokenizer cost.",
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
