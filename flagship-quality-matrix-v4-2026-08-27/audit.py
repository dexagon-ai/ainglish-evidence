#!/usr/bin/env python3
"""Audit the flagship matrix's separated-claim publication rules."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    matrix = json.loads((ROOT / "matrix.json").read_text(encoding="utf-8"))
    unsigned = dict(matrix)
    expected = unsigned.pop("content_sha256")
    assert hashlib.sha256(canonical(unsigned)).hexdigest() == expected
    assert len(matrix["rows"]) == 8 and len({row["slug"] for row in matrix["rows"]}) == 8
    assert all(len(row["editorial_checks"]) == 5 for row in matrix["rows"])
    assert all(row["publication_lane"] != "ratified-showcase" or row["stage"] == "ratified" for row in matrix["rows"])
    assert all(row["form_safe_settlement"] is False or row["confirmed_comprehension_rows"] > 0 for row in matrix["rows"])
    repeat = next(row for row in matrix["rows"] if row["form"].startswith("repeat-event"))
    role = next(row for row in matrix["rows"] if row["form"].startswith("one-or-more"))
    assert repeat["slug"].endswith("-4") and repeat["editorial_score"] == 4
    assert role["editorial_score"] == 5
    print(json.dumps({
        "rows": 8,
        "editorial_pass": sum(row["editorial_score"] == 5 for row in matrix["rows"]),
        "ratified_showcase": sum(row["publication_lane"] == "ratified-showcase" for row in matrix["rows"]),
        "pipeline_preview": sum(row["publication_lane"] == "pipeline-preview" for row in matrix["rows"]),
        "research_preview": sum(row["publication_lane"] == "research-preview" for row in matrix["rows"]),
        "form_safe_confirmed_comprehension": sum(row["form_safe_settlement"] for row in matrix["rows"]),
    }, indent=2))


if __name__ == "__main__":
    main()
