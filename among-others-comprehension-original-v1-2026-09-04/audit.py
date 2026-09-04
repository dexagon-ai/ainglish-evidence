#!/usr/bin/env python3
"""Audit the combined list-completeness claim carrier without model calls."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    doc = json.loads((ROOT / "items.json").read_text(encoding="utf-8"))
    items = doc["items"]
    real = [item for item in items if not item.get("calibration")]
    controls = [item for item in items if item.get("calibration")]
    checks = {
        "digest": hashlib.sha256(canonical(items)).hexdigest() == doc["sha256"],
        "counts": (len(real), len(controls)) == (240, 8),
        "unique_ids": len({item["id"] for item in items}) == len(items),
        "forms": Counter(item["form"] for item in real) == {"among-others": 120, "and-no-others": 120},
        "strata": Counter(item["settlement_stratum"] for item in real) == {"among-others": 120, "and-no-others": 120},
        "careful_only": all(item.get("comparator") == "careful" for item in real),
        "answers": all(item["answer"] in item["options"] for item in items),
        "three_options": all(len(item["options"]) == 3 for item in items),
        "probe_balance": all(value == 2 * count for key, count in Counter(item["strata"]["probe"] for item in real if item["form"] == "among-others").items() for value in [Counter(item["strata"]["probe"] for item in real)[key]]),
        "controls_target_independent": all(item.get("calibration_scope") == "target-independent" and item["english"] != item["ainglish"] for item in controls),
    }
    if not all(checks.values()):
        raise SystemExit(f"REFUSING: carrier audit failed: {checks}")
    print(json.dumps({"kind": "dexagon.ainglish.among-others-carrier-audit.v1", "status": "ok", "checks": checks, "sha256": doc["sha256"]}, indent=2))


if __name__ == "__main__":
    main()
