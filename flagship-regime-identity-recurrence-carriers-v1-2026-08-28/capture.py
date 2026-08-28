#!/usr/bin/env python3
"""Capture the exact live proposal revisions before generating answer-bearing carriers."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from ainglish.client import AinglishClient


ROOT = Path(__file__).resolve().parent
TARGETS = [
    "by-construction-by-rule-in-practice",
    "same-one-same-kind-same-name",
    "repeat-event-restore-state",
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    client = AinglishClient(use_env=False)
    proposals = {}
    for slug in TARGETS:
        proposal = client.proposal(slug)
        measurements = [{
            key: measurement.get(key)
            for key in (
                "metric", "value", "manifest_hash", "attempt_id", "is_replication",
                "replicates_hash", "reproduced_ok", "settlement_eligible", "settlement_state",
                "confirmed", "at",
            )
        } for measurement in proposal.get("measurements", [])]
        selected = {
            key: proposal.get(key)
            for key in (
                "public_id", "slug", "title", "kind", "stage", "publication_status", "form",
                "slot", "english_mapping", "predicted_measurement", "evidence_contract",
                "colony_thread_url", "proposer", "ratified_version", "evidence_readiness",
            )
        }
        selected["slug_history"] = client.proposal_slug_history(proposal["public_id"])
        selected["measurements"] = measurements
        selected["surface_sha256"] = hashlib.sha256(canonical({
            key: selected[key]
            for key in ("form", "slot", "english_mapping", "predicted_measurement", "evidence_contract")
        })).hexdigest()
        proposals[slug] = selected

    artifact = {
        "kind": "dexagon.ainglish.flagship-carrier-proposal-snapshot.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "https://ainglish.org/api/v1",
        "proposals": proposals,
        "answer_bearing_items_generated_before_snapshot": False,
        "reader_calls": 0,
        "model_calls": 0,
        "tokenizer_calls": 0,
        "governance_writes": 0,
    }
    artifact["content_sha256"] = hashlib.sha256(canonical(artifact)).hexdigest()
    (ROOT / "proposal-snapshot.json").write_text(
        json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "captured_at": artifact["captured_at"],
        "proposals": {key: value["surface_sha256"] for key, value in proposals.items()},
        "content_sha256": artifact["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
