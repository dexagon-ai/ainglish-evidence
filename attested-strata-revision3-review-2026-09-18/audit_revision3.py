#!/usr/bin/env python3
"""Pinned, offline revision-3 re-review; never a formal measurement or API write."""
import argparse
import copy
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys

COMMIT = "cd1be2a0f59aa49e1e7a4cf417ccf10240c13aa1"
PINS = {
    "candidate.py": "cc9dc690830a4b9b1247baa63d4469cb7398e535154aa81a3def332685ba9b74",
    "reference.py": "f102a9f80fc53318de99df0a6352f52069c7b6da385d3a02f148f3d090583dd0",
    "oracle.py": "2ec5cbeeb6155a865fbf2efd177bcd9a4d24d29b2baafd437ccfb8271c36866f",
    "replay.py": "b39a98d55aaafd12781d3d4ccd171113eea0b72cdbdbc8fe7bf064a6c5958a5d",
    "MANIFEST.sha256": "b5a7261c581b2e7b33cc4635abd35d0c761a1dfb45ca597e7ba4f73538556f79",
}

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def differences(before, after):
    assert set(before) == set(after)
    return [{"surface": k, "before": before[k], "after": after[k]}
            for k in sorted(before) if before[k] != after[k]]

def audit(packet, out):
    out.mkdir(parents=True, exist_ok=False)
    for name, expected in PINS.items():
        assert digest(packet / name) == expected, name
    manifests = []
    for line in (packet / "MANIFEST.sha256").read_text().splitlines():
        expected, name = line.split(maxsplit=1)
        relative = Path(name.strip().lstrip("*"))
        assert not relative.is_absolute() and ".." not in relative.parts
        assert digest(packet / relative) == expected, name
        manifests.append(name)
    previous = Path(__file__).with_name("revision2-reference-outcomes.json")
    assert digest(previous) == "3a6d5a80be3dcbb2443bbb87a5564cc37428ed11f76324537a198c5f1e5df775"
    previous_outcomes = json.loads(previous.read_text())
    published = json.loads((packet / "reference_outcomes.json").read_text())

    def seeded(seed):
        target = out / f"reference-seed-{seed}.json"
        process = subprocess.run(
            [sys.executable, "-B", str(packet / "reference.py"), "--raw", str(packet / "raw"), "--out", str(target)],
            env=os.environ | {"PYTHONHASHSEED": str(seed)}, capture_output=True, text=True, check=True,
        )
        (out / f"reference-seed-{seed}.log").write_text(process.stdout + process.stderr)
        value = json.loads(target.read_text())
        assert value == published
        assert len(value) == 28 and all(v["match"] for v in value.values())
        assert {k: value[k] for k in previous_outcomes} == previous_outcomes
        result = {"seed": seed, "checks": len(value), "all_passed": True,
                  "canonical_sha256": hashlib.sha256(canonical(value)).hexdigest(),
                  "unchanged_revision2_checks": len(previous_outcomes)}
        print("reference", json.dumps(result), flush=True)
        return result

    with ThreadPoolExecutor(max_workers=2) as pool:
        seeds = list(pool.map(seeded, range(4)))
    assert len({s["canonical_sha256"] for s in seeds}) == 1
    sys.path.insert(0, str(packet))
    candidate = importlib.import_module("candidate")
    reference = importlib.import_module("reference")
    rows, props = candidate.load(str(packet / "raw"))
    before = json.loads((packet / "surfaces_before.json").read_text())
    after, selection = candidate.transform(rows, props, before)
    assert len(before) == 3038 and differences(before, after) == []
    (out / "executed-surfaces-after.json").write_text(json.dumps(after, sort_keys=True))
    subprocess.run([sys.executable, "-B", str(packet / "oracle.py"), "--raw", str(packet / "raw"),
                    "--before", str(packet / "surfaces_before.json"), "--after", str(out / "executed-surfaces-after.json"),
                    "--label", "snapshot", "--out", str(out / "executed-oracle.json")], check=True)
    oracle = json.loads((out / "executed-oracle.json").read_text())["snapshot"]
    assert oracle["changed_surfaces"] == 0 and oracle["surfaces"] == 3038

    # Execute the new candidate controls; reading their saved JSON alone is not a test.
    controls = candidate.controls(rows)
    assert controls == json.loads((packet / "controls_result.json").read_text())
    assert controls["two_state"]["unconfirmed"]["bucket"] == "unresolved"
    assert controls["two_state"]["confirmed"]["bucket"] == "satisfied"
    assert controls["replication_only"]["bucket"] == "missing"

    # Re-run our prior witness's shape and additional exclusion guards independently
    # of the author's controls() construction. All altered metadata is synthetic.
    source = rows[candidate.CONTROL_SOURCE]
    metric = "comprehension_accuracy_delta"
    additional = {}
    cases = {
        "unconfirmed": ({"confirmed": False, "counts_toward_verdict": False}, "unresolved"),
        "confirmed": ({}, "satisfied"),
        "confirmed_but_not_counting": ({"counts_toward_verdict": False}, "unresolved"),
        "replication_only": ({"is_replication": True, "replicates_hash": "synthetic-absent"}, "missing"),
        "replication_hash_only": ({"replicates_hash": "synthetic-absent"}, "missing"),
        "voided": ({"voided_at": "2026-09-18T00:00:00Z"}, "missing"),
        "record_only": ({"evidence_state": "record_only"}, "missing"),
        "wrong_metric": ({"metric": "token_delta"}, "missing"),
    }
    for label, (changes, expected) in cases.items():
        m = copy.deepcopy(source)
        m.update(confirmed=True, counts_toward_verdict=True, is_replication=False,
                 replicates_hash=None, evidence_state="valid", voided_at=None, retraction=None)
        m.update(changes)
        m["manifest"]["settlement_analysis"] = reference.IDENTITY
        slug = "synthetic-independent-" + label
        key = "p:" + slug
        p = {"slug": slug, "measurements": [m], "evidence_contract": {"prerequisites": [
            {"metric": metric, "at_least": -5, "bound_reading": "attested_interval_v1"}]}}
        baseline = {key: {"stage": "seconded", "readiness_satisfied": [], "readiness_missing": [],
                          "readiness_unresolved": [metric], "readiness_opposing": []}}
        result, detail = candidate.transform({m["manifest_hash"]: m}, {slug: p}, baseline)
        assert detail["keyed_detail"][0]["bucket"] == expected, label
        assert (metric in result[key]["readiness_satisfied"]) == (expected == "satisfied")
        additional[label] = {"expected": expected, "observed": result[key], "detail": detail["keyed_detail"][0]}

    choices = sorted(h for h, m in rows.items() if m.get("is_replication")
                     and (m.get("replication_comparison") or {}).get("rule_applied") == "interval-overlap-commensurable-v1"
                     and (m.get("replication_comparison") or {}).get("aggregate_reproduced_ok") is True
                     and m.get("reproduced_ok") is False and rows.get(m.get("replicates_hash"))
                     and m.get("interval_provenance_attestation")
                     and rows[m["replicates_hash"]].get("interval_provenance_attestation"))
    replica = choices[0]; original = rows[replica]["replicates_hash"]
    injected = dict(rows)
    for h in (original, replica):
        injected[h] = copy.deepcopy(rows[h])
        injected[h]["manifest"]["settlement_analysis"] = reference.IDENTITY
    positive, positive_selection = candidate.transform(injected, props, before)
    positive_diff = differences(before, positive)
    assert len(positive_diff) == 1 and positive_diff[0]["surface"] == "m:" + replica
    assert positive_diff[0]["before"]["reproduced_ok"] is False and positive_diff[0]["after"]["reproduced_ok"] is True
    assert positive_selection["new_branch_pairs"] == [replica]

    result = {"scope": "Offline bounded re-review; not a formal protocol measurement or live transition",
              "commit": COMMIT, "pins": PINS, "manifest_files_verified": len(manifests), "seed_runs": seeds,
              "legacy_snapshot": {"surfaces": len(before), "changes": [], "selection": selection, "executed_oracle": oracle},
              "executed_author_controls": controls, "independent_exclusion_controls": additional,
              "positive_control": {"original": original, "replica": replica, "changes": positive_diff},
              "confirmation_bypass_closed": True, "f10_request": "No new fixture required; accepted row-level baseline remains unchanged",
              "reader_calls": 0, "minted_attempts": 0, "formal_measurements": 0, "raw_snapshot_changed": False}
    (out / "audit-result.json").write_text(json.dumps(result, indent=2) + "\n")
    print("AUDIT_PASSED", json.dumps({"fixtures": 28, "independent_controls": len(cases), "manifest_files": len(manifests), "legacy_changes": 0, "positive_changes": 1}), flush=True)
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    audit(args.packet.resolve(), args.out.resolve())
