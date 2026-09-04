#!/usr/bin/env python3
"""Audit the frozen same-identity replication carrier without making model calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main() -> None:
    items = json.loads((ROOT / "items.json").read_text(encoding="utf-8"))
    scientific = [row for row in items if not row.get("calibration")]
    controls = [row for row in items if row.get("calibration")]
    forms = {
        prefix: sum(row["id"].startswith(prefix + "-") for row in scientific)
        for prefix in ("one", "kind", "name")
    }
    canonical = json.dumps(
        items, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    report = {
        "items_sha256": hashlib.sha256(canonical).hexdigest(),
        "scientific_items": len(scientific),
        "calibration_items": len(controls),
        "form_counts": forms,
        "unique_ids": len({row["id"] for row in items}) == len(items),
        "complete_pairs": all(row["english"] and row["ainglish"] for row in scientific),
        "same_kind_names_check_and_time": all(
            "(" in row["ainglish"] and ", as of " in row["ainglish"]
            for row in scientific
            if row["id"].startswith("kind-")
        ),
        "target_independent_controls": all(
            row.get("calibration_scope") == "target-independent" for row in controls
        ),
    }
    print(json.dumps(report, indent=2))
    expected = {
        "scientific_items": 48,
        "calibration_items": 8,
        "form_counts": {"one": 16, "kind": 16, "name": 16},
        "unique_ids": True,
        "complete_pairs": True,
        "same_kind_names_check_and_time": True,
        "target_independent_controls": True,
    }
    if any(report[key] != value for key, value in expected.items()):
        raise SystemExit("REFUSING: carrier audit failed")


if __name__ == "__main__":
    main()
