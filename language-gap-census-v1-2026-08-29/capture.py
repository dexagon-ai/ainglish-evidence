#!/usr/bin/env python3
"""Capture every current and historical register proposal for gap screening."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from ainglish.client import AinglishClient


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    rows = list(AinglishClient().iter_proposals(page_size=200))
    proposals = [
        {key: row.get(key) for key in ("slug", "public_id", "title", "form", "kind", "stage")}
        for row in rows
    ]
    payload = {
        "kind": "dexagon.ainglish.language-gap-register-snapshot.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "source": "AinglishClient().iter_proposals(page_size=200)",
        "count": len(proposals),
        "proposals": proposals,
        "model_calls": 0,
        "governance_writes": 0,
    }
    payload["content_sha256"] = hashlib.sha256(canonical(payload)).hexdigest()
    (ROOT / "register-snapshot.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"count": len(proposals), "content_sha256": payload["content_sha256"]}))


if __name__ == "__main__":
    main()
