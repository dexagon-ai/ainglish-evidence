#!/usr/bin/env python3
"""Refresh the public settlement state of every handoff without credentials."""

from __future__ import annotations

import json
import pathlib
import urllib.request


ROOT = pathlib.Path(__file__).resolve().parent
API = "https://ainglish.org/api/v1/measurements/"


def main() -> int:
    handoffs = json.loads((ROOT / "handoffs.json").read_text())
    changed = False
    for target in handoffs["targets"]:
        with urllib.request.urlopen(API + target["replicates_hash"], timeout=30) as response:
            row = json.load(response)
        current = {
            "stage": row["proposal"]["stage"],
            "settlement_state": row["settlement_state"],
            "replication_count": row["replication_count"],
            "disagreement_count": row["disagreement_count"],
            "counts_toward_verdict": row["counts_toward_verdict"],
        }
        stale = target["live_state"] != current["settlement_state"]
        changed |= stale
        print(json.dumps({"key": target["key"], "stale": stale, **current}, sort_keys=True))
    return int(changed)


if __name__ == "__main__":
    raise SystemExit(main())
