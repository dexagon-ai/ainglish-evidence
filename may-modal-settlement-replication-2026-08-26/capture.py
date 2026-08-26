#!/usr/bin/env python3
"""Capture live surface and non-answer-bearing target metadata."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402


SLUG = "may-as-permission-may-as-possibility-does-may-authorize-an-a"
TARGET = "dba42c0e48b623502fb370067cf080a1b639a2bb621318400217f1f3d79b3e83"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    client = ainglish_client()
    suggestions = client.suggestions()
    proposal = client.proposal(SLUG, authenticated=True)
    target = client.measurement(TARGET)
    routed = [
        row for row in suggestions.get("suggestions", [])
        if row.get("replicates_hash") == TARGET and row.get("executable_now") is True
    ]
    if not routed:
        raise SystemExit("REFUSING: target is not freshly routed as an executable replication")
    if target.get("metric") != "comprehension_accuracy_delta" or target.get("replicates_hash"):
        raise SystemExit("REFUSING: target is not the expected comprehension original")
    planned = ((target.get("attempt") or {}).get("pin") or {}).get("planned_sample") or {}
    expected = {"real_items": 160, "calibration_items": 8, "frames": 80, "forms": 2, "comparator": "careful"}
    if any(planned.get(key) != value for key, value in expected.items()):
        raise SystemExit(f"REFUSING: target sample shape drifted: {planned!r}")
    snapshot = {
        "kind": "dexagon.ainglish.may-modal-settlement-snapshot.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "suggestions_generated_at": suggestions.get("generated_at"),
        "proposal": {
            key: proposal.get(key)
            for key in ("slug", "public_id", "title", "form", "english_mapping", "stage", "revision", "updated_at", "colony_thread_url")
        },
        "target_original": {
            "measurement_hash": target.get("manifest_hash"),
            "metric": target.get("metric"),
            "value": target.get("value"),
            "at": target.get("at"),
            "panel_models": target.get("panel_models"),
            "planned_sample": planned,
        },
        "answer_bearing_target_opened": False,
        "routed_executable": True,
    }
    snapshot["content_sha256"] = hashlib.sha256(canonical(snapshot)).hexdigest()
    (ROOT / "snapshot.json").write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"stage": proposal.get("stage"), "target": TARGET, "content_sha256": snapshot["content_sha256"]}))


if __name__ == "__main__":
    main()

