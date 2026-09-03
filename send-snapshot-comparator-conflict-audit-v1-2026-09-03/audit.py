#!/usr/bin/env python3
"""Verify that the send-snapshot token rows answer two different contrasts."""

from __future__ import annotations

import json

from ainglish.client import AinglishClient


SLUG = "send-snapshot-version-ref-to-recipient-grant-live-view"
MINIMAL = "3d50880de5d78f427fbfe8a32fec788b85a2aea1581a54a1435aa6aa9f89c76e"
MINIMAL_REPLICATION = "80f4a47c75e8ccdabba07dc778719a765f70b737a5dcef24cac3fa80ae940edc"
COMPLETE = "3ac9910f538f68f962193586b253cc212a0c1ca7b76ff2f9705189549906ad4d"


def main() -> None:
    proposal = AinglishClient(use_env=False).proposal(SLUG)
    assert "complete mappings" in proposal["predicted_measurement"]
    rows = {row["manifest_hash"]: row for row in proposal["measurements"]}
    assert rows[MINIMAL]["value"] == 9.3
    assert rows[MINIMAL]["settlement_state"] == "confirmed"
    assert rows[MINIMAL_REPLICATION]["replicates_hash"] == MINIMAL
    assert rows[MINIMAL_REPLICATION]["reproduced_ok"] is True
    assert rows[COMPLETE]["value"] == -15.286
    assert rows[COMPLETE]["replication_count"] == 0

    minimal_estimand = rows[MINIMAL_REPLICATION]["attempt"]["pin"]["estimand"]
    complete_estimand = rows[COMPLETE]["attempt"]["pin"]["estimand"]
    assert "bare English sharing sentence" in minimal_estimand
    assert "full-lossless English gloss" in complete_estimand

    print(json.dumps({
        "kind": "ainglish.send-snapshot-comparator-conflict-audit.v1",
        "proposal": SLUG,
        "declared_prerequisite_comparator": "complete careful-English mappings",
        "contrasts": [
            {
                "role": "descriptive_minimal_phrase_cost",
                "original": MINIMAL,
                "replication": MINIMAL_REPLICATION,
                "values": [rows[MINIMAL]["value"], rows[MINIMAL_REPLICATION]["value"]],
                "answers_declared_prerequisite": False,
            },
            {
                "role": "declared_complete_mapping_prerequisite",
                "original": COMPLETE,
                "replication": None,
                "values": [rows[COMPLETE]["value"]],
                "answers_declared_prerequisite": True,
            },
        ],
        "classification": "different_estimands_not_replication_disagreement",
        "next_action": "modern successor plus independent replication for the complete-mapping row",
    }, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
