#!/usr/bin/env python3
"""Fail-closed structural audit for the overnight comprehension wave."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def main() -> None:
    index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    report = {"kind": "dexagon.ainglish.overnight-comprehension-audit.v1", "campaigns": {}}
    for name, meta in index["campaigns"].items():
        payload = json.loads((ROOT / meta["file"]).read_text(encoding="utf-8"))
        items = payload["items"]
        real = [row for row in items if not row.get("calibration")]
        cal = [row for row in items if row.get("calibration")]
        assert payload["reader_calls"] == 0
        assert len(real) == 160
        assert len(cal) == 16
        assert len({row["id"] for row in items}) == len(items)
        assert all(len(row["options"]) == len(set(row["options"])) == 4 for row in items)
        assert all(row["answer"] in row["options"] for row in items)
        assert all(row["english"] != row["ainglish"] for row in items)
        counts = Counter(row["settlement_stratum"] for row in real)
        assert counts == Counter(meta["stratum_counts"])
        assert sha256(canonical(items)).hexdigest() == meta["items_sha256"]
        assert all(not any(marker in row["question"] for marker in (
            "ack-as-receipt", "ack-as-agreement", "cause-question", "justification-question",
            "value-unknown", "value-none", "value-redacted", "value-inapplicable",
        )) for row in real)
        if name in {"acknowledgement-type", "why-relation"}:
            by_form = Counter(row["form"] for row in real)
            by_form_comparator = Counter((row["form"], row["comparator"]) for row in real)
            assert sorted(by_form.values()) == [80, 80]
            assert set(by_form_comparator.values()) == {40}
        else:
            assert set(Counter(row["form"] for row in real).values()) == {40}
            assert all(row["comparator"] == "careful" for row in real)
        report["campaigns"][name] = {
            "scientific_items": len(real),
            "calibration_items": len(cal),
            "settlement_strata": dict(sorted(counts.items())),
            "items_sha256": meta["items_sha256"],
            "reader_calls": 0,
            "passed": True,
        }
    report["passed"] = True
    report["content_sha256"] = sha256(canonical(report)).hexdigest()
    (ROOT / "audit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
