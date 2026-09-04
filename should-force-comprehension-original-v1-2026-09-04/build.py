#!/usr/bin/env python3
"""Bind the old, never-run should carrier to explicit settlement strata."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "modal-operational-comprehension-carriers-2026-08-25" / "panel" / "should.json"


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def main() -> None:
    old = json.loads(SOURCE.read_text(encoding="utf-8"))
    assert old["sha256"] == sha256(canonical(old["items"])).hexdigest()
    items = []
    for item in old["items"]:
        fixed = dict(item)
        if not fixed.get("calibration"):
            fixed["settlement_stratum"] = fixed["form"]
        items.append(fixed)

    real = [row for row in items if not row.get("calibration")]
    controls = [row for row in items if row.get("calibration")]
    forms = Counter(row["form"] for row in real)
    complements = Counter((row["form"], row["strata"]["complement"]) for row in real)
    answers = Counter(row["options"].index(row["answer"]) for row in real)
    assert len(real) == 100 and len(controls) == 8
    assert forms == {"should-as-rule": 50, "should-as-forecast": 50}
    assert complements == {
        ("should-as-rule", "agentive"): 25,
        ("should-as-rule", "stative"): 25,
        ("should-as-forecast", "agentive"): 25,
        ("should-as-forecast", "stative"): 25,
    }
    # 100 cells cannot divide equally across three answer positions.  The
    # frozen 34/34/32 distribution is also 17/17/16 within each form.
    assert answers == {0: 34, 1: 34, 2: 32}
    assert len({row["id"] for row in items}) == len(items)

    payload = {
        "kind": "dexagon.ainglish.should-force-items.v1",
        "source": {
            "path": "modal-operational-comprehension-carriers-2026-08-25/panel/should.json",
            "original_items_sha256": old["sha256"],
            "transformation": "add settlement_stratum equal to form on scientific rows; answer-bearing fields unchanged",
        },
        "items": items,
    }
    payload["items_sha256"] = sha256(canonical(items)).hexdigest()
    audit = {
        "kind": "dexagon.ainglish.should-force-items-audit.v1",
        "passed": True,
        "model_calls": 0,
        "scientific_items": len(real),
        "calibration_items": len(controls),
        "forms": forms,
        "form_by_complement": {f"{key[0]}:{key[1]}": value for key, value in complements.items()},
        "answer_positions": answers,
        "items_sha256": payload["items_sha256"],
    }
    (ROOT / "items.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2, default=dict))


if __name__ == "__main__":
    main()
