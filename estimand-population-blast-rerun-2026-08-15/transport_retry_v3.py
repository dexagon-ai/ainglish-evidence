#!/usr/bin/env python3
"""Transport-only successor for the v2 80-character label rejection."""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
from typing import Any

import rerun as base


ARTIFACT_DIR = Path(__file__).resolve().parent
PRIOR_ATTEMPT = "f39984a8-9a79-47e5-b8b2-3273eac05386"
RUNSPEC_PATH = ARTIFACT_DIR / "runspec-v3.json"
ATTEMPT_PATH = ARTIFACT_DIR / "attempt-v3.json"
V2_RUNSPEC = ARTIFACT_DIR / "runspec-v2.json"
V2_SNAPSHOT = ARTIFACT_DIR / "snapshot-v2.json"
V2_RESULT = ARTIFACT_DIR / "result-v2.json"
V2_FAILURE = ARTIFACT_DIR / "transport-failure-v2.json"
SHORT_MODEL = "dexagon-blast-rerun-v2@197d8de5"


def manifest() -> dict[str, Any]:
    spec = deepcopy(base.read_json(V2_RUNSPEC))
    old_models = spec["models"]
    spec["models"] = [SHORT_MODEL]
    spec["transport_successor"] = {
        "prior_attempt": PRIOR_ATTEMPT,
        "reason": "the API rejected the 110-character manifest.models label; the field maximum is 80",
        "only_change": {"models": {"from": old_models, "to": [SHORT_MODEL]}},
        "prior_snapshot_sha256": base.digest(base.read_json(V2_SNAPSHOT)),
        "prior_result_sha256": base.digest(base.read_json(V2_RESULT)),
        "transport_failure_sha256": base.digest(base.read_json(V2_FAILURE)),
        "result_known_before_successor": True,
        "no_rescan": "Reuse the exact successful v2 complete-population snapshot; changing any data or analysis is forbidden.",
    }
    spec["result_blind_at_freeze"] = False
    spec["result_blind_note"] = (
        "The complete v2 scan passed and returned zero before its HTTP write was rejected. "
        "This successor changes only the overlong instrument label and openly reuses that result."
    )
    return spec


def validate_inputs() -> tuple[dict[str, Any], dict[str, Any]]:
    snapshot = base.read_json(V2_SNAPSHOT)
    result = base.read_json(V2_RESULT)
    failure = base.read_json(V2_FAILURE)
    if base.digest(snapshot) != failure["substantive_snapshot_sha256"]:
        raise RuntimeError("v2 snapshot no longer matches the transport-failure receipt")
    if base.digest(result) != failure["substantive_result_sha256"]:
        raise RuntimeError("v2 result no longer matches the transport-failure receipt")
    if result.get("failures") != [] or result.get("unclaimed_verdict_flips") != 0:
        raise RuntimeError("v2 did not produce the declared successful zero-flip result")
    if snapshot.get("proposal_count") != base.EXPECTED_PROPOSALS:
        raise RuntimeError("v2 proposal denominator changed")
    if snapshot.get("measurement_occurrence_count") != base.EXPECTED_MEASUREMENTS:
        raise RuntimeError("v2 measurement denominator changed")
    if snapshot.get("settlement_buckets") != base.EXPECTED_BUCKETS:
        raise RuntimeError("v2 settlement buckets changed")
    if len(SHORT_MODEL) > 80:
        raise RuntimeError("replacement model label still violates the API limit")
    return snapshot, result


def freeze() -> None:
    if RUNSPEC_PATH.exists():
        raise SystemExit("refusing to overwrite the v3 transport-successor runspec")
    validate_inputs()
    spec = manifest()
    base.write_json(RUNSPEC_PATH, spec, exclusive=True)
    print(json.dumps({"runspec": str(RUNSPEC_PATH), "manifest_commitment": base.digest(spec)}, indent=2))


def validate_manifest(spec: dict[str, Any]) -> None:
    if spec != manifest():
        raise RuntimeError("the v3 runspec no longer matches the transport-only successor")


def mint() -> None:
    if ATTEMPT_PATH.exists():
        raise SystemExit("refusing to overwrite the v3 attempt receipt")
    validate_inputs()
    spec = base.read_json(RUNSPEC_PATH)
    validate_manifest(spec)
    receipt = base.ainglish_client().mint_attempt(
        base.SLUG,
        manifest=spec,
        estimand=(
            "transport-only successor: the exact v2 complete-population snapshot and zero-flip "
            "result, changing only a 110-character instrument label to a 35-character label"
        ),
        admissibility_gates=[
            "v2 snapshot hash, result hash, 114-proposal denominator, 203-occurrence denominator and all five buckets match exactly",
            "v2 result has no failed gate and unclaimed_verdict_flips=0",
            "the only runspec change is the manifest.models label and the transport-successor disclosure",
            "the replacement label is at most 80 characters",
            "no data is fetched again and no outcome, input, gate, population or analysis field changes",
        ],
        planned_sample={
            "snapshot_sha256": base.digest(base.read_json(V2_SNAPSHOT)),
            "proposal_records": base.EXPECTED_PROPOSALS,
            "measurement_occurrences": base.EXPECTED_MEASUREMENTS,
            "sampling": "exact frozen v2 complete-population snapshot; no rescan or exclusion",
        },
    )
    base.write_json(ATTEMPT_PATH, receipt, exclusive=True)
    print(json.dumps(receipt, indent=2, ensure_ascii=False))


def link_abort() -> None:
    successor = base.read_json(ATTEMPT_PATH)
    failure = base.read_json(V2_FAILURE)
    receipt = base.ainglish_client().abort_attempt(
        PRIOR_ATTEMPT,
        failed_gate="HTTP 422: manifest.models label exceeded the 80-character transport contract",
        preflight_receipt_hash=base.digest(failure),
        successor_attempt_id=base.attempt_id(successor),
    )
    base.write_json(ARTIFACT_DIR / "abort-v2.json", receipt)
    print(json.dumps(receipt, indent=2, ensure_ascii=False))


def submit() -> None:
    _, result = validate_inputs()
    spec = base.read_json(RUNSPEC_PATH)
    validate_manifest(spec)
    attempt = base.read_json(ATTEMPT_PATH)
    prior_abort = base.read_json(ARTIFACT_DIR / "abort-v2.json")
    prior_state = prior_abort.get("attempt", prior_abort)
    if prior_state.get("state") != "aborted" or prior_state.get("successor_attempt_id") != base.attempt_id(attempt):
        raise RuntimeError("v2 attempt is not linked to this successor")
    payload = {
        "metric": "unclaimed_verdict_flips",
        "formula_version": 1,
        "value": result["unclaimed_verdict_flips"],
        "panel_models": spec["models"],
        "panel_neff": 1,
        "manifest": spec,
        "attempt_id": base.attempt_id(attempt),
    }
    base.write_json(ARTIFACT_DIR / "measurement-request-v3.json", payload)
    receipt = base.ainglish_client().measure(base.SLUG, payload)
    base.write_json(ARTIFACT_DIR / "measurement-receipt-v3.json", receipt)
    print(json.dumps(receipt, indent=2, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("freeze", "mint", "link-abort", "submit"))
    args = parser.parse_args()
    if args.command == "freeze":
        freeze()
    elif args.command == "mint":
        mint()
    elif args.command == "link-abort":
        link_abort()
    else:
        submit()


if __name__ == "__main__":
    main()
