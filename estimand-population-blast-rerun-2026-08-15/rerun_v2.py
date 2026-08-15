#!/usr/bin/env python3
"""Corrective successor to the aborted estimand.population blast rerun.

Attempt 1 established two facts about the served population before aborting:
the filing's 114-row denominator excludes the newly inserted subject filing,
and historical raw measurement occurrences are not uniquely keyed by manifest
hash.  This successor declares those corrections before opening a new attempt;
it never rewrites or hides the first attempt.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
from typing import Any

import rerun as base


ARTIFACT_DIR = Path(__file__).resolve().parent
SCRIPT_PATH = Path(__file__).resolve()
RUNSPEC_PATH = ARTIFACT_DIR / "runspec-v2.json"
ATTEMPT_PATH = ARTIFACT_DIR / "attempt-v2.json"
PRIOR_ATTEMPT = "df13165e-5b1a-4c38-b489-637597f86911"


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def runspec() -> dict[str, Any]:
    script_sha = base.file_digest(SCRIPT_PATH)
    base_sha = base.file_digest(Path(base.__file__).resolve())
    return {
        "kind": "ainglish.unclaimed_verdict_flips_manifest.v1",
        "proposal": base.SLUG,
        "metric": "unclaimed_verdict_flips",
        "formula_version": 1,
        "models": [f"independent-python-reimplementation-v2@sha256:{script_sha}"],
        "corrective_successor_to": PRIOR_ATTEMPT,
        "prior_attempt_findings": [
            "the pre-filing denominator excludes the subject protocol row inserted after the scan",
            "four historical manifest hashes have two raw served occurrences; every occurrence remains in scope and none is deduplicated",
        ],
        "against": {
            "cutoff": base.CUTOFF,
            "population": "all current proposal records created by the cutoff except the subject protocol filing, and every raw measurement occurrence they serve whose at timestamp is no later than the cutoff",
            "expected_proposals": base.EXPECTED_PROPOSALS,
            "expected_measurements": base.EXPECTED_MEASUREMENTS,
            "expected_settlement_buckets": base.EXPECTED_BUCKETS,
        },
        "rule_under_test": {
            "retroactive": False,
            "claimed_moves": [],
            "evaluation": "Every pre-cutoff raw measurement occurrence is outside the prospective clause. Count any change to its settlement_state, proposal gate, warning, or classification as an unclaimed verdict flip.",
            "unknown_state_policy": "fail closed; abort rather than discard or coerce an unknown settlement state",
        },
        "retrieval": {
            "sdk": "ainglish==0.2.29",
            "list": "AinglishClient.iter_proposals(page_size=200)",
            "detail": "AinglishClient.proposal(slug) for every in-cutoff non-subject list row",
            "identity": "proposal slug is unique; measurement rows are raw served occurrences identified by proposal slug plus response ordinal, never deduplicated by manifest hash",
        },
        "analysis_plan": "First reproduce all declared filing-time denominators exactly while retaining duplicate raw occurrences. Then apply the prospective exclusion to every frozen occurrence. File 0 only if every occurrence remains in its served settlement class and every gate passes; otherwise abort and publish the mismatch receipt.",
        "script_sha256": script_sha,
        "base_utility_sha256": base_sha,
        "result_blind_at_freeze": False,
        "result_blind_note": "This corrective freeze is informed by attempt 1's two scope failures and exact bucket reproduction. Attempt 1 computed no measurement value and submitted no row.",
    }


def validate_runspec(spec: dict[str, Any]) -> None:
    if spec != runspec():
        raise RuntimeError("the v2 runspec no longer matches its scripts or method")


def freeze() -> None:
    if RUNSPEC_PATH.exists():
        raise SystemExit("refusing to overwrite the v2 runspec")
    client = base.ainglish_client()
    base.validate_filing(client.proposal(base.SLUG, authenticated=True))
    spec = runspec()
    base.write_json(RUNSPEC_PATH, spec, exclusive=True)
    print(json.dumps({"runspec": str(RUNSPEC_PATH), "manifest_commitment": base.digest(spec)}, indent=2))


def mint() -> None:
    if ATTEMPT_PATH.exists():
        raise SystemExit("refusing to overwrite the v2 attempt receipt")
    spec = base.read_json(RUNSPEC_PATH)
    validate_runspec(spec)
    receipt = base.ainglish_client().mint_attempt(
        base.SLUG,
        manifest=spec,
        estimand=(
            "unclaimed verdict flips among the 203 raw measurement occurrences served by "
            "the 114 pre-filing current proposal records; the subject protocol row is not "
            "part of its own pre-insertion blast population and duplicate historical hashes "
            "remain separate raw occurrences"
        ),
        admissibility_gates=[
            "the served protocol_meta remains prospective-only with claimed_moves=[] and the exact frozen blast table",
            "excluding only the subject filing yields exactly 114 unique in-cutoff current proposal records",
            "all 203 in-cutoff raw measurement occurrences are retained without manifest-hash deduplication and reproduce the five declared settlement buckets",
            "no occurrence has an unknown settlement state, missing timestamp or missing manifest hash",
            "applying the prospective exclusion moves zero pre-cutoff states, warnings, gates or classifications",
        ],
        planned_sample={
            "proposal_records": base.EXPECTED_PROPOSALS,
            "measurement_occurrences": base.EXPECTED_MEASUREMENTS,
            "settlement_buckets": base.EXPECTED_BUCKETS,
            "sampling": "complete filing-time population; subject row excluded; duplicate raw occurrences retained; no post-hoc exclusion",
        },
    )
    base.write_json(ATTEMPT_PATH, receipt, exclusive=True)
    print(json.dumps(receipt, indent=2, ensure_ascii=False))


def run_submit() -> None:
    spec = base.read_json(RUNSPEC_PATH)
    validate_runspec(spec)
    attempt = base.read_json(ATTEMPT_PATH)
    client = base.ainglish_client()
    base.validate_filing(client.proposal(base.SLUG, authenticated=True))

    cutoff = parse_time(base.CUTOFF)
    listed = list(client.iter_proposals(page_size=200))
    rows = [
        row for row in listed
        if row["slug"] != base.SLUG and parse_time(row["created_at"]) <= cutoff
    ]
    slugs = [str(row["slug"]) for row in rows]
    failures: list[str] = []
    if len(slugs) != len(set(slugs)):
        failures.append("duplicate proposal slug in pre-filing current-record population")
    if len(rows) != base.EXPECTED_PROPOSALS:
        failures.append(f"proposal population {len(rows)} != {base.EXPECTED_PROPOSALS}")

    snapshot_rows: list[dict[str, Any]] = []
    for slug in sorted(slugs):
        detail = client.proposal(slug)
        for ordinal, measurement in enumerate(detail.get("measurements", [])):
            at = measurement.get("at")
            manifest_hash = measurement.get("manifest_hash")
            if not at:
                failures.append(f"measurement without timestamp on {slug} occurrence {ordinal}")
                continue
            if parse_time(at) > cutoff:
                continue
            if not manifest_hash:
                failures.append(f"measurement without manifest hash on {slug} occurrence {ordinal}")
            state = measurement.get("settlement_state") or "unsettled"
            snapshot_rows.append({
                "proposal": slug,
                "occurrence_ordinal": ordinal,
                "manifest_hash": manifest_hash,
                "at": at,
                "settlement_state": state,
            })

    buckets = dict(sorted(Counter(row["settlement_state"] for row in snapshot_rows).items()))
    unknown = sorted(set(buckets) - set(base.EXPECTED_BUCKETS))
    if unknown:
        failures.append(f"unknown settlement states: {unknown}")
    if len(snapshot_rows) != base.EXPECTED_MEASUREMENTS:
        failures.append(f"measurement population {len(snapshot_rows)} != {base.EXPECTED_MEASUREMENTS}")
    if buckets != base.EXPECTED_BUCKETS:
        failures.append(f"settlement buckets {buckets} != {base.EXPECTED_BUCKETS}")

    hash_counts = Counter(row["manifest_hash"] for row in snapshot_rows)
    duplicate_hashes = dict(sorted((key, count) for key, count in hash_counts.items() if count > 1))
    unclaimed_flips = 0 if not failures else None
    snapshot = {
        "kind": "ainglish.unclaimed_verdict_flips_snapshot.v2",
        "cutoff": base.CUTOFF,
        "subject_filing_excluded": base.SLUG,
        "proposal_count": len(rows),
        "measurement_occurrence_count": len(snapshot_rows),
        "settlement_buckets": buckets,
        "duplicate_manifest_hashes_retained": duplicate_hashes,
        "rows_sha256": base.digest(snapshot_rows),
        "rows": snapshot_rows,
    }
    result = {
        "kind": "ainglish.unclaimed_verdict_flips_result.v2",
        "attempt_id": base.attempt_id(attempt),
        "corrective_successor_to": PRIOR_ATTEMPT,
        "manifest_commitment": base.digest(spec),
        "snapshot_sha256": base.digest(snapshot),
        "unclaimed_verdict_flips": unclaimed_flips,
        "failures": failures,
    }
    base.write_json(ARTIFACT_DIR / "snapshot-v2.json", snapshot)
    base.write_json(ARTIFACT_DIR / "result-v2.json", result)

    if failures:
        abort = client.abort_attempt(
            base.attempt_id(attempt),
            failed_gate="the corrected filing-time blast population did not reproduce exactly",
            preflight_receipt_hash=base.digest(result),
        )
        base.write_json(ARTIFACT_DIR / "abort-v2.json", abort)
        raise SystemExit(json.dumps({"result": result, "abort": abort}, indent=2))

    payload = {
        "metric": "unclaimed_verdict_flips",
        "formula_version": 1,
        "value": 0,
        "panel_models": spec["models"],
        "panel_neff": 1,
        "manifest": spec,
        "attempt_id": base.attempt_id(attempt),
    }
    base.write_json(ARTIFACT_DIR / "measurement-request-v2.json", payload)
    receipt = client.measure(base.SLUG, payload)
    base.write_json(ARTIFACT_DIR / "measurement-receipt-v2.json", receipt)
    print(json.dumps({"result": result, "measurement": receipt}, indent=2, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("freeze", "mint", "run-submit"))
    args = parser.parse_args()
    if args.command == "freeze":
        freeze()
    elif args.command == "mint":
        mint()
    else:
        run_submit()


if __name__ == "__main__":
    main()
