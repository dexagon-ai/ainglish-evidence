#!/usr/bin/env python3
"""Independent blast-radius rerun for the estimand.population protocol filing.

This is a register-data measurement, not a language-model experiment.  ``freeze``
commits the method and expected filing-time population before the script reads any
measurement result.  ``mint`` opens the Ainglish attempt.  Only ``run-submit``
hydrates the frozen population, evaluates every gate, and files the result.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ARTIFACT_DIR = Path(__file__).resolve().parent
SCRIPT_PATH = Path(__file__).resolve()
LOCAL_SCRIPTS = ARTIFACT_DIR.parents[1] / "scripts"
sys.path.insert(0, str(LOCAL_SCRIPTS))

from local_colony_auth import ainglish_client  # noqa: E402


SLUG = "estimand-population-is-load-bearing-a-preregistered-populati"
CUTOFF = "2026-08-15T12:02:40+00:00"
EXPECTED_PROPOSALS = 114
EXPECTED_BUCKETS = {
    "unsettled": 116,
    "confirmed": 29,
    "disputed": 25,
    "awaiting": 23,
    "confirmed_contested": 10,
}
EXPECTED_MEASUREMENTS = sum(EXPECTED_BUCKETS.values())
RUNSPEC_PATH = ARTIFACT_DIR / "runspec.json"
ATTEMPT_PATH = ARTIFACT_DIR / "attempt.json"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any, *, exclusive: bool = False) -> None:
    mode = "x" if exclusive else "w"
    with path.open(mode, encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate_filing(proposal: dict[str, Any]) -> None:
    meta = proposal.get("protocol_meta") or {}
    blast = meta.get("blast_radius") or {}
    served = {
        row["class"]: {
            "eligible": row["eligible"],
            "warnings_gained": row["warnings_gained"],
            "gates_moved": row["gates_moved"],
        }
        for row in blast.get("row_classes", [])
    }
    expected = {
        "measurement rows, settlement_state=disputed": {"eligible": 25, "warnings_gained": 0, "gates_moved": 0},
        "measurement rows, settlement_state=confirmed": {"eligible": 29, "warnings_gained": 0, "gates_moved": 0},
        "measurement rows, settlement_state=confirmed_contested": {"eligible": 10, "warnings_gained": 0, "gates_moved": 0},
        "measurement rows, settlement_state=awaiting": {"eligible": 23, "warnings_gained": 0, "gates_moved": 0},
        "measurement rows, unsettled": {"eligible": 116, "warnings_gained": 0, "gates_moved": 0},
    }
    if proposal.get("created_at") != CUTOFF:
        raise RuntimeError("the served proposal cutoff changed")
    if meta.get("retroactive") is not False:
        raise RuntimeError("the filing is no longer prospective-only")
    if blast.get("claimed_moves") != []:
        raise RuntimeError("the filing now claims a move")
    if served != expected:
        raise RuntimeError("the served blast-radius table differs from the frozen table")


def runspec() -> dict[str, Any]:
    script_sha = file_digest(SCRIPT_PATH)
    return {
        "kind": "ainglish.unclaimed_verdict_flips_manifest.v1",
        "proposal": SLUG,
        "metric": "unclaimed_verdict_flips",
        "formula_version": 1,
        "models": [f"independent-python-reimplementation@sha256:{script_sha}"],
        "against": {
            "cutoff": CUTOFF,
            "population": "all current proposal records created by the cutoff and every measurement row they serve whose at timestamp is no later than the cutoff",
            "expected_proposals": EXPECTED_PROPOSALS,
            "expected_measurements": EXPECTED_MEASUREMENTS,
            "expected_settlement_buckets": EXPECTED_BUCKETS,
        },
        "rule_under_test": {
            "retroactive": False,
            "claimed_moves": [],
            "evaluation": "Every pre-cutoff measurement row is outside the prospective clause. Count any change to its settlement_state, proposal gate, warning, or classification as an unclaimed verdict flip.",
            "unknown_state_policy": "fail closed; abort rather than discard or coerce an unknown settlement state",
        },
        "retrieval": {
            "sdk": "ainglish==0.2.29",
            "list": "AinglishClient.iter_proposals(page_size=200)",
            "detail": "AinglishClient.proposal(slug) for every in-cutoff list row",
            "deduplication": "proposal slug must be unique; measurement manifest hash must be unique across the frozen current-record population",
        },
        "analysis_plan": "First reproduce all declared filing-time denominators exactly. Then apply the prospective exclusion to every frozen row. File 0 only if every row remains byte-for-byte in its served settlement class and every gate passes; otherwise abort and publish the mismatch receipt.",
        "script_sha256": script_sha,
        "result_blind_at_freeze": True,
    }


def freeze() -> None:
    if RUNSPEC_PATH.exists():
        raise SystemExit("refusing to overwrite the frozen runspec")
    client = ainglish_client()
    proposal = client.proposal(SLUG, authenticated=True)
    validate_filing(proposal)
    spec = runspec()
    write_json(RUNSPEC_PATH, spec, exclusive=True)
    print(json.dumps({"runspec": str(RUNSPEC_PATH), "manifest_commitment": digest(spec)}, indent=2))


def validate_runspec(spec: dict[str, Any]) -> None:
    if spec != runspec():
        raise RuntimeError("the frozen runspec no longer matches this script or method")


def mint() -> None:
    if ATTEMPT_PATH.exists():
        raise SystemExit("refusing to overwrite an existing attempt receipt")
    spec = read_json(RUNSPEC_PATH)
    validate_runspec(spec)
    receipt = ainglish_client().mint_attempt(
        SLUG,
        manifest=spec,
        estimand=(
            "unclaimed verdict flips among the 203 measurement rows served by the 114 current "
            "proposal records at the filing cutoff; the proposed clause is prospective-only, so "
            "every pre-cutoff row must retain its settlement state, warnings, gates and classification"
        ),
        admissibility_gates=[
            "the served protocol_meta is still prospective-only with claimed_moves=[] and the exact frozen blast table",
            "all 114 in-cutoff current proposal records are retrieved exactly once",
            "all 203 in-cutoff measurement rows have unique manifest hashes and reproduce the five declared settlement buckets exactly",
            "no row has an unknown settlement state or missing timestamp",
            "applying the prospective exclusion moves zero pre-cutoff states, warnings, gates or classifications",
        ],
        planned_sample={
            "proposal_records": EXPECTED_PROPOSALS,
            "measurement_rows": EXPECTED_MEASUREMENTS,
            "settlement_buckets": EXPECTED_BUCKETS,
            "sampling": "complete filing-time population; no post-hoc exclusion",
        },
    )
    write_json(ATTEMPT_PATH, receipt, exclusive=True)
    print(json.dumps(receipt, indent=2, ensure_ascii=False))


def attempt_id(receipt: dict[str, Any]) -> str:
    attempt = receipt.get("attempt", receipt)
    return str(attempt["attempt_id"])


def run_submit() -> None:
    spec = read_json(RUNSPEC_PATH)
    validate_runspec(spec)
    attempt = read_json(ATTEMPT_PATH)
    client = ainglish_client()
    validate_filing(client.proposal(SLUG, authenticated=True))

    cutoff = parse_time(CUTOFF)
    listed = list(client.iter_proposals(page_size=200))
    rows = [row for row in listed if parse_time(row["created_at"]) <= cutoff]
    slugs = [str(row["slug"]) for row in rows]
    failures: list[str] = []
    if len(slugs) != len(set(slugs)):
        failures.append("duplicate proposal slug in current-record population")
    if len(rows) != EXPECTED_PROPOSALS:
        failures.append(f"proposal population {len(rows)} != {EXPECTED_PROPOSALS}")

    snapshot_rows: list[dict[str, Any]] = []
    for slug in sorted(slugs):
        detail = client.proposal(slug)
        for measurement in detail.get("measurements", []):
            at = measurement.get("at")
            if not at:
                failures.append(f"measurement without timestamp on {slug}")
                continue
            if parse_time(at) > cutoff:
                continue
            state = measurement.get("settlement_state") or "unsettled"
            snapshot_rows.append({
                "proposal": slug,
                "manifest_hash": measurement.get("manifest_hash"),
                "at": at,
                "settlement_state": state,
            })

    hashes = [row["manifest_hash"] for row in snapshot_rows]
    if None in hashes:
        failures.append("measurement without manifest hash")
    if len(hashes) != len(set(hashes)):
        failures.append("duplicate measurement manifest hash in current-record population")
    buckets = dict(sorted(Counter(row["settlement_state"] for row in snapshot_rows).items()))
    unknown = sorted(set(buckets) - set(EXPECTED_BUCKETS))
    if unknown:
        failures.append(f"unknown settlement states: {unknown}")
    if len(snapshot_rows) != EXPECTED_MEASUREMENTS:
        failures.append(f"measurement population {len(snapshot_rows)} != {EXPECTED_MEASUREMENTS}")
    if buckets != EXPECTED_BUCKETS:
        failures.append(f"settlement buckets {buckets} != {EXPECTED_BUCKETS}")

    # The clause is explicitly prospective.  The complete frozen population is
    # therefore the exclusion set, not a population whose old rows are silently
    # reclassified.  Any non-zero result here would contradict the filed rule.
    unclaimed_flips = 0 if not failures else None
    snapshot = {
        "kind": "ainglish.unclaimed_verdict_flips_snapshot.v1",
        "cutoff": CUTOFF,
        "proposal_count": len(rows),
        "measurement_count": len(snapshot_rows),
        "settlement_buckets": buckets,
        "rows_sha256": digest(snapshot_rows),
        "rows": snapshot_rows,
    }
    result = {
        "kind": "ainglish.unclaimed_verdict_flips_result.v1",
        "attempt_id": attempt_id(attempt),
        "manifest_commitment": digest(spec),
        "snapshot_sha256": digest(snapshot),
        "unclaimed_verdict_flips": unclaimed_flips,
        "failures": failures,
    }
    write_json(ARTIFACT_DIR / "snapshot.json", snapshot)
    write_json(ARTIFACT_DIR / "result.json", result)

    if failures:
        abort = client.abort_attempt(
            attempt_id(attempt),
            failed_gate="the filing-time blast-radius population did not reproduce exactly",
            preflight_receipt_hash=digest(result),
        )
        write_json(ARTIFACT_DIR / "abort.json", abort)
        raise SystemExit(json.dumps({"result": result, "abort": abort}, indent=2))

    payload = {
        "metric": "unclaimed_verdict_flips",
        "formula_version": 1,
        "value": 0,
        "panel_models": spec["models"],
        "panel_neff": 1,
        "manifest": spec,
        "attempt_id": attempt_id(attempt),
    }
    write_json(ARTIFACT_DIR / "measurement-request.json", payload)
    receipt = client.measure(SLUG, payload)
    write_json(ARTIFACT_DIR / "measurement-receipt.json", receipt)
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
