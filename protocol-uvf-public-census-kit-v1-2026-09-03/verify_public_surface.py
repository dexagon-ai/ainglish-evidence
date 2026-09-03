#!/usr/bin/env python3
"""Audit the public inputs and current verdict surface of the UVF batch.

This is deliberately a public-surface audit, not an independent replication of
the private focused source tests used by the original measurements.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urljoin
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
DEFAULT_BASE = "https://ainglish.org"
USER_AGENT = "ainglish-public-uvf-census-kit/1"


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def fetch(base: str, path_or_url: str) -> dict[str, Any]:
    url = path_or_url if path_or_url.startswith(("http://", "https://")) else urljoin(base + "/", path_or_url.lstrip("/"))
    request = Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=30) as response:
            if response.status != 200:
                raise RuntimeError(f"GET {url} returned HTTP {response.status}")
            data = json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"GET {url} failed: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError(f"GET {url} returned a non-object JSON root")
    return data


def proposal_rows(base: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cursor: str | None = None
    expected_total: int | None = None
    while True:
        params: dict[str, Any] = {"limit": 200}
        if cursor:
            params["cursor"] = cursor
        page = fetch(base, "/api/v1/proposals?" + urlencode(params))
        page_rows = page.get("proposals")
        pagination = page.get("pagination")
        if not isinstance(page_rows, list) or not isinstance(pagination, dict):
            raise RuntimeError("proposal page lacks proposals or pagination")
        total = pagination.get("total")
        if not isinstance(total, int):
            raise RuntimeError("proposal pagination total is not an integer")
        if expected_total is None:
            expected_total = total
        elif total != expected_total:
            raise RuntimeError("proposal total changed during one traversal")
        rows.extend(page_rows)
        if not pagination.get("has_more"):
            break
        cursor = pagination.get("next_cursor")
        if not isinstance(cursor, str) or not cursor:
            raise RuntimeError("proposal page says has_more without next_cursor")
    if len(rows) != expected_total:
        raise RuntimeError(f"proposal traversal returned {len(rows)} of {expected_total} rows")
    return rows


def measurement_rows(base: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    path = "/api/v1/measurements?limit=200"
    first_sweep: dict[str, Any] | None = None
    expected_total: int | None = None
    while path:
        page = fetch(base, path)
        page_rows = page.get("measurements")
        sweep = page.get("sweep")
        if not isinstance(page_rows, list) or not isinstance(sweep, dict):
            raise RuntimeError("measurement page lacks measurements or sweep metadata")
        total = page.get("total")
        if not isinstance(total, int):
            raise RuntimeError("measurement total is not an integer")
        if first_sweep is None:
            first_sweep = sweep
            expected_total = total
        elif sweep.get("snapshot_max_id") != first_sweep.get("snapshot_max_id") or total != expected_total:
            raise RuntimeError("measurement snapshot changed inside its cursor chain")
        rows.extend(page_rows)
        next_path = page.get("next")
        path = next_path if page.get("has_more") else ""
        if path and not isinstance(path, str):
            raise RuntimeError("measurement page says has_more without a next URL")
    if len(rows) != expected_total:
        raise RuntimeError(f"measurement traversal returned {len(rows)} of {expected_total} rows")
    return rows, first_sweep or {}


def projection(base: str) -> dict[str, Any]:
    proposals = proposal_rows(base)
    measurements, sweep = measurement_rows(base)
    proposal_surface = [
        {key: row.get(key) for key in (
            "slug", "stage", "advance_blocked", "verdict_class", "verdict",
            "register_screen", "deterministic",
        )}
        for row in proposals
    ]
    measurement_surface = [
        {key: row.get(key) for key in (
            "manifest_hash", "attempt_id", "metric", "evidence_state", "settlement_state",
            "settlement_eligible", "reproduced_ok", "confirmation_count", "disagreement_count",
            "voided_at", "retraction",
        )}
        for row in measurements
    ]
    return {
        "proposal_count": len(proposals),
        "proposal_sha256": digest(proposal_surface),
        "measurement_count": len(measurements),
        "measurement_snapshot_max_id": sweep.get("snapshot_max_id"),
        "measurement_filter_sha256": sweep.get("filter_sha256"),
        "measurement_sha256": digest(measurement_surface),
    }


def verify_campaign(base: str, campaign: dict[str, Any]) -> dict[str, Any]:
    slug = campaign["proposal_slug"]
    target_hash = campaign["original_manifest_hash"]
    proposal = fetch(base, "/api/v1/proposals/" + quote(slug, safe=""))
    target = fetch(base, "/api/v1/measurements/" + quote(target_hash, safe=""))
    manifest = target.get("manifest")
    errors = []
    if proposal.get("slug") != slug:
        errors.append("proposal slug mismatch")
    if target.get("manifest_hash") != target_hash:
        errors.append("measurement manifest hash mismatch")
    if target.get("metric") != "unclaimed_verdict_flips":
        errors.append("measurement metric is not unclaimed_verdict_flips")
    if target.get("is_replication") is not False:
        errors.append("target is not an original")
    if target.get("evidence_state") != "valid" or target.get("voided_at") is not None or target.get("retraction") is not None:
        errors.append("target is not active valid evidence")
    if not isinstance(manifest, dict) or manifest.get("metric") != "unclaimed_verdict_flips":
        errors.append("stored manifest is missing or has the wrong metric")
    against = manifest.get("against") if isinstance(manifest, dict) else None
    return {
        "key": campaign["key"],
        "proposal_slug": slug,
        "proposal_stage": proposal.get("stage"),
        "original_manifest_hash": target_hash,
        "original_value": target.get("value"),
        "evidence_state": target.get("evidence_state"),
        "settlement_state": target.get("settlement_state"),
        "implementation_commit": against.get("implementation_commit") if isinstance(against, dict) else None,
        "deployed_commit_at_original": against.get("deployed_commit") if isinstance(against, dict) else None,
        "stored_manifest_sha256": digest(manifest) if isinstance(manifest, dict) else None,
        "passed": not errors,
        "errors": errors,
    }


def selftest() -> None:
    assert digest({"b": 2, "a": 1}) == "43258cff783fe7036d8a43033f830adfc60ec037382473548ac742b888292777"
    assert canonical({"z": "Ainglish", "a": [1, True, None]}) == b'{"a":[1,true,null],"z":"Ainglish"}'
    fixture = json.loads((ROOT / "campaigns.json").read_text(encoding="utf-8"))
    assert fixture["kind"] == "ainglish.protocol-uvf-public-census-kit.v1"
    assert len(fixture["campaigns"]) == 7
    assert len({row["key"] for row in fixture["campaigns"]}) == 7
    assert all(len(row["original_manifest_hash"]) == 64 for row in fixture["campaigns"])
    print("selftest: ok")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=DEFAULT_BASE)
    parser.add_argument("--out", type=Path, default=Path("public-surface-receipt.json"))
    parser.add_argument("--pause", type=float, default=0.5, help="Seconds between the two complete traversals")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return 0

    fixture_bytes = (ROOT / "campaigns.json").read_bytes()
    fixture = json.loads(fixture_bytes)
    health = fetch(args.base, "/api/v1/health")
    protocols = fetch(args.base, "/api/v1/protocols")
    campaigns = [verify_campaign(args.base, row) for row in fixture["campaigns"]]
    first = projection(args.base)
    time.sleep(max(0.0, args.pause))
    second = projection(args.base)
    stable_keys = (
        "proposal_count", "proposal_sha256", "measurement_count",
        "measurement_snapshot_max_id", "measurement_sha256",
    )
    stable = all(first[key] == second[key] for key in stable_keys)
    metric = (protocols.get("metrics") or {}).get("unclaimed_verdict_flips")
    receipt = {
        "kind": "ainglish.protocol-uvf-public-surface-receipt.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "base": args.base,
        "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
        "deployment": health.get("deployment"),
        "metric_contract": metric,
        "campaigns": campaigns,
        "projections": {"first": first, "second": second, "stable": stable},
        "result": {
            "public_inputs_valid": all(row["passed"] for row in campaigns),
            "current_verdict_surface_stable": stable,
            "settlement_eligible_replication": False,
            "reason": (
                "The public audit does not execute the private repository's focused source tests, "
                "so it does not reproduce the original causal/source admissibility gate."
            ),
        },
    }
    args.out.write_bytes(json.dumps(receipt, indent=2, ensure_ascii=False).encode("utf-8") + b"\n")
    print(json.dumps(receipt["result"], indent=2))
    return 0 if receipt["result"]["public_inputs_valid"] and stable else 1


if __name__ == "__main__":
    raise SystemExit(main())
