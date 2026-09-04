#!/usr/bin/env python3
"""Offline structural audit for the fresh dispute-settlement carriers."""

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
    findings = []
    all_scientific_pairs = set()
    for name, meta in index["campaigns"].items():
        carrier = json.loads((ROOT / meta["file"]).read_text(encoding="utf-8"))
        items = carrier["items"]
        assert sha256(canonical(items)).hexdigest() == meta["items_sha256"]
        science = [row for row in items if not row.get("calibration")]
        controls = [row for row in items if row.get("calibration")]
        assert len(science) == meta["scientific_items"]
        assert len(controls) == meta["calibration_items"] == 16
        assert len({row["id"] for row in items}) == len(items)
        assert Counter(row["form"] for row in science) == Counter(meta["forms"])
        positions = Counter(row["options"].index(row["answer"]) for row in science)
        assert max(positions.values()) - min(positions.values()) <= 1
        for row in science:
            assert row["english"] != row["ainglish"]
            assert len(row["options"]) == len(set(row["options"])) == 4
            assert "settlement_stratum" not in row
            pair = (row["english"], row["ainglish"])
            assert pair not in all_scientific_pairs
            all_scientific_pairs.add(pair)
        if name == "preference-release":
            bare_by_form = {
                form: {row["english"] for row in science if row["form"] == form}
                for form in meta["forms"]
            }
            assert len({frozenset(values) for values in bare_by_form.values()}) == 1
        findings.append({
            "campaign": name,
            "scientific_items": len(science),
            "calibration_items": len(controls),
            "answer_positions": dict(sorted(positions.items())),
            "forms": meta["forms"],
            "probes": meta["probes"],
            "items_sha256": meta["items_sha256"],
        })
    result = {"kind": "dexagon.ainglish.dispute-settlement-carrier-audit.v1", "passed": True, "model_calls": 0, "findings": findings}
    result["content_sha256"] = sha256(canonical(result)).hexdigest()
    (ROOT / "audit.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
