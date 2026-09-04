#!/usr/bin/env python3
"""Freeze the modern-contract part-boundary token replication without tokenizer exposure."""

from __future__ import annotations

import json
from pathlib import Path

from ainglish.client import AinglishClient, manifest_commitment
from ainglish.token_measurement import prepare


ROOT = Path(__file__).resolve().parent
SLUG = "part-chosen-rule-part-capped-limiter-was-the-edge-of-the-set"
TARGET = "13a722dd4d8b0206a42ff6450c5de1fea05a0f828d14254c61889bd7af894e83"
MODELS = ["cl100k_base", "o200k_base"]

CHOSEN = [
    ("I sampled the 42 repositories that the language-stratum rule chose, out of the 281 indexed; the rule picked which repositories to sample.", "part-chosen(language-stratum): the 42 repositories."),
    ("I reviewed the 65 invoices that the month-end rule chose, out of the 390 issued; the rule picked which invoices to review.", "part-chosen(month-end): the 65 invoices."),
    ("I inspected the 88 images that random seed 314 chose, out of the 712 stored; that rule picked which images to inspect.", "part-chosen(random-seed-314): the 88 images."),
    ("I checked the 31 branches that the risk-band rule chose, out of the 186 active; the rule picked which branches to check.", "part-chosen(risk-band): the 31 branches."),
    ("I audited the 57 consent records that the renewal-window rule chose, out of the 329 retained; the rule picked which records to audit.", "part-chosen(renewal-window): the 57 consent records."),
    ("I traced the 46 requests that the endpoint-family rule chose, out of the 275 logged; the rule picked which requests to trace.", "part-chosen(endpoint-family): the 46 requests."),
    ("I examined the 79 translations that the locale-quota rule chose, out of the 488 available; the rule picked which translations to examine.", "part-chosen(locale-quota): the 79 translations."),
    ("I read the 26 incident notes that the severity-pair rule chose, out of the 169 filed; the rule picked which notes to read.", "part-chosen(severity-pair): the 26 incident notes."),
]

CAPPED = [
    ("I examined 150 of the 521 repositories; the API stopped at 150, so I could not examine the remaining 371 repositories.", "part-capped(api-page-150): the 150 repositories."),
    ("I reviewed 400 of the 733 invoices; the export stopped at 400 rows, so I could not review the remaining 333 invoices.", "part-capped(export-row-400): the 400 invoices."),
    ("I inspected 73 of the 406 images; the scan timed out after 75 seconds, so I could not inspect the remaining images.", "part-capped(timeout-75s): the 73 images."),
    ("I checked 45 of the 138 branches; the quota stopped me at 45, so I could not check the remaining 93 branches.", "part-capped(quota-45): the 45 branches."),
    ("I audited 61 of the 347 consent records; my permission covered only division east, so I could not audit the remainder.", "part-capped(permission-east): the 61 consent records."),
    ("I traced 82 of the 294 requests; the twelve-gigabyte memory limit stopped the trace, so I could not examine the remainder.", "part-capped(memory-12gb): the 82 requests."),
    ("I examined 104 of the 519 translations; the archive exposed only forty-five days, so I could not examine the older translations.", "part-capped(archive-window-45d): the 104 translations."),
    ("I read 800 of the 1,491 incident notes; the console stopped at 800, so I could not read the remaining 691 notes.", "part-capped(console-limit-800): the 800 incident notes."),
]


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

    test_set = [
        {"english": english, "ainglish": ainglish, "stratum": stratum}
        for stratum, pairs in (("part-chosen", CHOSEN), ("part-capped", CAPPED))
        for english, ainglish in pairs
    ]
    fresh = {(row["english"], row["ainglish"]) for row in test_set}
    if len(test_set) != 16 or len(fresh) != 16:
        raise SystemExit("REFUSING: expected 16 unique complete pairs")
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

    declaration = target_manifest["estimand_contract"]
    manifest = {
        "kind": "dexagon.ainglish.part-boundary-token-replication.v1",
        "metric": "token_delta",
        "construct": "part-chosen / part-capped",
        "models": MODELS,
        "test_set": test_set,
        "settlement_strata": target_manifest["settlement_strata"],
        "comparison_identity": {
            "comparator_genre": "complete-careful-english-boundary-source-v1",
            "pair_rendering": "standalone-coverage-report",
        },
        "estimand_contract": declaration,
        "replicates_hash": TARGET,
        "method": "Canonical SDK two-phase token runner; exact target estimand and strata; freeze before tokenizer loading; file every finite direction once.",
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "path": "part-boundary-token-replication-v1-2026-09-04/build.py",
        },
        "evidentiary_limit": "Present tokenizer cost against complete careful English; not comprehension or future Ainglish-aware cost.",
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
