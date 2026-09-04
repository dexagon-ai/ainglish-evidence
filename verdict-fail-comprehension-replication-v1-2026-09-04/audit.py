#!/usr/bin/env python3
"""Audit the frozen carrier without invoking any reader."""

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
    science = [row for row in items if not row.get("calibration")]
    calibration = [row for row in items if row.get("calibration")]
    checks = {
        "digest_matches": sha256(canonical(items)).hexdigest() == index["items_sha256"],
        "science_96": len(science) == 96,
        "calibration_16": len(calibration) == 16,
        "forms_balanced": Counter(row["form"] for row in science) == {"verdict-fail": 48, "no-verdict": 48},
        "unique_ids": len({row["id"] for row in items}) == len(items),
        "unique_complete_pairs": len({(row["english"], row["ainglish"]) for row in science}) == len(science),
        "answers_in_options": all(row["answer"] in row["options"] for row in items),
        "four_unique_options": all(len(row["options"]) == len(set(row["options"])) == 4 for row in items),
        "no_reader_calls": payload["reader_calls"] == index["model_calls"] == 0,
    }
    report = {"kind": "dexagon.ainglish.verdict-fail-comprehension-audit.v1", "checks": checks, "ok": all(checks.values())}
    (ROOT / "audit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
