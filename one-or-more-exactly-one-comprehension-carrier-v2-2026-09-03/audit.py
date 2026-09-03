#!/usr/bin/env python3
"""Audit carrier hashes, v1 scientific identity, and v2 planted controls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
V1 = ROOT.parent / "one-or-more-exactly-one-comprehension-carrier-2026-08-26"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    checked = []
    for name, meta in index["campaigns"].items():
        current = json.loads((ROOT / meta["file"]).read_text(encoding="utf-8"))
        old = json.loads((V1 / meta["file"]).read_text(encoding="utf-8"))
        rows = current["items"]
        assert hashlib.sha256(canonical(rows)).hexdigest() == meta["items_sha256"]
        science = [row for row in rows if not row.get("calibration")]
        old_science = [row for row in old["items"] if not row.get("calibration")]
        controls = [row for row in rows if row.get("calibration")]
        assert science == old_science and len(science) == 120
        assert len(controls) == 8 and all(row["english"] != row["ainglish"] for row in controls)
        assert not any(marker in (row["english"] + row["ainglish"]).casefold()
                       for row in controls for marker in ("one-or-more", "exactly-one"))
        checked.append(name)
    unsealed = dict(index)
    expected = unsealed.pop("content_sha256")
    assert hashlib.sha256(canonical(unsealed)).hexdigest() == expected
    print(json.dumps({"status": "ok", "campaigns": checked, "reader_calls": 0}))


if __name__ == "__main__":
    main()
