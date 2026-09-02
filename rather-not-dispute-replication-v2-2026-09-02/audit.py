#!/usr/bin/env python3
"""Fail-closed audit for the fresh rather-not replication carrier."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def main() -> None:
    payload = json.loads((ROOT / "items.json").read_text(encoding="utf-8"))
    index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    items = payload["items"]
    real = [row for row in items if not row.get("calibration")]
    cal = [row for row in items if row.get("calibration")]
    assert payload["reader_calls"] == 0
    assert len(real) == index["scientific_items"] == 288
    assert len(cal) == index["calibration_items"] == 8
    assert len({row["id"] for row in items}) == len(items)
    assert len({(row["strata"]["base_id"], row["form"]) for row in real}) == index["frames"] == 72
    assert Counter(row["form"] for row in real) == Counter({form: 96 for form in ("rather-not", "fine-either-way", "would-welcome")})
    assert Counter(row["outcome"] for row in real) == Counter({"preference": 144, "obligation": 144})
    assert set(Counter(row["settlement_stratum"] for row in real).values()) == {48}
    assert all(len(row["options"]) == len(set(row["options"])) == 3 for row in real)
    assert all(row["answer"] in row["options"] for row in items)
    assert all(row["english"] != row["ainglish"] for row in items)
    assert all(not any(form in row["question"] for form in ("rather-not", "fine-either-way", "would-welcome")) for row in real)
    assert sha256(canonical(items)).hexdigest() == index["items_sha256"]
    report = {
        "kind": "dexagon.ainglish.rather-not-dispute-replication-audit.v2",
        "scientific_items": len(real),
        "calibration_items": len(cal),
        "frames": index["frames"],
        "forms": index["forms"],
        "outcomes": index["outcomes"],
        "settlement_strata": index["settlement_strata"],
        "items_sha256": index["items_sha256"],
        "reader_calls": 0,
        "passed": True,
    }
    report["content_sha256"] = sha256(canonical(report)).hexdigest()
    (ROOT / "audit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
