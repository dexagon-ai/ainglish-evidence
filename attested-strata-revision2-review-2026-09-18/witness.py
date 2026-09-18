#!/usr/bin/env python3
"""Bounded offline review of pinned revision 2; synthetic metadata is never submitted."""

import argparse
import copy
import hashlib
import importlib
import json
from pathlib import Path
import sys


PINS = {
    "candidate.py": "27792949f625a30efa3ba04b62c7c2ad8a0d00f55ec59372fbf44a3e3ca7c11c",
    "reference.py": "966d49ed13a264834674d9d1cc0e10c2bae93e2a8886cfc9514d954b6f38e3f2",
    "oracle.py": "2ec5cbeeb6155a865fbf2efd177bcd9a4d24d29b2baafd437ccfb8271c36866f",
    "MANIFEST.sha256": "eb795e6aaf6ac43b7d261b832bebce344c695325035ef2059b93f2d7ab8c438b",
}


def diff(before, after):
    assert set(before) == set(after)
    return [{"surface": key, "before": before[key], "after": after[key]}
            for key in sorted(before) if before[key] != after[key]]


def run(packet):
    for name, expected in PINS.items():
        assert hashlib.sha256((packet / name).read_bytes()).hexdigest() == expected, name
    sys.path.insert(0, str(packet))
    candidate = importlib.import_module("candidate")
    reference = importlib.import_module("reference")
    rows, props = candidate.load(str(packet / "raw"))
    before = json.loads((packet / "surfaces_before.json").read_text())
    after, report = candidate.transform(rows, props, before)
    legacy_diff = diff(before, after)
    assert not legacy_diff and len(before) == 3038

    # Reproduce the author's positive-control selection, in memory. Do not use
    # inject_control(): this review never deletes or changes any source snapshot.
    choices = sorted(h for h, m in rows.items()
                     if m.get("is_replication")
                     and (m.get("replication_comparison") or {}).get("rule_applied") == "interval-overlap-commensurable-v1"
                     and (m.get("replication_comparison") or {}).get("aggregate_reproduced_ok") is True
                     and m.get("reproduced_ok") is False
                     and rows.get(m.get("replicates_hash"))
                     and m.get("interval_provenance_attestation")
                     and rows[m["replicates_hash"]].get("interval_provenance_attestation"))
    rep_hash = choices[0]
    original_hash = rows[rep_hash]["replicates_hash"]
    injected = dict(rows)
    for h in (rep_hash, original_hash):
        injected[h] = copy.deepcopy(rows[h])
        injected[h]["manifest"]["settlement_analysis"] = reference.IDENTITY
    positive_after, positive_report = candidate.transform(injected, props, before)
    positive_diff = diff(before, positive_after)
    assert len(positive_diff) == 1
    assert positive_diff[0]["surface"] == "m:" + rep_hash
    assert positive_diff[0]["before"]["reproduced_ok"] is False
    assert positive_diff[0]["after"]["reproduced_ok"] is True

    # The exact real pooled-disjoint witness from the previous review must fail.
    orig = next(m for h, m in rows.items() if h.startswith("fb5835e0"))
    rep = next(m for h, m in rows.items() if h.startswith("895db45a"))
    widths = {}
    orig_view = candidate.attested_row(orig, widths)
    rep_view = candidate.attested_row(rep, widths)
    for view in (orig_view, rep_view):
        view["manifest"] = dict(view["manifest"], settlement_analysis=reference.IDENTITY)
    branch, pooled = reference.settle_pair(orig_view, rep_view)
    assert branch == "new_branch" and pooled == {"reproduced_ok": False, "failing_stratum": "pooled"}

    # This is an expressly synthetic prospective opt-in based on retained cells,
    # not a changed historical measurement or a mint-valid submission.
    support_source = next(m for h, m in rows.items() if h.startswith("b2d2e231ec71"))
    slug = "synthetic-unconfirmed-only"
    metric = "comprehension_accuracy_delta"
    key = "p:" + slug
    baseline = {key: {"stage": "seconded", "readiness_satisfied": [],
                      "readiness_missing": [], "readiness_unresolved": [metric],
                      "readiness_opposing": []}}
    results = {}
    for confirmed in (False, True):
        m = copy.deepcopy(support_source)
        m.update(confirmed=confirmed, is_replication=False, replicates_hash=None,
                 evidence_state="valid", counts_toward_verdict=confirmed)
        m["manifest"]["settlement_analysis"] = reference.IDENTITY
        p = {"slug": slug, "measurements": [m], "evidence_contract": {
            "prerequisites": [{"metric": metric, "at_least": -5,
                               "bound_reading": "attested_interval_v1"}]}}
        observed, selected = candidate.transform({m["manifest_hash"]: m}, {slug: p}, baseline)
        results[str(confirmed).lower()] = {
            "input_confirmed": confirmed,
            "input_counts_toward_verdict": confirmed,
            "input_is_replication": False,
            "observed": observed[key],
            "satisfied": metric in observed[key]["readiness_satisfied"],
            "selected": selected,
        }
    assert results["false"]["satisfied"] is True, "The pinned confirmation-bypass witness changed"
    assert results["false"]["observed"] == results["true"]["observed"]
    return {
        "scope": "Offline reference review, not a formal UVF measurement or production transition",
        "commit": "6cb5100b19de1b264d1e6f49ba160b4aa49096e5",
        "pins": PINS,
        "legacy_snapshot": {"surfaces": len(before), "changes": legacy_diff, "selected": report},
        "positive_control": {"original": original_hash, "replica": rep_hash,
                             "changes": positive_diff, "selected": positive_report},
        "pooled_witness": {"original": orig["manifest_hash"], "replica": rep["manifest_hash"], "result": pooled},
        "confirmation_witness": {"retained_cell_source": support_source["manifest_hash"],
                                 "synthetic_not_submit_ready": True,
                                 "expected_unconfirmed_satisfied": False,
                                 "runs": results},
        "source_snapshot_modified": False,
        "reader_calls": 0,
        "minted_attempts": 0,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.packet.resolve())
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"legacy_changes": len(result["legacy_snapshot"]["changes"]),
                      "positive_control_changes": len(result["positive_control"]["changes"]),
                      "pooled_witness": result["pooled_witness"]["result"],
                      "unconfirmed_source_incorrectly_satisfies": result["confirmation_witness"]["runs"]["false"]["satisfied"]}))


if __name__ == "__main__":
    main()
