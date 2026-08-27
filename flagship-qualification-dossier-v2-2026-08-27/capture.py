#!/usr/bin/env python3
"""Capture the complete public flagship catalog as a frozen live-state snapshot."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request


ROOT = Path(__file__).resolve().parent
URL = "https://ainglish.org/api/v1/flagships"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    with urllib.request.urlopen(URL, timeout=30) as response:
        catalog = json.load(response)
    assert catalog["kind"] == "ainglish.flagship-catalog.v1"
    assert len(catalog["entries"]) == catalog["selection"]["entry_count"] == 17
    snapshot = {
        "kind": "dexagon.ainglish.flagship-catalog-snapshot.v2",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "source_url": URL,
        "source_content_sha256": catalog["content_sha256"],
        "catalog": catalog,
        "network_reads": 1,
        "network_writes": 0,
        "governance_writes": 0,
    }
    snapshot["content_sha256"] = hashlib.sha256(canonical(snapshot)).hexdigest()
    (ROOT / "snapshot.json").write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: snapshot[key] for key in ("captured_at", "source_content_sha256", "content_sha256")}, indent=2))


if __name__ == "__main__":
    main()
