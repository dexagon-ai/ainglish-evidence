#!/usr/bin/env python3
"""Audit scalar-only settlement cancellation without network or governance calls."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REL_TOL = 0.10
ABS_TOL = 0.02


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    sealed = dict(value)
    expected = sealed.pop("content_sha256")
    assert hashlib.sha256(canonical(sealed)).hexdigest() == expected
    return value


def pooled(values: dict[str, float], weights: dict[str, int]) -> float:
    return sum(values[name] * weights[name] for name in values) / sum(weights.values())


def main() -> None:
    snapshot = checked(ROOT / "snapshot.json")
    keys = set(snapshot["new_measurement_keys"])
    forbidden = {"per_form", "per_stratum", "strata", "cell_results", "form_values"}
    assert not keys & forbidden
    assert {"value", "replicates_hash", "per_member", "manifest"} <= keys
    assert "within tolerance" in snapshot["targets"]["preference"]["replicate_note"]
    assert "strictly outnumber" in snapshot["replication_settlement"]
    witnesses = {}
    shifts_by_count = {
        2: (-30.0, 30.0),
        3: (-30.0, 15.0, 15.0),
    }
    for name, target in snapshot["targets"].items():
        assert target["metric"] == "comprehension_accuracy_delta"
        assert target["proposal_slug"] == target["slug"]
        assert target["settlement_state"] == "awaiting"
        carrier_path = (ROOT / target["carrier"]).resolve()
        carrier = json.loads(carrier_path.read_text(encoding="utf-8"))
        rows = [row for row in carrier["items"] if not row.get("calibration")]
        weights = dict(Counter(row["form"] for row in rows))
        assert weights == target["expected_forms"]
        original = {form: float(target["value"]) for form in weights}
        shifts = shifts_by_count[len(weights)]
        replication = {
            form: float(target["value"]) + shifts[index]
            for index, form in enumerate(weights)
        }
        original_scalar = pooled(original, weights)
        replication_scalar = pooled(replication, weights)
        tolerance = max(ABS_TOL, REL_TOL * abs(original_scalar))
        scalar_agrees = abs(replication_scalar - original_scalar) <= tolerance
        per_form_agrees = {
            form: abs(replication[form] - original[form]) <= tolerance for form in weights
        }
        assert scalar_agrees and not all(per_form_agrees.values())
        assert abs(replication_scalar - original_scalar) < 1e-9
        witnesses[name] = {
            "weights": weights,
            "original_scalar": round(original_scalar, 4),
            "replication_scalar": round(replication_scalar, 4),
            "scalar_tolerance": round(tolerance, 4),
            "scalar_reproduced_ok": scalar_agrees,
            "synthetic_per_form_values": {
                form: round(value, 4) for form, value in replication.items()
            },
            "per_form_reproduced_ok": per_form_agrees,
            "largest_hidden_form_shift_pp": max(abs(value) for value in shifts),
        }
    report = {
        "kind": "dexagon.ainglish.multiform-scalar-settlement-audit.v1",
        "status": "blocked",
        "targets": witnesses,
        "finding": (
            "The live write and settlement surfaces can mark a pooled scalar as reproduced while "
            "one or more load-bearing forms disagree by 30 percentage points."
        ),
        "safe_action": (
            "Do not launch these three pooled replications until settlement binds per-form values, "
            "or supersede the originals with separately filed per-form estimands."
        ),
        "network_calls": 0,
        "governance_writes": 0,
        "model_calls": 0,
    }
    report["content_sha256"] = hashlib.sha256(canonical(report)).hexdigest()
    (ROOT / "audit.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
