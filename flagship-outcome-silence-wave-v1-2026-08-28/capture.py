#!/usr/bin/env python3
"""Capture current proposal/evidence state before generating answer-bearing inputs."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from ainglish.client import AinglishClient


ROOT = Path(__file__).resolve().parent
TARGETS = [
    "test-run-t-test-passed-t-did-tested-mean-the-check-happened-",
    "go-unless-no-t-hold-until-yes-say-what-the-addressee-s-silen",
    "some-or-all-some-but-not-all-does-some-leave-room-for-all-2",
    "may-as-permission-may-as-possibility-does-may-authorize-an-a",
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    client = AinglishClient(use_env=False)
    proposals = {}
    for requested_slug in TARGETS:
        proposal = client.proposal(requested_slug)
        selected = {
            key: proposal.get(key)
            for key in (
                "public_id", "slug", "title", "kind", "stage", "publication_status", "form",
                "slot", "english_mapping", "predicted_measurement", "evidence_contract",
                "evidence_readiness", "colony_thread_url", "proposer", "verdict",
            )
        }
        selected["measurements"] = [{
            key: measurement.get(key)
            for key in (
                "metric", "value", "value_lo", "value_hi", "manifest_hash", "attempt_id",
                "is_replication", "replicates_hash", "reproduced_ok", "settlement_eligible",
                "settlement_state", "confirmed", "at", "submitter",
            )
        } for measurement in proposal.get("measurements", [])]
        selected["surface_sha256"] = hashlib.sha256(canonical({
            key: selected[key]
            for key in ("form", "slot", "english_mapping", "predicted_measurement", "evidence_contract")
        })).hexdigest()
        proposals[requested_slug] = selected

    artifact = {
        "kind": "dexagon.ainglish.flagship-outcome-silence-snapshot.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "https://ainglish.org/api/v1",
        "proposals": proposals,
        "answer_bearing_items_generated_before_snapshot": False,
        "reader_calls": 0,
        "model_calls": 0,
        "tokenizer_calls": 0,
        "attempt_mints": 0,
        "governance_writes": 0,
    }
    artifact["content_sha256"] = hashlib.sha256(canonical(artifact)).hexdigest()
    (ROOT / "proposal-snapshot.json").write_text(
        json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "captured_at": artifact["captured_at"],
        "proposals": {slug: row["surface_sha256"] for slug, row in proposals.items()},
        "content_sha256": artifact["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
