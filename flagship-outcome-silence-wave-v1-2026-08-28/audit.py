#!/usr/bin/env python3
"""Fail closed on wave balance, comparator integrity, no-spend dispositions, and seals."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PLACEHOLDER = "REPLACE_AFTER_FIRST_COMMIT"
GENERATED = [
    "proposal-snapshot.json", "test-outcome.items.json", "silence-default.items.json",
    "test-outcome-bare-diagnostic.json", "test-outcome-validity-diagnostic.json",
    "silence-default-bare-diagnostic.json", "silence-default-boundary-diagnostic.json",
    "test-outcome.template.json", "silence-default.template.json", "index.json",
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def load(name: str) -> dict:
    value = json.loads((ROOT / name).read_text(encoding="utf-8"))
    unsigned = dict(value)
    expected = unsigned.pop("content_sha256")
    assert hashlib.sha256(canonical(unsigned)).hexdigest() == expected, name
    return value


def primary(name: str, forms: set[str], seams: set[str], markers: set[str], allow_placeholder: bool) -> dict:
    artifact = load(f"{name}.items.json")
    template = load(f"{name}.template.json")
    items = artifact["items"]
    assert items == template["items"]
    assert hashlib.sha256(canonical(items)).hexdigest() == template["items_artifact"]["items_sha256"]
    calibration = [row for row in items if row.get("calibration")]
    scientific = [row for row in items if not row.get("calibration")]
    assert len(calibration) == 12 and len(scientific) == 96
    assert len({row["id"] for row in items}) == len(items)
    counts = Counter(row["settlement_stratum"] for row in scientific)
    assert set(counts) == {f"{form}.{seam}" for form in forms for seam in seams}
    assert set(counts.values()) == {8}
    for row in items:
        assert row["answer"] in row["options"] and len(row["options"]) == len(set(row["options"]))
        assert row["english"] != row["ainglish"]
    for row in scientific:
        assert row["form"] in forms
        assert row.get("semantic_seam", row.get("addressee_behaviour")) in seams
        assert row["form"] in row["ainglish"]
        assert all(marker not in row["english"] for marker in markers)
        assert all(marker not in row["question"] for marker in markers)
        if name == "silence-default":
            assert "evaluat" in row["english"].lower()
            if row["form"] == "hold-until-yes" and row["addressee_behaviour"] == "approve":
                assert row["answer"] == "cannot determine"
    assert template["activation"]["runnable"] is False
    assert template["panel_neff"] == 2
    assert template["model_calls"] == template["governance_writes"] == 0
    url = template["items_artifact"]["published_url"]
    if allow_placeholder:
        assert PLACEHOLDER in url
    else:
        assert PLACEHOLDER not in url and "/main/" not in url
    return {"scientific": 96, "calibration": 12, "strata": len(counts), "per_stratum": 8}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-placeholder", action="store_true")
    args = parser.parse_args()
    snapshot = load("proposal-snapshot.json")
    assert snapshot["answer_bearing_items_generated_before_snapshot"] is False
    test = primary(
        "test-outcome", {"test-run", "test-passed"},
        {"terminal_execution", "declared_acceptance", "all_subchecks", "broader_fitness", "current_fitness", "independent_verification"},
        {"test-run", "test-passed"}, args.allow_placeholder,
    )
    silence = primary(
        "silence-default", {"go-unless-no", "hold-until-yes"},
        {"silent", "decline", "defer", "question", "approve", "late_decline"},
        {"go-unless-no", "hold-until-yes"}, args.allow_placeholder,
    )
    for name, count in (
        ("test-outcome-bare-diagnostic.json", 96),
        ("test-outcome-validity-diagnostic.json", 16),
        ("silence-default-bare-diagnostic.json", 96),
        ("silence-default-boundary-diagnostic.json", 16),
    ):
        sidecar = load(name)
        assert sidecar["governance_metric"] is None and len(sidecar["items"]) == count
        assert all(row["descriptive_only"] is True for row in sidecar["items"])
    index = load("index.json")
    assert index["fresh_answer_bearing_items"] == 192
    assert index["dispositions"]["some-or-all"]["action"] == "do_not_add_same_principal_reader_run"
    assert index["dispositions"]["some-or-all"]["existing_comprehension_hashes"]
    assert index["dispositions"]["may-as"]["action"] == "do_not_spend_reader"
    assert "token_delta" in index["dispositions"]["may-as"]["opposing_evidence"]
    assert index["model_calls"] == index["tokenizer_calls"] == index["attempt_mints"] == index["governance_writes"] == 0
    audit = {
        "kind": "dexagon.ainglish.flagship-outcome-silence-wave-audit.v1",
        "proposal_snapshot_sha256": snapshot["content_sha256"], "test_outcome": test,
        "silence_default": silence, "complete_careful_english_required": True,
        "bare_diagnostics_excluded_from_governance_metric": True,
        "adverse_or_disputed_rows_not_spent": True,
        "all_answer_bearing_inputs_frozen_before_reader_calls": True,
        "model_calls": 0, "tokenizer_calls": 0, "attempt_mints": 0, "governance_writes": 0,
    }
    audit["content_sha256"] = hashlib.sha256(canonical(audit)).hexdigest()
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    names = GENERATED + ["audit.json"]
    (ROOT / "SHA256SUMS").write_text("\n".join(
        f"{hashlib.sha256((ROOT / name).read_bytes()).hexdigest()}  {name}" for name in names
    ) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
