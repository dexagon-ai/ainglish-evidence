#!/usr/bin/env python3
"""Recompute identity and all declared carrier balances."""

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
    actual = hashlib.sha256(canonical(items)).hexdigest()
    checks = {
        "digest": actual == doc["sha256"],
        "unique_ids": len({item["id"] for item in items}) == len(items),
        "counts": (len(real), len(controls)) == (144, 8),
        "forms": Counter(item["strata"]["form"] for item in real) == {"send-snapshot": 72, "grant-live-view": 72},
        "domains": all(value == 24 for value in Counter(item["strata"]["domain"] for item in real).values()),
        "events": all(value == 36 for value in Counter(item["strata"]["event"] for item in real).values()),
        "probes": all(value == 48 for value in Counter(item["strata"]["probe"] for item in real).values()),
        "settlement_strata": len(Counter(item["settlement_stratum"] for item in real)) == 12 and all(value == 12 for value in Counter(item["settlement_stratum"] for item in real).values()),
        "reported_consequence_cells": len(Counter(item["report_cell"] for item in real)) == 48 and all(value == 3 for value in Counter(item["report_cell"] for item in real).values()),
        "minimal_pairs": all(item["english"].split(" Instruction:", 1)[0] == item["ainglish"].split(" Instruction:", 1)[0] for item in real),
        "controls": all(item["english"] != item["ainglish"] and item.get("calibration_scope") == "target-independent" for item in controls),
        "answers": all(item["answer"] in item["options"] for item in items),
        "two_questions": all(len(item["questions"]) == 2 for item in real),
        "component_cartesian": all(
            len(item["option_components"]) == 4
            and Counter(
                (row["implementation_correct"], row["consequence_correct"])
                for row in item["option_components"].values()
            ) == {(True, True): 1, (True, False): 1,
                  (False, True): 1, (False, False): 1}
            for item in real
        ),
        "answer_positions": Counter(item["options"].index(item["answer"]) for item in real) == {0: 36, 1: 36, 2: 36, 3: 36},
    }
    if not all(checks.values()):
        raise SystemExit(f"REFUSING: failed carrier checks: {checks}")
    print(json.dumps({"kind": "dexagon.ainglish.snapshot-live-carrier-audit.v1", "status": "ok", "sha256": actual, "checks": checks}, indent=2))


if __name__ == "__main__":
    main()
