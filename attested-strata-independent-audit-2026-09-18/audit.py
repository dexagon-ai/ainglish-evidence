"""Audit a pinned public reference packet; no inference or register writes.

Run: python audit.py /path/to/reticuli-packet /path/to/output.json
The supplied packet is never modified. Executable fixture replays use fresh
temporary copies and record the Python hash seed explicitly.
"""
from __future__ import annotations

import ast
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import tempfile

PIN = "fb2e22d88db9def8871e5eb7b83f630b28bd2541"
MANIFEST = "e76e9d863819bb98c41d0b75b6d567ff91e6ce18f9275251e0ee75a40228f477"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def definitions(path):
    """Load only reference functions/constants, not its writing fixture driver."""
    tree = ast.parse(path.read_text())
    allowed = {"IDENTITY", "SERVER_TOLERANCE", "ROW_F4_WORDING"}
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) or (
        isinstance(n, ast.Assign) and all(isinstance(t, ast.Name) and t.id in allowed for t in n.targets)
    )]
    scope = {}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), scope)
    return scope


def audit(root):
    raw = (root / "MANIFEST.sha256").read_bytes()
    assert sha(raw) == MANIFEST
    checked = []
    for line in raw.decode().splitlines():
        expected, filename = line.split(maxsplit=1)
        assert Path(filename).name == filename
        assert sha((root / filename).read_bytes()) == expected, filename
        checked.append(filename)
    pop = json.loads((root / "population.json").read_text())
    hashes = (root / "population_manifest_hashes.txt").read_text().splitlines()
    assert hashes == sorted(set(hashes))
    assert len(hashes) == pop["measurements"] == 1370
    assert sha("\n".join(hashes).encode()) == pop["digest_newline"]
    surfaces = json.loads((root / "surfaces_before.json").read_text())
    census = json.loads((root / "census.json").read_text())
    assert len(surfaces) == census["uvf"]["verdict_surfaces_counted"] == 3013
    assert sha(json.dumps(surfaces, sort_keys=True, separators=(",", ":")).encode()) == census["uvf"]["surfaces_before_sha256"]

    runs = []
    for seed in range(12):
        with tempfile.TemporaryDirectory(prefix="ainglish-reference-replay-") as tmp:
            for filename in ("reference.py", "replay.py"):
                shutil.copy2(root / filename, Path(tmp) / filename)
            result = subprocess.run(
                [sys.executable, str(Path(tmp) / "reference.py")],
                env={**os.environ, "PYTHONHASHSEED": str(seed)},
                text=True, capture_output=True, timeout=30, check=True,
            )
            outcomes = json.loads((Path(tmp) / "reference_outcomes.json").read_text())
            f3d = outcomes["F3d"]
            runs.append({"python_hash_seed": seed, "F3d": f3d,
                         "all_match": all(x["match"] for x in outcomes.values()),
                         "outcomes_sha256": sha(json.dumps(outcomes, sort_keys=True).encode()),
                         "stderr": result.stderr})
    ref = definitions(root / "reference.py")
    opted = {"settlement_analysis": "attested-strata-v1"}
    deg = {"manifest": opted, "attested": True,
           "strata": [{"id": "one", "value_lo": 0, "value_hi": 0,
                       "arms": {"english": 1, "ainglish": 1}}]}
    pair_result = ref["settle_pair"](deg, deg)
    prereq = {"metric": "comprehension_accuracy_delta", "at_least": -5,
              "bound_reading": "attested_interval_v1"}
    # Contract-unit witness, not a claim that this is a filed attested journal.
    pooled_witness = {"manifest": opted, "attested": True, "value": 0,
                      "value_lo": -6, "value_hi": 2,
                      "strata": [{"id": "one", "value_lo": -4, "value_hi": 2,
                                  "arms": {"english": .7, "ainglish": .7}}]}
    widths = json.loads((root / "widths.json").read_text())
    all_widths = [s["width"] for row in widths.values() for s in (row["strata"] or {}).values()]
    width_summary = {"rows": len(widths), "stratum_intervals": len(all_widths),
                     "median": statistics.median(all_widths), "zero_width": all_widths.count(0)}
    assert width_summary["stratum_intervals"] == census["width_summary"]["stratum_intervals"] == 562
    assert width_summary["median"] == census["width_summary"]["width_median"]
    prefix = {h[:8]: h for h in widths}
    assert len(prefix) == len(widths)
    reported = json.loads((root / "counterfactual_if_opted.json").read_text())
    comparisons = []
    for pair in reported:
        orig, rep = widths[prefix[pair["orig"]]], widths[prefix[pair["rep"]]]
        def as_ref(row):
            return {"manifest": opted, "attested": True,
                    "strata": [{"id": sid, "value_lo": s["lo"], "value_hi": s["hi"],
                                "arms": row["arms_by_stratum"].get(sid)}
                               for sid, s in row["strata"].items()]}
        outcome = ref["settle_pair"](as_ref(orig), as_ref(rep))[1]
        label = "agree" if outcome["reproduced_ok"] is True else "oppose" if outcome["reproduced_ok"] is False else "hold"
        comparisons.append({"orig": pair["orig"], "rep": pair["rep"],
                            "census": pair["counterfactual"], "reference": label})
    source = (root / "reference.py").read_text()
    published = json.loads((root / "reference_outcomes.json").read_text())
    return {
        "kind": "ainglish.reference-audit.report-only.v1", "source_commit": PIN,
        "files_hash_verified": checked, "population_preimage_verified": pop,
        "surface_projection_digest_verified": census["uvf"]["surfaces_before_sha256"],
        "raw_frozen_rows_in_packet": (root / "measurements").exists(),
        "raw_frozen_proposals_in_packet": (root / "proposals").exists(),
        "candidate_code_executed": False, "measurement_filed": False,
        "python_version": sys.version, "process_seed_replays": runs,
        "distinct_fixture_outcome_digests": len({r["outcomes_sha256"] for r in runs}),
        "F3d_match_counts": dict(Counter(str(r["F3d"]["match"]) for r in runs)),
        "F4": {"row_refusal_threshold": ref["ROW_F4_WORDING"],
               "reference_refusal_threshold": ref["SERVER_TOLERANCE"],
               "difference": .000105, "row_predicts_refusal": .000105 > ref["ROW_F4_WORDING"],
               "reference_predicts_refusal": .000105 > ref["SERVER_TOLERANCE"],
               "matcher_is_unconditional": '"F4": lambda g: True' in source},
        "F10_in_fixture_output": "F10" in published,
        "F11_matcher_is_unconditional": '"F11": lambda g: True' in source,
        "legacy_fixture_actual_values": {k: published[k]["reference"] for k in ("F3", "F3b", "F3c", "F11")},
        "degenerate_pair_reference": pair_result,
        "pooled_bound_unit_witness": {"input": pooled_witness, "reference_result": ref["stance"](prereq, pooled_witness),
                                      "declared_rule_result": "unresolved", "scope": "contract unit witness, not an attested execution"},
        "published_width_summary_recount": width_summary,
        "counterfactual_census_counts": dict(Counter(r["census"] for r in comparisons)),
        "counterfactual_reference_counts": dict(Counter(r["reference"] for r in comparisons)),
        "counterfactual_disagreements": [r for r in comparisons if r["census"] != r["reference"]],
        "boundary": "Checks reference reproducibility and contract fidelity, not a zero-flip measurement or language performance."
    }


if __name__ == "__main__":
    result = audit(Path(sys.argv[1]))
    Path(sys.argv[2]).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ["distinct_fixture_outcome_digests", "F3d_match_counts", "F4", "F10_in_fixture_output", "degenerate_pair_reference", "counterfactual_census_counts", "counterfactual_reference_counts"]}, indent=2))
