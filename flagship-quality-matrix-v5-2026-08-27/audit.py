#!/usr/bin/env python3
"""Audit v5 matrix claim separation and all-row coverage."""

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main():
    value = json.loads((ROOT / "matrix.json").read_text(encoding="utf-8"))
    unsigned = dict(value); expected = unsigned.pop("content_sha256")
    assert hashlib.sha256(canonical(unsigned)).hexdigest() == expected
    assert len(value["rows"]) == 17 and [r["rank"] for r in value["rows"]] == list(range(1, 18))
    assert all(len(row["editorial_checks"]) == 5 for row in value["rows"])
    assert all(row["publication_lane"] != "site-leading-guarded" or row["stage"] == "ratified" for row in value["rows"])
    assert all(row["qualification_state"] != "qualified" for row in value["rows"])
    assert sum(row["modern_carrier_frozen"] for row in value["rows"]) == 5
    assert next(row for row in value["rows"] if row["rank"] == 14)["editorial_score"] == 4
    assert next(row for row in value["rows"] if row["rank"] == 17)["editorial_score"] == 4
    print(json.dumps(value["summary"], indent=2))


if __name__ == "__main__":
    main()
