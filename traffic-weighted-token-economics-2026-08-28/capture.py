#!/usr/bin/env python3
"""Freeze live adoption receipts for the v0.35.0 language release."""

from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path

from ainglish.client import AinglishClient


ROOT = Path(__file__).resolve().parent
RELEASE = ROOT.parent.parent / "ainglish-releases" / "ainglish-training-v0.35.0"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    register_path = RELEASE / "data" / "register.jsonl"
    rows = [json.loads(line) for line in register_path.read_text(encoding="utf-8").splitlines() if line]
    client = AinglishClient()
    proposals = []
    for row in rows:
        live = client.proposal(row["slug"])
        adoption = live.get("adoption") or {}
        methodology = adoption.get("methodology") or {}
        proposals.append({
            "slug": row["slug"],
            "public_id": live.get("public_id"),
            "title": live.get("title"),
            "form": live.get("form"),
            "stage": live.get("stage"),
            "ratified_at": live.get("ratified_at"),
            "adoption": {
                "status": adoption.get("status"),
                "recent_usage": adoption.get("recent_usage"),
                "computed_at": methodology.get("computed_at"),
                "window": methodology.get("window"),
                "corpus": methodology.get("corpus"),
                "detector_version": methodology.get("detector_version"),
                "scan_count": methodology.get("scan_count"),
                "coverage": methodology.get("coverage"),
            },
        })
    document = {
        "kind": "dexagon.ainglish.release-adoption-snapshot.v1",
        "captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source": {
            "register_path": "ainglish-releases/ainglish-training-v0.35.0/data/register.jsonl",
            "register_sha256": hashlib.sha256(register_path.read_bytes()).hexdigest(),
            "api_base": "https://ainglish.org/api/v1",
        },
        "constructs": proposals,
    }
    document["content_sha256"] = hashlib.sha256(canonical(document)).hexdigest()
    (ROOT / "adoption-snapshot.json").write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({"constructs": len(proposals), "content_sha256": document["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
