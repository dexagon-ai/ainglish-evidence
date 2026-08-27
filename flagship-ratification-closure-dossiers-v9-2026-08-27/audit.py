#!/usr/bin/env python3
"""Offline integrity audit for the v9 closure-dossier bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    sealed = dict(value)
    expected = sealed.pop("content_sha256")
    actual = hashlib.sha256(canonical(sealed)).hexdigest()
    if actual != expected:
        raise SystemExit(f"REFUSING: digest drift in {path}: {actual} != {expected}")
    return value


def main() -> None:
    snapshot = checked(ROOT / "snapshot.json")
    manifest = checked(ROOT / "manifest.json")
    if manifest["snapshot_sha256"] != snapshot["content_sha256"]:
        raise SystemExit("REFUSING: manifest does not bind the captured snapshot")
    if len(manifest["dossiers"]) != 17:
        raise SystemExit("REFUSING: dossier manifest does not contain 17 entries")
    ranks = set()
    slugs = set()
    for row in manifest["dossiers"]:
        dossier = checked(ROOT / row["json"])
        markdown = ROOT / row["markdown"]
        if not markdown.is_file():
            raise SystemExit(f"REFUSING: missing Markdown dossier {markdown}")
        if dossier["content_sha256"] != row["content_sha256"]:
            raise SystemExit(f"REFUSING: manifest digest mismatch for {row['slug']}")
        if dossier["rank"] != row["rank"] or dossier["slug"] != row["slug"]:
            raise SystemExit(f"REFUSING: identity mismatch for {row['slug']}")
        ranks.add(row["rank"])
        slugs.add(row["slug"])
    live_slugs = {row["slug"] for row in snapshot["flagships"]}
    if ranks != set(range(1, 18)) or slugs != live_slugs:
        raise SystemExit("REFUSING: dossier coverage differs from the 17-entry live set")
    if snapshot["fresh_clearing_audit"]["eligible_deterministic_governance_writes"] != 0:
        raise SystemExit("REFUSING: clearing-decision invariant drift")
    print(json.dumps({
        "status": "ok",
        "dossiers": 17,
        "ratified": manifest["summary"]["ratified"],
        "pipeline": manifest["summary"]["pipeline"],
        "reader_lineages": manifest["summary"]["reader_lineages"],
        "eligible_deterministic_governance_writes": 0,
        "model_calls": 0,
        "governance_writes": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
