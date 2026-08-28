#!/usr/bin/env python3
"""Recompute the receipt digests and fail on any unmet live-QA contract."""

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
    assert all(snapshot["deployment"]["contains_required_merges"].values())
    assert all(response["status"] == 200 for response in snapshot["responses"].values())
    assert all(
        present
        for group in snapshot["markers"].values()
        for present in group.values()
    )
    assert report["status"] == "verified"
    assert report["failed_checks"] == []
    assert report["passed_count"] == report["check_count"]
    assert report["model_calls"] == report["governance_writes"] == 0
    print(json.dumps({
        "status": "verified",
        "checks": report["check_count"],
        "content_sha256": report["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
