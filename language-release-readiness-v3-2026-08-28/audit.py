#!/usr/bin/env python3
"""Fail closed on drift in the release-readiness derivation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(name: str) -> dict:
    value = json.loads((ROOT / name).read_text(encoding="utf-8"))
    digest = value.pop("content_sha256")
    assert hashlib.sha256(canonical(value)).hexdigest() == digest
    value["content_sha256"] = digest
    return value


def main() -> None:
    snapshot = checked("snapshot.json")
    report = checked("report.json")
    assert report["source_snapshot_sha256"] == snapshot["content_sha256"]
    assert report["latest_bundle"]["matches_live_register_head"] is True
    assert report["live"]["language_entries"] == report["latest_bundle"]["language_entries"] == 19
    assert report["live"]["protocol_entries"] == 16
    assert report["delta_for_release_3"] == {
        "added_language_slugs": [],
        "changed_language_slugs": [],
        "removed_language_slugs": [],
        "new_language_count": 0,
    }
    assert report["decision"]["state"] == "current_release_complete_next_release_not_yet_warranted"
    assert report["model_calls"] == report["governance_writes"] == 0
    print(json.dumps({"status": "verified", "content_sha256": report["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
