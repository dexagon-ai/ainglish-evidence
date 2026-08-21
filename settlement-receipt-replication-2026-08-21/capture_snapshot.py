#!/usr/bin/env python3
"""Capture a stable, minimal settlement-rule population without classifying it.

This is deliberately separate from analyze_snapshot.mjs.  It observes only the
public register fields committed by the measurement protocol, makes two full
passes, and refuses to publish a snapshot if those passes differ.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

from ainglish.client import AinglishClient


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def iso_utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def unwrap_proposal(value: dict) -> dict:
    proposal = value.get("proposal")
    return proposal if isinstance(proposal, dict) else value


def collect(client: AinglishClient) -> dict:
    listing = client.proposals()
    expected = int((listing.get("pagination") or {}).get("total", -1))
    slugs: list[str] = []
    for row in client.iter_proposals():
        candidate = row.get("proposal", row) if isinstance(row, dict) else row
        slugs.append(candidate["slug"])

    if expected < 0 or len(slugs) != expected or len(set(slugs)) != expected:
        raise RuntimeError(
            f"proposal envelope shortfall/duplication: expected={expected} "
            f"observed={len(slugs)} unique={len(set(slugs))}"
        )

    rows: list[dict] = []
    for ordinal, slug in enumerate(sorted(slugs), start=1):
        proposal = unwrap_proposal(client.proposal(slug))
        measurements: list[dict] = []
        for row_index, measurement in enumerate(proposal.get("measurements") or []):
            manifest = measurement.get("manifest") or {}
            accuracy_resolution = measurement.get("accuracy_resolution") or {}
            measurements.append(
                {
                    "row_index": row_index,
                    "manifest_hash": measurement.get("manifest_hash"),
                    "metric": measurement.get("metric"),
                    "formula_version": measurement.get("formula_version"),
                    "value": measurement.get("value"),
                    "value_lo": measurement.get("value_lo"),
                    "value_hi": measurement.get("value_hi"),
                    "replicates_hash": measurement.get("replicates_hash"),
                    "reproduced_ok": measurement.get("reproduced_ok"),
                    "settlement_eligible": measurement.get("settlement_eligible"),
                    "settlement_basis": measurement.get("settlement_basis"),
                    "input_disjointness": measurement.get("input_disjointness"),
                    "unit": (
                        accuracy_resolution.get("unit")
                        if isinstance(accuracy_resolution, dict)
                        else None
                    ),
                    "interval_kind_declared": (
                        manifest.get("interval_kind")
                        if isinstance(manifest, dict)
                        else None
                    ),
                    "estimand_digest": (
                        manifest.get("estimand_digest")
                        if isinstance(manifest, dict)
                        else None
                    ),
                    "by": (measurement.get("submitter") or {}).get("name"),
                }
            )
        rows.append(
            {
                "slug": slug,
                "publication_status": proposal.get("publication_status"),
                "measurements": measurements,
            }
        )
        if ordinal % 25 == 0:
            print(f"captured {ordinal}/{expected}", file=sys.stderr, flush=True)

    return {
        "proposal_records": len(rows),
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    client = AinglishClient()
    started_at = iso_utc()
    first = collect(client)
    between_passes_at = iso_utc()
    second = collect(client)
    completed_at = iso_utc()

    first_bytes = canonical_bytes(first)
    second_bytes = canonical_bytes(second)
    if first_bytes != second_bytes:
        raise SystemExit(
            "snapshot passes diverged; the register changed during capture, so no "
            "population artifact was written"
        )

    stable_digest = hashlib.sha256(first_bytes).hexdigest()
    snapshot = {
        "kind": "dexagon.settlement_rule_snapshot.v1",
        "source": "public Ainglish proposal details; two complete matching passes",
        "capture_window": {
            "started_at": started_at,
            "between_passes_at": between_passes_at,
            "completed_at": completed_at,
        },
        "envelope_reconciled": True,
        "stable_payload_sha256": stable_digest,
        **first,
    }
    payload = canonical_bytes(snapshot)
    args.output.write_bytes(payload)
    print(
        json.dumps(
            {
                "snapshot_sha256": hashlib.sha256(payload).hexdigest(),
                "stable_payload_sha256": stable_digest,
                "proposal_records": snapshot["proposal_records"],
                "measurement_rows": sum(
                    len(row["measurements"]) for row in snapshot["rows"]
                ),
                "capture_window": snapshot["capture_window"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
