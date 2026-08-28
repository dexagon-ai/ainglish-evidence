#!/usr/bin/env python3
"""Validate the frozen claim audit and optionally verify immutable source bytes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import urllib.parse
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent
AUDIT = ROOT / "audit.json"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")


def content_url(repository: str, commit: str, path: str) -> str:
    quoted_path = urllib.parse.quote(path, safe="/")
    quoted_ref = urllib.parse.quote(commit, safe="")
    return f"https://api.github.com/repos/{repository}/contents/{quoted_path}?ref={quoted_ref}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true", help="verify reviewed bytes from GitHub")
    args = parser.parse_args()

    document = json.loads(AUDIT.read_text(encoding="utf-8"))
    assert document["schema"] == "ainglish.cross_repo_efficiency_claim_audit.v1"
    assert len(document["decision_rules"]) == 6
    assert len(document["scope"]) == 5
    assert [finding["id"] for finding in document["findings"]] == [
        "F1", "F2", "F3", "F4", "F5", "F6"
    ]
    assert document["conclusion"]["false_mechanism_claims_found"] == 0
    assert document["conclusion"]["corrective_edits_required_on_pinned_heads"] == 0

    checked = 0
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    for repository in document["scope"]:
        commit = repository["commit"]
        assert COMMIT.fullmatch(commit), commit
        assert repository["ref"].startswith("refs/heads/")
        assert repository["files"]
        for source in repository["files"]:
            assert source["path"] and not source["path"].startswith("/")
            assert ".." not in Path(source["path"]).parts
            assert SHA256.fullmatch(source["sha256"]), source
            checked += 1
            if args.fetch:
                headers = {
                    "Accept": "application/vnd.github.raw+json",
                    "User-Agent": "ainglish-efficiency-claim-audit/1",
                    "X-GitHub-Api-Version": "2022-11-28",
                }
                if token:
                    headers["Authorization"] = f"Bearer {token}"
                request = urllib.request.Request(
                    content_url(repository["repository"], commit, source["path"]),
                    headers=headers,
                )
                try:
                    with urllib.request.urlopen(request, timeout=30) as response:
                        payload = response.read()
                except urllib.error.HTTPError as error:
                    hint = " (set GITHUB_TOKEN or GH_TOKEN if this repository is private)" if error.code in (401, 404) else ""
                    raise SystemExit(
                        f"fetch failed: {repository['repository']}:{source['path']} "
                        f"HTTP {error.code}{hint}"
                    ) from None
                actual = hashlib.sha256(payload).hexdigest()
                if actual != source["sha256"]:
                    raise SystemExit(
                        f"digest mismatch: {repository['repository']}:{source['path']} "
                        f"expected {source['sha256']} got {actual}"
                    )

    mode = "remote bytes" if args.fetch else "offline structure"
    print(json.dumps({"status": "verified", "mode": mode, "files": checked}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
