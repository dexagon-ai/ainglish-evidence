#!/usr/bin/env python3
"""Freeze a small, fail-closed receipt for the 2026-08-28 Symfony deploy."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re
import subprocess
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
SYMFONY = ROOT.parent.parent / "ainglish-symfony"
BASE = "https://ainglish.org"
REQUIRED_MERGES = {
    "press_and_history_pr_323": "b6ec4ff951b8ccf2c2d9ff6020df36bd1b11c5d3",
    "artifact_header_scope_pr_326": "ea6113df3035ecbdadb7da264b55b7a381333a25",
    "applied_map_semantics_pr_327": "dfb624a82052f27977ee88623980968eb8922524",
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def fetch(path: str) -> tuple[dict, bytes]:
    request = Request(
        BASE + path,
        headers={
            "User-Agent": "Dexagon-Ainglish-live-QA/1.0",
            "Cache-Control": "no-cache",
        },
    )
    with urlopen(request, timeout=30) as response:
        body = response.read()
        headers = {key.lower(): value for key, value in response.headers.items()}
        receipt = {
            "path": path,
            "effective_url": response.url,
            "status": response.status,
            "body_bytes": len(body),
            "body_sha256": hashlib.sha256(body).hexdigest(),
            "headers": {
                key: headers.get(key)
                for key in (
                    "content-type",
                    "cache-control",
                    "link",
                    "access-control-allow-origin",
                    "etag",
                    "last-modified",
                )
            },
        }
    return receipt, body


def normalized_text(body: bytes) -> str:
    return re.sub(r"\s+", " ", html.unescape(body.decode("utf-8", errors="replace")))


def markers(body: bytes, expected: list[str]) -> dict[str, bool]:
    text = normalized_text(body)
    return {marker: marker in text for marker in expected}


def is_ancestor(ancestor: str, descendant: str) -> bool:
    return subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=SYMFONY,
        check=False,
    ).returncode == 0


def main() -> None:
    target = ROOT / "snapshot.json"
    if target.exists():
        raise SystemExit("REFUSING: snapshot.json already exists")

    paths = [
        "/api/v1/health",
        "/press",
        "/history",
        "/state",
        "/sitemap.xml",
        "/releases",
        "/training",
        "/paper",
        "/releases/ainglish-core-v0.35.0/MANIFEST.json",
        "/training/ainglish-training-v0.35.0/data/parallel.jsonl",
        "/paper/1.0/ainglish-whitepaper.md",
    ]
    responses: dict[str, dict] = {}
    bodies: dict[str, bytes] = {}
    for path in paths:
        responses[path], bodies[path] = fetch(path)

    health = json.loads(bodies["/api/v1/health"])
    deployed_commit = health["deployment"]["commit"]
    deployment_contains = {
        name: is_ancestor(commit, deployed_commit)
        for name, commit in REQUIRED_MERGES.items()
    }

    snapshot = {
        "kind": "dexagon.ainglish.post-merge-live-qa.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE,
        "deployment": {
            "identity": health["deployment"]["identity"],
            "commit": deployed_commit,
            "openapi_sha256": health["deployment"]["openapi_sha256"],
            "required_merges": REQUIRED_MERGES,
            "contains_required_merges": deployment_contains,
        },
        "responses": responses,
        "markers": {
            "press": markers(bodies["/press"], [
                "Copy-ready descriptions",
                "internally verified and ending at the current register digest",
                "not externally peer-reviewed or human-authored",
                "not evidence of widespread adoption",
            ]),
            "history": markers(bodies["/history"], [
                "Selected history, complete mutation log",
                "No separate errata file is published alongside this edition",
                "not a claim that the paper contains no errors",
                "original record and link both directions",
            ]),
            "state": markers(bodies["/state"], [
                "Ratified, observed",
                "Ratified, not scanned",
                "Ratified machinery",
                "In pipeline",
                "Never filed",
                "No usage seen",
                "ratified constructs with an observed reading",
                "ratified with no current reading",
                "corpus adoption does not apply",
                "am-ratified-na",
            ]),
            "sitemap": markers(bodies["/sitemap.xml"], [
                "https://ainglish.org/press",
                "https://ainglish.org/history",
            ]),
        },
        "model_calls": 0,
        "governance_writes": 0,
    }
    snapshot["content_sha256"] = hashlib.sha256(canonical(snapshot)).hexdigest()
    target.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "captured_at": snapshot["captured_at"],
        "deployment_commit": deployed_commit,
        "required_merges_present": deployment_contains,
        "content_sha256": snapshot["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
