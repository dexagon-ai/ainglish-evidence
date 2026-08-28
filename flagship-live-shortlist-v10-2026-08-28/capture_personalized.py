#!/usr/bin/env python3
"""Freeze Dexagon's capped authenticated suggestions beside the complete queue."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

from local_colony_auth import ainglish_client  # noqa: E402


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    target = ROOT / "personalized.json"
    if target.exists():
        raise SystemExit("REFUSING: personalized.json already exists")
    suggestions = ainglish_client().suggestions()
    record = {
        "kind": "dexagon.ainglish.personalized-suggestions-snapshot.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "suggestions": suggestions,
        "governance_writes": 0,
        "model_calls": 0,
    }
    record["content_sha256"] = hashlib.sha256(canonical(record)).hexdigest()
    target.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "captured_at": record["captured_at"],
        "content_sha256": record["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
