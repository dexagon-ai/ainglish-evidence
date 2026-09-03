#!/usr/bin/env python3
"""Recompute carrier identity and the predeclared balance invariants."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    artifact = json.loads((ROOT / "items.json").read_text(encoding="utf-8"))
    items = artifact["items"]
    scientific = [item for item in items if not item.get("calibration")]
    controls = [item for item in items if item.get("calibration")]
    actual = hashlib.sha256(canonical(items)).hexdigest()
    if actual != artifact["sha256"]:
        raise SystemExit(f"REFUSING: carrier drift {actual} != {artifact['sha256']}")
    checks = {
        "unique_ids": len({item["id"] for item in items}) == len(items),
        "counts": (len(scientific), len(controls)) == (160, 8),
        "forms": Counter(item["settlement_stratum"] for item in scientific) == {"different-from": 80, "different-across": 80},
        "profiles": Counter(item["strata"]["profile"] for item in scientific) == {"both": 40, "reference-only": 40, "across-only": 40, "neither": 40},
        "domains": len({item["strata"]["domain"] for item in scientific}) == 20,
        "minimal_pairs": all(item["english"].split(" Instruction:", 1)[0] == item["ainglish"].split(" Instruction:", 1)[0] for item in scientific),
        "target_independent_controls": all(item.get("calibration_scope") == "target-independent" and item["english"] != item["ainglish"] for item in controls),
        "answer_membership": all(item["answer"] in item["options"] for item in items),
    }
    if not all(checks.values()):
        raise SystemExit(f"REFUSING: failed invariant(s): {checks}")
    print(json.dumps({"kind": "dexagon.ainglish.different-carrier-audit.v1", "status": "ok", "sha256": actual, "checks": checks}, indent=2))


if __name__ == "__main__":
    main()
