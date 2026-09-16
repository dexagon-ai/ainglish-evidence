"""Synthetic protocol-review diagnostics. No language items, model calls or API writes.

Uses installed SDK 0.2.61's actual counter stream and pooled estimator. The proposed
per-form extraction and outcome-order functions are review oracles, NOT deployed code.
"""
import hashlib
import json
import math
from importlib.metadata import version
from pathlib import Path

from ainglish import panel


def quantiles(values):
    ordered = sorted(values)
    if not ordered:
        return None
    return {
        "accepted_draws": len(ordered),
        "lower_index": 25 * len(ordered) // 1000,
        "upper_index": 975 * len(ordered) // 1000,
        "lower": ordered[25 * len(ordered) // 1000],
        "upper": ordered[975 * len(ordered) // 1000],
        "mean_of_draws": sum(ordered) / len(ordered),
    }


def synthetic_journal():
    seed, reader = 16092026, "synthetic-review-reader"
    items, rows = [], []
    for number in range(19):
        ident = f"numeric-alpha-{number:02d}"
        items.append({"id": ident, "answer": "correct", "settlement_stratum": "alpha"})
        rows.append((ident, panel.arm_for(seed, reader, ident), reader,
                     "correct" if number % 3 else "incorrect"))
    # The sparse second form has one cell in each arm. Its missing-arm bootstrap
    # draws make the distinction between local and common draw masks observable.
    for arm in ("english", "ainglish"):
        for suffix in range(1000):
            ident = f"numeric-beta-{arm}-{suffix}"
            if panel.arm_for(seed, reader, ident) == arm:
                items.append({"id": ident, "answer": "correct", "settlement_stratum": "beta"})
                rows.append((ident, arm, reader, "correct"))
                break
        else:
            raise AssertionError("synthetic allocation construction failed")
    return seed, [{"name": reader}], items, rows


def replay_masks():
    seed, readers, items, rows = synthetic_journal()
    contract = [{"id": "alpha", "share": .5}, {"id": "beta", "share": .5}]
    cells = panel._attested_accuracy_cells(rows, items, readers, seed)
    by_item = {item["id"]: [] for item in items}
    for cell in cells:
        by_item[cell["item_id"]].append(cell)
    sources = {row["id"]: sorted(item["id"] for item in items
                               if item["settlement_stratum"] == row["id"])
               for row in contract}
    local, joint, pooled = {s: [] for s in sources}, {s: [] for s in sources}, []
    for draw in range(panel.INTERVAL_BOOTSTRAP_DRAWS):
        sampled = {
            s: [ids[panel._attested_draw_index(seed, draw, position, len(ids), stratum=s)]
                for position in range(len(ids))]
            for s, ids in sources.items()
        }
        forms = {s: panel._attested_sample_value(by_item, ids)
                 for s, ids in sampled.items()}
        for s, value in forms.items():
            if value is not None:
                local[s].append(value)
        combined = [(s, ident) for s, ids in sampled.items() for ident in ids]
        headline = panel._attested_sample_value(by_item, combined, contract)
        if headline is not None:
            assert all(value is not None for value in forms.values())
            assert abs(headline - sum(.5 * value for value in forms.values())) < 1e-10
            pooled.append(headline)
            for s, value in forms.items():
                joint[s].append(value)
    sdk_lo, sdk_hi, receipt = panel.attested_bootstrap_accuracy(
        rows, items, readers, contract, seed=seed)
    pooled_report = quantiles(pooled)
    assert (sdk_lo, sdk_hi) == (pooled_report["lower"], pooled_report["upper"])
    assert receipt["algorithm"]["accepted_draws"] == len(pooled)
    assert len(local["alpha"]) > len(joint["alpha"])
    assert all(len(values) == len(pooled) for values in joint.values())
    journal_hash = hashlib.sha256(json.dumps(cells, sort_keys=True).encode()).hexdigest()
    return {
        "synthetic_only": True, "seed": seed, "items": len(items), "scored_cells": len(rows),
        "journal_sha256": journal_hash, "sdk_pooled_replay_equal": True,
        "local_mask": {s: quantiles(values) for s, values in local.items()},
        "common_pooled_mask": {s: quantiles(values) for s, values in joint.items()},
        "pooled": pooled_report,
    }


def required_form_decision(forms, threshold=-5):
    """Proposed precedence oracle, not current server behavior.

    None denotes a missing or method-inadmissible bound (including a held
    degenerate form). A valid upper bound below the floor refutes ALL-form success.
    """
    if not forms or not math.isfinite(threshold):
        raise ValueError("nonempty required forms and a finite threshold are required")
    for bound in forms:
        if bound is not None and (len(bound) != 2 or
                                  not all(math.isfinite(value) for value in bound) or
                                  bound[0] > bound[1]):
            raise ValueError("malformed interval is not a scientific opposing result")
    if any(bound is not None and bound[1] < threshold for bound in forms):
        return "opposes"
    if any(bound is None for bound in forms):
        return "unresolved"
    return "supports" if all(bound[0] >= threshold for bound in forms) else "unresolved"


def prospective_branch(original_opted, replica_opted):
    """Recommended branch-selection table, not evidence that it is implemented."""
    if not original_opted and not replica_opted:
        return "legacy_unchanged"
    if original_opted and replica_opted:
        return "new_rule_after_attestation_validation"
    return "mixed_generation_hold_not_legacy_reinterpretation"


def capacity():
    limit = panel.INTERVAL_PROVENANCE_MAX_CELLS
    assert limit == 5000, "Reassess the capacity note for this SDK version"
    refused = False
    try:
        panel._attested_accuracy_cells([None] * (limit + 1), [], [], 0)
    except ValueError as error:
        refused = "at most 5000 real cells" in str(error)
    assert refused
    return {
        "sdk_limit": limit, "limit_plus_one_refused_before_replay": refused,
        "prior_n1024_per_reader_arm_form_target_cells": 1024 * 2 * 2 * 2,
        "candidate_budget_not_sample_selection": {
            "semantic_worlds_per_form": 1200, "forms": 2, "readers": 2,
            "target_cells_per_run": 4800, "calibration_calls_per_run_if_32_items": 128,
            "two_runs_target_plus_calibration_calls": 9856,
            "excludes_qualification_and_separate_auxiliary_or_bare_controls": True,
        },
    }


def main():
    report = {
        "kind": "synthetic-protocol-review-witness-v1", "model_calls": 0,
        "not_an_official_measurement": True, "sdk_version": version("ainglish"),
        "draw_mask": replay_masks(), "capacity": capacity(),
        "proposed_branch_oracle": {
            f"{a}/{b}": prospective_branch(a, b)
            for a, b in ((False, False), (True, True), (False, True), (True, False))
        },
        "proposed_precedence_oracle": {
            "held_and_opposing": required_form_decision([None, (-12, -7)]),
            "held_and_supporting": required_form_decision([None, (-4, 2)]),
            "both_supporting": required_form_decision([(-5, 2), (-4, 1)]),
            "boundary_uncertain": required_form_decision([(-6, 2), (-4, 1)]),
        },
    }
    Path(__file__).with_name("witness.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
