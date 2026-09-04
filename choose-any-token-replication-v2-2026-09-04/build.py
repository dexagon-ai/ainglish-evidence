#!/usr/bin/env python3
"""Freeze a fresh canonical token replication without loading any tokenizer."""

from __future__ import annotations

import json
from pathlib import Path

from ainglish.client import AinglishClient, manifest_commitment


ROOT = Path(__file__).resolve().parent
SLUG = "choose-any-set-ref-draw-uniform-set-ref"
TARGET = "b69c504b32ada4a6c2563049fa4ca75e4223930d1c5714d4bfcd198b8121b1cd"


PAIRS = [
    ("Choose any one of the on-call reviewers; each reviewer is acceptable.", "choose-any(on-call-reviewers)."),
    ("Choose any one of the mirrored registries; each registry is acceptable.", "choose-any(mirrored-registries)."),
    ("Choose any one of the unused service accounts; each account is acceptable.", "choose-any(unused-service-accounts)."),
    ("Choose any one of the admissible routes; each route is acceptable.", "choose-any(admissible-routes)."),
    ("Choose any one of the passing builds; each build is acceptable.", "choose-any(passing-builds)."),
    ("Choose any one of the available interpreters; each interpreter is acceptable.", "choose-any(available-interpreters)."),
    ("Choose any one of the verified snapshots; each snapshot is acceptable.", "choose-any(verified-snapshots)."),
    ("Choose any one of the compatible adapters; each adapter is acceptable.", "choose-any(compatible-adapters)."),
    ("Draw one of the candidate shards so that each shard has equal probability.", "draw-uniform(candidate-shards)."),
    ("Draw one of the eligible auditors so that each auditor has equal probability.", "draw-uniform(eligible-auditors)."),
    ("Draw one of the healthy replicas so that each replica has equal probability.", "draw-uniform(healthy-replicas)."),
    ("Draw one of the unresolved tickets so that each ticket has equal probability.", "draw-uniform(unresolved-tickets)."),
    ("Draw one of the validated checkpoints so that each checkpoint has equal probability.", "draw-uniform(validated-checkpoints)."),
    ("Draw one of the permitted regions so that each region has equal probability.", "draw-uniform(permitted-regions)."),
    ("Draw one of the complete samples so that each sample has equal probability.", "draw-uniform(complete-samples)."),
    ("Draw one of the independent readers so that each reader has equal probability.", "draw-uniform(independent-readers)."),
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
    assert manifest_commitment(target_manifest) == TARGET
    assert target.get("metric") == "token_delta"
    assert target_manifest.get("models") == ["cl100k_base", "o200k_base", "p50k_base"]

    proposal = client.proposal(SLUG)
    fresh = set(PAIRS)
    assert len(fresh) == 16
    prior: set[tuple[str, str]] = set()
    for row in proposal.get("measurements") or []:
        manifest = row.get("manifest")
        if not isinstance(manifest, dict) and row.get("manifest_hash"):
            detail = client.measurement(row["manifest_hash"])
            manifest = detail.get("measurement", detail).get("manifest")
        if isinstance(manifest, dict):
            prior |= pair_set(manifest)
    assert not fresh & prior, "fresh complete-pair overlap detected"

    manifest = {
        "kind": "dexagon.ainglish.choose-any-token-replication.v2",
        "metric": "token_delta",
        "construct": "choose-any / draw-uniform",
        "models": target_manifest["models"],
        "test_set": [
            {"english": english, "ainglish": ainglish}
            for english, ainglish in PAIRS
        ],
        "estimand_contract": {
            "kind": "ainglish.estimand-shadow.v1",
            "unit_span": "complete message",
            "contrast": "Ainglish form versus complete careful English",
            "population": "16 frozen fresh operational instructions balanced 8/8 across choose-any and draw-uniform",
            "aggregation": {
                "reducer": "least_favourable",
                "rule": "equal pair mean, then maximum tokenizer mean",
            },
            "governance_effect": "report_only",
        },
        "replicates_hash": TARGET,
        "method": "Canonical SDK two-phase token runner; freeze before tokenizer loading and file every finite direction once.",
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "path": "choose-any-token-replication-v2-2026-09-04/build.py",
        },
        "evidentiary_limit": "Current tokenizer cost only; not comprehension and not a forecast of Ainglish-aware models or tokenizers.",
    }
    spec = {"manifest": manifest, "replication_target_manifest": target_manifest}
    (ROOT / "spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "target": TARGET,
        "target_value": target.get("value"),
        "fresh_pair_count": len(fresh),
        "prior_pair_count": len(prior),
        "overlap": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
