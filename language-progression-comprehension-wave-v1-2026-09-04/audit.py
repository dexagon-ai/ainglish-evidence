#!/usr/bin/env python3
"""Fail closed on structural carrier defects before publication or inference."""

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
    for name, meta in index["campaigns"].items():
        payload = json.loads((ROOT / meta["file"]).read_text(encoding="utf-8"))
        items = payload["items"]
        science = [row for row in items if not row.get("calibration")]
        controls = [row for row in items if row.get("calibration")]
        ids = [row["id"] for row in items]
        assert len(items) == 48 and len(science) == 32 and len(controls) == 16
        assert len(ids) == len(set(ids))
        assert sha256(canonical(items)).hexdigest() == meta["items_sha256"]
        assert Counter(row["settlement_stratum"] for row in science) == Counter({s["id"]: 16 for s in meta["settlement_strata"]})
        for row in items:
            assert set(["id", "english", "ainglish", "question", "options", "answer"]).issubset(row)
            assert len(row["options"]) == len(set(row["options"])) == 4
            assert row["answer"] in row["options"]
            assert row["english"] != row["ainglish"]
        answer_positions = Counter(row["options"].index(row["answer"]) for row in science)
        assert max(answer_positions.values()) - min(answer_positions.values()) <= 1
        findings.append({
            "campaign": name,
            "items_sha256": meta["items_sha256"],
            "scientific_items": len(science),
            "calibration_items": len(controls),
            "answer_positions": dict(sorted(answer_positions.items())),
            "strata": meta["stratum_counts"],
        })
    receipt = {"kind": "dexagon.ainglish.language-progression-carrier-audit.v1", "passed": True, "model_calls": 0, "findings": findings}
    receipt["content_sha256"] = sha256(canonical(receipt)).hexdigest()
    (ROOT / "audit.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
