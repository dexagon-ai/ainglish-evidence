#!/usr/bin/env python3
"""Freeze live register, latest language bundle, and release-tooling PR state."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

from ainglish.client import AinglishClient


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent
RELEASES = PROJECT / "ainglish-releases"
LATEST = RELEASES / "ainglish-core-v0.35.0"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=RELEASES, check=True, capture_output=True, text=True
    ).stdout.strip()


def github_pr() -> dict:
    result = subprocess.run(
        [
            "gh", "pr", "view", "3", "--repo", "ai-nglish/ainglish-releases",
            "--json", "number,url,state,isDraft,headRefOid,mergeStateStatus,reviewDecision",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def main() -> None:
    target = ROOT / "snapshot.json"
    if target.exists():
        raise SystemExit("REFUSING: snapshot.json already exists")
    client = AinglishClient()
    live_register = client.register()
    live_release = client.register_release()
    manifest = json.loads((LATEST / "MANIFEST.json").read_text(encoding="utf-8"))
    released_register = json.loads((LATEST / "register.json").read_text(encoding="utf-8"))
    snapshot = {
        "kind": "dexagon.ainglish.language-release-readiness-snapshot.v3",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "live_register": live_register,
        "live_register_release": live_release,
        "latest_language_bundle": {
            "directory": LATEST.name,
            "manifest": manifest,
            "manifest_sha256": hashlib.sha256((LATEST / "MANIFEST.json").read_bytes()).hexdigest(),
            "register": released_register,
            "register_sha256": hashlib.sha256((LATEST / "register.json").read_bytes()).hexdigest(),
            "mirror_origin_master": git("rev-parse", "origin/master"),
        },
        "next_training_builder": github_pr(),
        "cadence_policy": {
            "next_release_version": "3",
            "routine_new_language_range": [5, 10],
            "elapsed_time_trigger_days": 30,
            "protocol_only_changes_do_not_trigger": True,
            "explicit_greenlight_required_for_exact_bytes": True,
        },
        "model_calls": 0,
        "governance_writes": 0,
    }
    snapshot["content_sha256"] = hashlib.sha256(canonical(snapshot)).hexdigest()
    target.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "captured_at": snapshot["captured_at"],
        "live_version": live_register["version"],
        "live_entries": live_register["count"],
        "content_sha256": snapshot["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
