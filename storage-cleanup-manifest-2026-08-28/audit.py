#!/usr/bin/env python3
"""Fail closed if the cleanup manifest includes an unsafe worktree."""

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
    assert snapshot["mutations_performed"] == report["mutations_performed"] == []
    assert snapshot["safety_policy"]["models"] == "preserve"
    assert report["models"]["action"].startswith("preserve all")
    candidates = [
        row for row in snapshot["worktrees"]
        if row["classification"] == "cleanup_candidate_clean_and_reachable"
    ]
    assert len(candidates) == report["worktrees"]["cleanup_candidate_count"]
    assert sum(row["size_bytes"] or 0 for row in candidates) == report["worktrees"]["cleanup_candidate_bytes"]
    for row in candidates:
        assert row["primary"] is False
        assert row["exists"] is True
        assert row["dirty_entry_count"] == 0
        assert row["head_reachable_from_default_remote"] is True
        assert row["size_error"] is None
    assert report["capacity"]["wsl_free_bytes"] > 0
    assert report["capacity"]["windows_c_free_bytes"] > 0
    assert report["status"] == "inventory_complete_no_cleanup_performed"
    print(json.dumps({
        "status": "verified",
        "worktree_candidates": len(candidates),
        "content_sha256": report["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
