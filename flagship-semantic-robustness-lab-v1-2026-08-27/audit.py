#!/usr/bin/env python3
"""Audit frozen inputs and, when present, the robustness result."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    sealed = dict(value)
    expected = sealed.pop("content_sha256")
    if hashlib.sha256(canonical(sealed)).hexdigest() != expected:
        raise SystemExit(f"REFUSING: digest drift in {path}")
    return value


def main() -> None:
    plan = checked(ROOT / "plan.json")
    packet = json.loads((ROOT / "items.json").read_text(encoding="utf-8"))
    rows = packet["rows"]
    assert len(rows) == 136 and len({row["id"] for row in rows}) == 136
    assert hashlib.sha256(canonical(rows)).hexdigest() == packet["items_sha256"] == plan["items_sha256"]
    assert len({row["slug"] for row in rows}) == 17
    assert {row["variant"] for row in rows} == {"canonical", "hyphen_loss", "careful_english", "opposite_distractor"}
    assert all(sum(other["slug"] == row["slug"] for other in rows) == 8 for row in rows)
    output = {"status": "frozen-inputs-ok", "constructs": 17, "items": 136, "models": 3, "model_downloads": 0}
    if (ROOT / "result.json").exists():
        result = checked(ROOT / "result.json")
        assert result["plan_sha256"] == plan["content_sha256"]
        assert result["items_sha256"] == plan["items_sha256"]
        assert result["calls_expected"] == result["calls_observed"] == 51
        assert len(result["model_summary"]) == 3 and len(result["construct_summary"]) == 17
        assert result["model_downloads"] == result["governance_writes"] == 0
        output["result"] = "ok"
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
