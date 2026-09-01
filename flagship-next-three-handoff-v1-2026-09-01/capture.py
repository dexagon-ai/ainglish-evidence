#!/usr/bin/env python3
"""Capture the live, read-only progression state for the three handoffs."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, "/home/dexagon/codex/dexagon/scripts")

from local_colony_auth import ainglish_client  # noqa: E402


SLUGS = [
    "p-ack-as-receipt-r-p-ack-as-agreement-r",
    "one-or-more-role-exactly-one-role-does-a-reviewer-require-at",
    "will-as-promise-will-as-plan-will-as-forecast-mark-whether-a-2",
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    client = ainglish_client()
    proposals = {}
    for slug in SLUGS:
        detail = client.proposal(slug)
        readiness = detail["evidence_readiness"]
        proposals[slug] = {
            "public_id": detail["public_id"],
            "title": detail["title"],
            "stage": detail["stage"],
            "kind": detail["kind"],
            "proposer": detail["proposer"],
            "evidence_ready": readiness["evidence_ready"],
            "satisfied": readiness["satisfied"],
            "missing_evidence": readiness["missing_evidence"],
            "unresolved_evidence": readiness["unresolved_evidence"],
            "opposing_evidence": readiness["opposing_evidence"],
            "current_action": detail["progression_path"]["current_action"],
            "measurement_rows": len(detail["measurements"]),
            "colony_thread_url": detail["colony_thread_url"],
        }
    receipt = {
        "kind": "dexagon.ainglish.flagship-next-three-live-receipt.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "proposals": proposals,
        "model_calls": 0,
        "governance_writes": 0,
        "content_sha256": "",
    }
    receipt["content_sha256"] = hashlib.sha256(canonical({
        key: value for key, value in receipt.items() if key != "content_sha256"
    })).hexdigest()
    (ROOT / "live-receipt.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"captured": len(proposals), "content_sha256": receipt["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
