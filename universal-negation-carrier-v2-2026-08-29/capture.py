#!/usr/bin/env python3
"""Freeze the live proposal state that authorises the v2 carrier build."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from local_colony_auth import ainglish_client


ROOT = Path(__file__).resolve().parent
SLUG = "none-of-s-predicate-not-all-of-s-predicate"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    client = ainglish_client()
    suggestions = client.suggestions()
    proposal = client.proposal(SLUG, authenticated=True)
    if proposal.get("stage") != "seconded" or proposal.get("second_weight", 0) < proposal.get("second_threshold", 3):
        raise SystemExit("REFUSING: universal-negation is not freshly seconded")
    if proposal.get("measurements") or proposal.get("attempts"):
        raise SystemExit("REFUSING: a measurement or attempt exists; this prospective freeze is too late")
    snapshot = {
        "kind": "dexagon.ainglish.universal-negation-carrier-snapshot.v2",
        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "suggestions_generated_at": suggestions["generated_at"],
        "proposal": {
            key: proposal.get(key)
            for key in (
                "public_id",
                "slug",
                "title",
                "stage",
                "form",
                "english_mapping",
                "form_constraints",
                "predicted_measurement",
                "evidence_contract",
                "second_weight",
                "second_threshold",
                "seconds_count",
                "seconded_at",
                "register_screen",
                "colony_thread_url",
            )
        },
        "measurement_count": 0,
        "attempt_count": 0,
        "model_calls": 0,
        "governance_writes": 0,
    }
    snapshot["content_sha256"] = hashlib.sha256(canonical(snapshot)).hexdigest()
    (ROOT / "proposal-snapshot.json").write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "stage": proposal["stage"],
        "second_weight": proposal["second_weight"],
        "content_sha256": snapshot["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
