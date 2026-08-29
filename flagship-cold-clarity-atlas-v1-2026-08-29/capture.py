#!/usr/bin/env python3
"""Capture exact public proposal fields and already-installed Ollama artifacts once."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
PROPOSALS_PATH = ROOT / "proposal-snapshot.json"
ROSTER_PATH = ROOT / "reader-roster.json"
AINGLISH = "https://ainglish.org"
OLLAMA = "http://127.0.0.1:11434"

SLUGS = [
    "among-others-and-no-others-is-the-list-the-whole-list-2",
    "one-or-more-role-exactly-one-role-does-a-reviewer-require-at",
    "repeat-event-restore-state",
    "they-one-they-many-say-whether-they-is-one-actor-or-several",
    "observed-reported-by-inferred-from-mark-where-a-claim-came-f",
    "attempt-ensure-say-whether-the-instruction-tolerates-failure",
]

MODEL_TAGS = [
    "qwen3.6:35b",
    "gemma3:12b",
    "mistral-small3.2:24b-instruct-2506-q4_K_M",
    "phi4:14b",
    "olmo2:13b",
    "lfm2:24b",
]


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def fetch(url: str) -> tuple[dict[str, Any], dict[str, str]]:
    request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "dexagon-clarity-atlas/1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        raw = response.read()
        value = json.loads(raw)
        headers = {key.lower(): value for key, value in response.headers.items()}
    if not isinstance(value, dict):
        raise RuntimeError(f"non-object response from {url}")
    return value, {"etag": headers.get("etag", ""), "last_modified": headers.get("last-modified", ""), "raw_sha256": hashlib.sha256(raw).hexdigest()}


def unwrap_proposal(value: dict[str, Any]) -> dict[str, Any]:
    if isinstance(value.get("proposal"), dict):
        return value["proposal"]
    if isinstance(value.get("data"), dict):
        return value["data"]
    return value


def main() -> None:
    if PROPOSALS_PATH.exists() or ROSTER_PATH.exists():
        raise SystemExit("REFUSING: capture files already exist")
    captured_at = dt.datetime.now(dt.timezone.utc).isoformat()
    proposals = []
    for slug in SLUGS:
        url = f"{AINGLISH}/api/v1/proposals/{slug}"
        envelope, receipt = fetch(url)
        proposal = unwrap_proposal(envelope)
        if proposal.get("slug") != slug:
            raise RuntimeError(f"proposal slug mismatch for {slug}")
        proposals.append({
            "source_url": url,
            "source_receipt": receipt,
            "public_id": proposal.get("public_id"),
            "slug": slug,
            "title": proposal.get("title"),
            "kind": proposal.get("kind"),
            "stage": proposal.get("stage"),
            "form": proposal.get("form"),
            "english_mapping": proposal.get("english_mapping"),
            "form_constraints": proposal.get("form_constraints"),
            "corruption_neighbors": proposal.get("corruption_neighbors"),
            "created_at": proposal.get("created_at"),
            "seconded_at": proposal.get("seconded_at"),
        })
    proposal_snapshot = {
        "schema": "ainglish.flagship-cold-clarity-proposal-snapshot.v1",
        "captured_at": captured_at,
        "proposals": proposals,
    }
    PROPOSALS_PATH.write_bytes(json.dumps(proposal_snapshot, ensure_ascii=False, indent=2, sort_keys=True).encode() + b"\n")

    tags, tag_receipt = fetch(f"{OLLAMA}/api/tags")
    by_name = {row.get("name"): row for row in tags.get("models", []) if isinstance(row, dict)}
    missing = [tag for tag in MODEL_TAGS if tag not in by_name]
    if missing:
        raise RuntimeError(f"required models are not installed: {missing}")
    readers = []
    families = set()
    for tag in MODEL_TAGS:
        row = by_name[tag]
        details = row.get("details") if isinstance(row.get("details"), dict) else {}
        family = details.get("family")
        if not isinstance(family, str) or not family:
            raise RuntimeError(f"model {tag} has no declared family")
        if family in families:
            raise RuntimeError(f"model family is not distinct: {family}")
        families.add(family)
        digest = row.get("digest")
        if not isinstance(digest, str) or len(digest) != 64:
            raise RuntimeError(f"model {tag} has no exact digest")
        readers.append({
            "tag": tag,
            "digest": digest,
            "reader_id": f"ollama/{tag}@sha256:{digest}",
            "size": row.get("size"),
            "details": details,
        })
    version = subprocess.run(["ollama", "--version"], check=True, capture_output=True, text=True).stdout.strip()
    roster = {
        "schema": "ainglish.flagship-cold-clarity-reader-roster.v1",
        "captured_at": captured_at,
        "ollama_version": version,
        "api_tags_receipt": tag_receipt,
        "selection": "Six distinct already-installed model families; no downloads and no substitutions after freeze.",
        "readers": readers,
    }
    ROSTER_PATH.write_bytes(json.dumps(roster, ensure_ascii=False, indent=2, sort_keys=True).encode() + b"\n")
    print(json.dumps({"proposals": len(proposals), "readers": len(readers), "families": sorted(families)}, sort_keys=True))


if __name__ == "__main__":
    main()
