#!/usr/bin/env python3
"""Fail closed on carrier balance, comparator completeness, digests, and current repeat binding."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
GENERATED = [
    "proposal-snapshot.json",
    "regime.items.json",
    "identity.items.json",
    "regime-bare-diagnostic.json",
    "identity-bare-diagnostic.json",
    "regime.template.json",
    "identity.template.json",
    "repeat-restore-current.template.json",
    "index.json",
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def load(name: str) -> dict:
    value = json.loads((ROOT / name).read_text(encoding="utf-8"))
    unsigned = dict(value)
    expected = unsigned.pop("content_sha256")
    assert hashlib.sha256(canonical(unsigned)).hexdigest() == expected, name
    return value


def audit_primary(name: str, forms: set[str], seams: set[str], markers: set[str], required: dict[str, tuple[str, ...]]) -> dict:
    artifact = load(f"{name}.items.json")
    template = load(f"{name}.template.json")
    assert artifact["items"] == template["items"]
    assert hashlib.sha256(canonical(artifact["items"])).hexdigest() == template["items_artifact"]["items_sha256"]
    items = artifact["items"]
    calibration = [row for row in items if row.get("calibration")]
    scientific = [row for row in items if not row.get("calibration")]
    assert len(calibration) == 12 and len(scientific) == 96
    assert len({row["id"] for row in items}) == len(items)
    counts = Counter(row["settlement_stratum"] for row in scientific)
    expected = {f"{form}.{seam}" for form in forms for seam in seams}
    assert set(counts) == expected and set(counts.values()) == {8}
    assert {row["form"] for row in scientific} == forms
    for row in items:
        assert row["answer"] in row["options"] and len(row["options"]) == len(set(row["options"]))
        assert row["english"] != row["ainglish"]
    for row in scientific:
        assert row["semantic_seam"] in seams
        assert row["form"] in forms
        assert row["form"] in row["ainglish"]
        assert all(marker not in row["english"] for marker in markers)
        assert all(marker not in row["question"] for marker in markers)
        assert all(fragment in row["english"] for fragment in required[row["form"]])
    assert template["model_calls"] == 0 and template["governance_writes"] == 0
    assert template["activation"]["runnable"] is False
    assert "REPLACE_AFTER_FIRST_COMMIT" not in template["items_artifact"]["published_url"], "publish and rebind before activation"
    return {"scientific": len(scientific), "calibration": len(calibration), "strata": len(counts), "per_stratum": 8}


def main() -> None:
    snapshot = load("proposal-snapshot.json")
    assert set(snapshot["proposals"]) == {
        "by-construction-by-rule-in-practice",
        "same-one-same-kind-same-name",
        "repeat-event-restore-state",
    }
    assert all(row["stage"] == "measured" for row in snapshot["proposals"].values())
    assert all(row["evidence_readiness"]["missing_evidence"] == ["comprehension_accuracy_delta"] for row in snapshot["proposals"].values())

    regime = audit_primary(
        "regime",
        {"by-construction", "by-rule", "in-practice"},
        {"exception_possible", "exception_consequence", "responsibility", "intent_nonclaim"},
        {"by-construction", "by-rule", "in-practice"},
        {
            "by-construction": ("because of how the mechanism is built", "exception cannot occur"),
            "by-rule": ("standing rule requires", "violation"),
            "in-practice": ("observed instance", "Nothing in this statement prevents"),
        },
    )
    identity = audit_primary(
        "identity",
        {"same-one", "same-kind", "same-name"},
        {"propagation", "relation_recovery", "later_divergence", "stronger_relation"},
        {"same-one", "same-kind", "same-name"},
        {
            "same-one": ("one single", "modification through either mention"),
            "same-kind": ("distinct", "verified equal", "can diverge afterward"),
            "same-name": ("matching identifier only", "not been checked or claimed"),
        },
    )
    for name in ("regime", "identity"):
        sidecar = load(f"{name}-bare-diagnostic.json")
        assert sidecar["governance_metric"] is None and len(sidecar["items"]) == 96
        assert all(row["descriptive_only"] is True for row in sidecar["items"])

    repeat = load("repeat-restore-current.template.json")
    source_template = json.loads((REPO / "manifest-bound-flagship-carriers-v1-2026-08-27/repeat-restore.template.json").read_text())
    source_unsigned = dict(source_template)
    source_hash = source_unsigned.pop("content_sha256")
    assert hashlib.sha256(canonical(source_unsigned)).hexdigest() == source_hash
    assert repeat["source_template"]["content_sha256"] == source_hash
    assert repeat["proposal_revision"] == repeat["slug"] == "repeat-event-restore-state"
    assert repeat["items"] == source_template["items"], "metadata-only rebind must not edit answers"
    source_items = json.loads((REPO / "manifest-bound-flagship-carriers-v1-2026-08-27/repeat-restore.items.json").read_text())
    assert hashlib.sha256(canonical(source_items["items"])).hexdigest() == repeat["items_artifact"]["items_sha256"]
    repeat_scientific = [row for row in repeat["items"] if not row.get("calibration")]
    repeat_counts = Counter(row["settlement_stratum"] for row in repeat_scientific)
    assert len(repeat_scientific) == 256 and len(repeat_counts) == 16 and set(repeat_counts.values()) == {16}
    directive_rows = [row for row in repeat_scientific if row.get("force") == "directive"]
    assert len(directive_rows) == 64 and any(row.get("directive_time_seam") for row in directive_rows)

    index = load("index.json")
    assert index["fresh_answer_bearing_items"] == 192
    assert index["reused_answer_bearing_items"] == 256
    assert index["model_calls"] == index["tokenizer_calls"] == index["attempt_mints"] == index["governance_writes"] == 0
    audit = {
        "kind": "dexagon.ainglish.flagship-regime-identity-recurrence-audit.v1",
        "proposal_snapshot_sha256": snapshot["content_sha256"],
        "regime": regime,
        "identity": identity,
        "repeat_restore": {
            "scientific": len(repeat_scientific),
            "strata": len(repeat_counts),
            "per_stratum": 16,
            "directive_rows": len(directive_rows),
            "answer_bearing_items_changed": False,
        },
        "complete_careful_english_required": True,
        "bare_diagnostics_excluded_from_governance_metric": True,
        "all_answer_bearing_inputs_frozen_before_reader_calls": True,
        "model_calls": 0,
        "tokenizer_calls": 0,
        "attempt_mints": 0,
        "governance_writes": 0,
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
