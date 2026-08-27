#!/usr/bin/env python3
"""Offline structural and semantic audit for the four additional carriers."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
KEYS = ("attribution", "deadline", "disjunction", "polarity")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    expected = value.pop("content_sha256")
    assert hashlib.sha256(canonical(value)).hexdigest() == expected, path.name
    value["content_sha256"] = expected
    return value


def main() -> None:
    report = {}
    all_ids = set()
    for key in KEYS:
        template = checked(ROOT / f"{key}.template.json")
        artifact = json.loads((ROOT / template["items_artifact"]["file"]).read_text(encoding="utf-8"))
        assert artifact["items"] == template["items"]
        assert hashlib.sha256(canonical(artifact["items"])).hexdigest() == artifact["sha256"]
        assert artifact["sha256"] == template["items_artifact"]["items_sha256"]
        assert template["items_artifact"]["published_url"].endswith("/" + template["items_artifact"]["file"])
        science = [row for row in template["items"] if not row.get("calibration")]
        calibration = [row for row in template["items"] if row.get("calibration")]
        counts = Counter(row["settlement_stratum"] for row in science)
        contract = template["settlement_strata"]
        assert set(counts) == {row["id"] for row in contract}
        assert set(counts.values()) == {6}
        assert all(set(row) == {"id", "weight"} and row["weight"] == 1 for row in contract)
        assert len(science) == (72 if key == "polarity" else 48) and len(calibration) == 12
        assert all(row["english"] != row["ainglish"] and row["answer"] in row["options"] for row in science)
        assert all(row["calibration_scope"] == "target-independent" for row in calibration)
        ids = {row["id"] for row in template["items"]}
        assert len(ids) == len(template["items"]) and not (all_ids & ids)
        all_ids |= ids
        assert template["model_calls"] == template["governance_writes"] == 0
        report[key] = {"scientific": len(science), "calibration": 12, "strata": dict(counts)}

    assert set(report["deadline"]["strata"]) == {
        f"{form}.{state}" for form in ("start-by", "complete-by")
        for state in ("queue-only", "started-unfinished", "successful-completion", "terminal-failure")
    }
    assert set(report["disjunction"]["strata"]) == {
        f"{form}.{outcome}" for form in ("or-both", "not-both")
        for outcome in ("neither", "left-only", "right-only", "both")
    }
    assert set(report["polarity"]["strata"]) == {
        f"{form}.{kind}" for form in ("true-as-worded", "false-as-worded")
        for kind in ("positive", "contracted-negative", "uncontracted-not", "lexical-negative", "scoped-quantifier", "double-negation")
    }
    out = {
        "kind": "dexagon.ainglish.flagship-modern-carrier-audit.v3",
        "status": "frozen_waiting_external_gates",
        "published_commit_pinned": all("REPLACE_AFTER_FIRST_COMMIT" not in (
            ROOT / f"{key}.template.json"
        ).read_text(encoding="utf-8") for key in KEYS),
        "templates": report,
        "unique_item_ids": len(all_ids),
        "model_calls": 0,
        "governance_writes": 0,
    }
    out["content_sha256"] = hashlib.sha256(canonical(out)).hexdigest()
    (ROOT / "audit.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
