#!/usr/bin/env python3
"""Audit the identity-relation carrier without reader or governance calls."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT.parent
FORMS = ("same-one", "same-kind", "same-name")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def verify_seal(value: dict) -> None:
    unsigned = dict(value)
    expected = unsigned.pop("content_sha256")
    assert hashlib.sha256(canonical(unsigned)).hexdigest() == expected


def main() -> None:
    artifact = json.loads((ROOT / "identity-relation.items.json").read_text(encoding="utf-8"))
    template = json.loads((ROOT / "identity-relation.template.json").read_text(encoding="utf-8"))
    index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    verify_seal(template)
    verify_seal(index)
    assert artifact["items"] == template["items"]
    assert hashlib.sha256(canonical(artifact["items"])).hexdigest() == artifact["sha256"]
    assert artifact["sha256"] == template["items_artifact"]["items_sha256"] == index["items_sha256"]

    scientific = [row for row in artifact["items"] if not row.get("calibration")]
    calibration = [row for row in artifact["items"] if row.get("calibration")]
    assert len(scientific) == 144 and len(calibration) == 12
    counts = Counter(row["settlement_stratum"] for row in scientific)
    assert len(counts) == 6 and set(counts.values()) == {24}
    assert set(counts) == {f"{form}.{polarity}" for form in FORMS for polarity in ("positive", "negative")}
    assert Counter(row["answer"] for row in scientific) == Counter({"yes": 72, "no": 72})
    assert Counter(row["options"].index(row["answer"]) for row in scientific) == Counter({0: 48, 1: 48, 2: 48})

    for form in FORMS:
        source = json.loads((EVIDENCE / "flagship-carrier-bank-2026-08-26" / f"items-{form}.json").read_text(encoding="utf-8"))
        assert source["sha256"] == template["source_form_digests"][form]
        expected = [row for row in source["items"] if not row.get("calibration")]
        observed = [{key: value for key, value in row.items() if key not in ("form", "settlement_stratum")}
                    for row in scientific if row["form"] == form]
        assert observed == expected

    forbidden = set(FORMS)
    assert all(not any(marker in (row["english"] + row["ainglish"]) for marker in forbidden)
               for row in calibration)
    published = template["items_artifact"]["published_url"]
    runnable_url = "REPLACE_AFTER_FIRST_COMMIT" not in published
    print(json.dumps({
        "status": "passed",
        "scientific_items": len(scientific),
        "calibration_items": len(calibration),
        "settlement_strata": dict(sorted(counts.items())),
        "source_items_preserved_exactly": True,
        "answer_positions": dict(sorted(Counter(row["options"].index(row["answer"]) for row in scientific).items())),
        "published_url_final": runnable_url,
        "model_calls": 0,
        "governance_writes": 0,
        "content_sha256": index["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
