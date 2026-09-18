"""Audit the frozen 09-18 successor without modifying it or writing to APIs.

First run the author's reference/census into a SEPARATE reproduction directory,
and the companion PHP oracle against the pinned register source. See README.
This is a report-only review, not a preregistered UVF measurement.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

PACKET_MANIFEST_SHA256 = "657935dcac83d7fc8a5017998d2c5589c64ecbf8e5c86d0149032fc7e46d1059"
PIN = "dc9ca5b2d2d98bfbbf8a9e78dec503dea60edae1"


def load(path):
    return json.loads(path.read_text())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def verify_packet(packet):
    manifest = (packet / "MANIFEST.sha256").read_bytes()
    assert digest(manifest) == PACKET_MANIFEST_SHA256
    checked, skipped = [], []
    for line in manifest.decode().splitlines():
        expected, relative = line.split(maxsplit=1)
        relative = relative.lstrip("*")
        target = (packet / relative).resolve()
        assert target.is_relative_to(packet.resolve()), relative
        # Never download or execute someone else's compiled Python cache.
        if not target.is_file() and "__pycache__" in target.parts:
            skipped.append(relative)
            continue
        assert digest(target.read_bytes()) == expected, relative
        checked.append(relative)
    return {"verified_files": len(checked), "intentionally_omitted_bytecode": skipped}


def normalise_census(value):
    result = json.loads(json.dumps(value))
    # glob() ordering is filesystem dependent; this list is an enumeration, not
    # a ranking or declared contract order. Preserve all its entries and values.
    result["classes"]["cad_at_least_list"].sort(key=lambda row: row[0])
    return result


def legacy_mismatches(fixture, oracle):
    before = {row["hash"][:8]: row for row in oracle["observations"]}
    comparisons = []
    for contract in fixture["reference"]:
        for row in contract["rows"]:
            known = before[row["hash"]]
            comparisons.append({
                **known,
                "reference_before": row["before_0_37_0"],
                "reference_after": row["after"],
                "matches_real_legacy": row["before_0_37_0"] == known["legacy_prerequisite_stance"],
            })
    assert len(comparisons) == len(before), "oracle/fixture populations differ"
    return comparisons


def pooled_witnesses(counterfactual, rows, widths):
    result = []
    for pair in counterfactual:
        original = rows[pair["orig_hash"]]
        replica = rows[pair["rep_hash"]]
        olo, ohi = widths[pair["orig_hash"]]["pooled"]
        rlo, rhi = widths[pair["rep_hash"]]["pooled"]
        intersects = olo <= rhi and rlo <= ohi
        if pair["counterfactual"] == "agree" and not intersects:
            result.append({
                "original": pair["orig_hash"], "replica": pair["rep_hash"],
                "proposal": original["proposal"]["public_id"],
                "served_original_pooled": [original["value_lo"], original["value_hi"]],
                "served_replica_pooled": [replica["value_lo"], replica["value_hi"]],
                "replayed_original_pooled": [olo, ohi],
                "replayed_replica_pooled": [rlo, rhi],
                "current_commensurability": replica["replication_comparison"]["commensurability"]["verdict"],
                "stratum_intersections": pair["strata"],
                "reference_counterfactual": pair["counterfactual"],
                "question": "Does opted settlement retain pooled intersection as well as every stratum? The reference omits the pooled gate.",
                "scope": "Hypothetical opt-in only; these legacy rows do not acquire the new identity.",
            })
    return result


def audit(packet, reproduction, oracle):
    integrity = verify_packet(packet)
    rows = {row["manifest_hash"]: row for row in map(load, (packet / "raw/measurements").glob("*.json"))}
    hashes = (packet / "raw/population_manifest_hashes.txt").read_text().splitlines()
    population = load(packet / "raw/population.json")
    assert hashes == sorted(rows) and len(hashes) == population["measurements"] == 1382
    assert digest("\n".join(hashes).encode()) == population["digest_newline"]
    assert len(list((packet / "raw/proposals").glob("*.json"))) == population["proposals"] == 274
    replays = {}
    for relative in ["reference_outcomes.json", "census/widths.json", "census/counterfactual.json", "census/counterfactual_prior_pairs.json", "census/surfaces_before.json"]:
        actual = load(reproduction / relative)
        expected = load(packet / Path(relative).name)
        assert actual == expected, relative
        replays[relative] = {"json_equal": True, "canonical_sha256": digest(canonical(actual).encode())}
    reproduced_census = load(reproduction / "census/census.json")
    published_census = load(packet / "census.json")
    assert normalise_census(reproduced_census) == normalise_census(published_census)
    reference = load(reproduction / "reference_outcomes.json")
    seeds = load(reproduction / "seed-stability.json")
    assert [row["seed"] for row in seeds] == [0, 1, 2, 3]
    for row in seeds:
        assert row["exit_code"] == 0
        assert load(reproduction / f'reference-seed-{row["seed"]}.json') == reference
    comparisons = legacy_mismatches(reference["F10"], oracle)
    cf = load(reproduction / "census/counterfactual.json")
    widths = load(reproduction / "census/widths.json")
    witnesses = pooled_witnesses(cf, rows, widths)
    return {
        "kind": "ainglish.reference-successor-audit.report-only.v1",
        "source_commit": PIN,
        "manifest_sha256": PACKET_MANIFEST_SHA256,
        "integrity": integrity,
        "population": population,
        "reproductions": replays,
        "census_equal_except_unordered_contract_listing": True,
        "author_fixtures_passing": sum(row["match"] for row in reference.values()),
        "python_hash_seed_stability": seeds,
        "legacy_receipt_projection_control": reference["legacy_receipt_control"]["reference"],
        "bootstrap_control": reproduced_census["width_summary"],
        "counterfactual_counts": dict(Counter(row["counterfactual"] for row in cf)),
        "F10_actual_register_comparisons": comparisons,
        "F10_actual_register_mismatch_count": sum(not row["matches_real_legacy"] for row in comparisons),
        "F10_empty_contract_count": sum(not row["rows"] for row in reference["F10"]["reference"]),
        "pooled_gate_policy_witnesses": witnesses,
        "counterfactual_if_pooled_gate_retained": {
            "agree": sum(row["counterfactual"] == "agree" for row in cf) - len(witnesses),
            "oppose": sum(row["counterfactual"] == "oppose" for row in cf) + len(witnesses),
        },
        "actual_uvf_measured": False,
        "formal_attempt_or_measurement_filed": False,
        "boundary": "Audit of a published reference, not a candidate production implementation. Existing register labels were not changed. No GPU or reader calls.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--reproduction", type=Path, required=True)
    parser.add_argument("--oracle", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.packet, args.reproduction, load(args.oracle))
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ["integrity", "author_fixtures_passing", "F10_actual_register_mismatch_count", "counterfactual_counts", "counterfactual_if_pooled_gate_retained", "actual_uvf_measured"]}, indent=2))
