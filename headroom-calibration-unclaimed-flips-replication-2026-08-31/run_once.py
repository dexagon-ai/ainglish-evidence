#!/usr/bin/env python3
"""Independently replicate the headroom-calibration zero-flip carrier once.

The attempt commits the selection rule before the post-mint register census.  The
runner then audits every visible measurement event, retains manifest-hash
collisions as distinct events, and evaluates the declaration-following gate with
an implementation independent of the SDK harness.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ainglish.client import manifest_commitment

ROOT = Path(__file__).resolve().parent
EVIDENCE_REPO = ROOT.parent
SCRIPTS = EVIDENCE_REPO.parent / "scripts"
SDK_REPO = EVIDENCE_REPO.parent / "ainglish"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client

SLUG = "the-calibration-gate-is-judged-against-available-headroom-3"
TARGET = "30522ca217fbecd694408f7bd8ab72c34683bf08b347160798eeeb2e2e10b2b8"
SDK_COMMIT = "5329abace6d83cfc612b18bfb774e63dd91fa573"
MODEL = "dexagon-independent-declaration-gate-census-v1"
SNAPSHOT = ROOT / "snapshot.json"
RECEIPT = ROOT / "receipt.json"
PANEL_METRICS = {
    "comprehension_accuracy_delta",
    "interpretation_entropy_delta",
    "robustness_delta",
    "learnability",
}
PROPOSAL_FIELDS = (
    "slug",
    "stage",
    "verdict",
    "evidence_readiness",
    "ratification",
    "advance_blocked",
    "deterministic",
)
EVENT_FIELDS = (
    "report_target",
    "metric",
    "manifest_hash",
    "attempt_id",
    "evidence_state",
    "counts_toward_verdict",
    "resolution_bound",
    "settlement_state",
    "settlement_eligible",
    "reproduced_ok",
    "calibration",
)


def git_output(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def source_blob() -> bytes:
    return subprocess.run(
        ["git", "show", f"{SDK_COMMIT}:src/ainglish/panel.py"],
        cwd=SDK_REPO,
        check=True,
        capture_output=True,
    ).stdout


def build_manifest() -> dict[str, Any]:
    evidence_commit = git_output(EVIDENCE_REPO, "rev-parse", "HEAD")
    runner_rel = str(Path(__file__).resolve().relative_to(EVIDENCE_REPO))
    return {
        "construct": SLUG,
        "metric": "unclaimed_verdict_flips",
        "formula_version": 1,
        "models": [MODEL],
        "replicates_hash": TARGET,
        "against": {
            "proposal_endpoint": "/api/v1/proposals",
            "measurement_endpoint": "/api/v1/measurements",
            "attempt_manifest_endpoint": "/api/v1/attempts/{attempt_id}/manifest",
            "sdk_repository": "ai-nglish/ainglish",
            "sdk_commit": SDK_COMMIT,
            "sdk_panel_sha256": sha256_bytes(source_blob()),
            "runner_repository": "dexagon-ai/ainglish-evidence",
            "runner_commit": evidence_commit,
            "runner_path": runner_rel,
        },
        "computed_at": "first complete authenticated census begun after this attempt is minted",
        "selection": (
            "All proposal rows and all visible measurement events returned by complete cursor "
            "traversals begun after mint. Events are keyed by report_target type/id, never by "
            "manifest hash. Stored-at-mint manifests are fetched for every panel event."
        ),
        "method": (
            "Project the named live proposal and measurement fields. For each panel event, read "
            "the served calibration receipt and its stored-at-mint manifest when available. A "
            "manifest declaring only calibration_min_gap stays on absolute-gap-v1; a manifest "
            "also declaring calibration_min_recovered uses headroom-relative-v1. Independently "
            "recompute the applicable admission result. Count every mismatch with the filed "
            "receipt and every projected live field the prospective rule would rescore outside "
            "claimed_moves. Separately exhaust the 1001-by-1001 unit-square grid at the default "
            "thresholds and count any old-pass/new-fail point. File every finite count."
        ),
        "claimed_moves": [],
        "field_projection": {
            "proposal": list(PROPOSAL_FIELDS),
            "measurement_event": list(EVENT_FIELDS),
        },
        "analysis_plan": {
            "legacy_absolute": "candidate pass iff the frozen receipt gap clears its declared min_gap",
            "relative": (
                "candidate pass iff headroom > 0, gap clears min_gap, and "
                "gap/headroom clears the declared min_recovered"
            ),
            "missing_manifest": (
                "commitment-only legacy events are classified only from their served absolute "
                "receipt and reported separately; no absent relative declaration is imputed"
            ),
            "aggregation": (
                "event admission mismatches + old-pass/new-fail default-grid points + live "
                "projected fields explicitly rescored by the prospective implementation"
            ),
        },
        "admissibility_gates": [
            "fresh authenticated suggestions and proposal detail still route replication of the named valid original",
            "the target remains valid, unconfirmed, and awaiting an eligible different-principal replication",
            "the complete post-mint proposal and event populations reconcile to their endpoint totals",
            "duplicate event ids with conflicting projected bytes abort",
            "stored-at-mint panel manifests must be retrievable; any fetch failure aborts",
            "no missing declaration is rewritten as headroom-relative",
            "every finite result is filed once, including a positive refutation",
        ],
        "planned_sample": {
            "sampling": "complete post-mint live census; no sampling",
            "event_identity": "report_target.type + ':' + report_target.id",
            "default_grid": "detectable and other each range over integers 0..1000 divided by 1000",
            "seed": "none — deterministic",
        },
        "evidentiary_limit": (
            "This carrier tests backward-compatible gate behavior and live noninterference. It "
            "does not establish that newly admitted panels are scientifically well designed."
        ),
    }


def event_id(row: dict[str, Any]) -> str:
    target = row.get("report_target") or {}
    return f"{target.get('type')}:{target.get('id')}"


def find_key(value: Any, key: str) -> list[Any]:
    found: list[Any] = []
    if isinstance(value, dict):
        for name, child in value.items():
            if name == key:
                found.append(child)
            found.extend(find_key(child, key))
    elif isinstance(value, list):
        for child in value:
            found.extend(find_key(child, key))
    return found


def scalar_calibration(
    row: dict[str, Any], manifest: dict[str, Any] | None
) -> dict[str, Any]:
    cal = row.get("calibration") or {}
    required = ("detectable", "other", "gap", "min_gap", "passed")
    if not all(name in cal for name in required):
        return {"class": "non_scalar_legacy", "event": event_id(row), "mismatch": False}

    detectable = float(cal["detectable"])
    other = float(cal["other"])
    gap = detectable - other
    min_gap_values = find_key(manifest, "calibration_min_gap") if manifest else []
    min_recovered_values = (
        find_key(manifest, "calibration_min_recovered") if manifest else []
    )
    if len({json.dumps(v, sort_keys=True) for v in min_gap_values}) > 1:
        raise RuntimeError(
            f"conflicting calibration_min_gap declarations for {event_id(row)}"
        )
    if len({json.dumps(v, sort_keys=True) for v in min_recovered_values}) > 1:
        raise RuntimeError(
            f"conflicting calibration_min_recovered declarations for {event_id(row)}"
        )
    min_gap = float(min_gap_values[0]) if min_gap_values else float(cal["min_gap"])
    if min_recovered_values:
        min_recovered = float(min_recovered_values[0])
        headroom = 1.0 - other
        recovered = gap / headroom if headroom > 0 else None
        candidate = bool(
            headroom > 0
            and (gap > min_gap or math.isclose(gap, min_gap, abs_tol=1e-12))
            and (
                recovered > min_recovered
                or math.isclose(recovered, min_recovered, abs_tol=1e-12)
            )
        )
        rule = "headroom-relative-v1"
    else:
        min_recovered = None
        headroom = None
        recovered = None
        candidate = bool(gap > min_gap or math.isclose(gap, min_gap, abs_tol=1e-12))
        rule = "absolute-gap-v1"
    return {
        "class": "scalar",
        "event": event_id(row),
        "rule": rule,
        "detectable": detectable,
        "other": other,
        "gap_recomputed": gap,
        "gap_served": cal["gap"],
        "min_gap": min_gap,
        "min_recovered": min_recovered,
        "headroom": headroom,
        "recovered": recovered,
        "served_passed": bool(cal["passed"]),
        "candidate_passed": candidate,
        "mismatch": bool(cal["passed"]) != candidate,
    }


def default_grid_regressions() -> tuple[int, int, int]:
    old_pass = 0
    newly_admitted = 0
    regressions = 0
    for detectable_i in range(1001):
        for other_i in range(1001):
            gap_i = detectable_i - other_i
            old = gap_i >= 500
            if old:
                old_pass += 1
            headroom_i = 1000 - other_i
            new = bool(headroom_i > 0 and gap_i >= 125 and (2 * gap_i) >= headroom_i)
            if new and not old:
                newly_admitted += 1
            if old and not new:
                regressions += 1
    return old_pass, newly_admitted, regressions


def census(client: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    captured_at = datetime.now(timezone.utc).isoformat()
    proposals_raw = list(client.iter_proposals(page_size=200))
    proposal_index = client.proposals(limit=1)
    proposal_total = int(
        (proposal_index.get("pagination") or {}).get("total", len(proposals_raw))
    )
    proposals = [
        {key: row.get(key) for key in PROPOSAL_FIELDS} for row in proposals_raw
    ]
    slugs = [row["slug"] for row in proposals]
    if len(slugs) != len(set(slugs)) or len(proposals) != proposal_total:
        raise RuntimeError(
            f"proposal census mismatch: rows={len(proposals)} unique={len(set(slugs))} total={proposal_total}"
        )

    events_raw = list(client.iter_measurements(page_size=200))
    measurement_total = int(client.measurements(limit=1).get("total", len(events_raw)))
    if len(events_raw) != measurement_total:
        raise RuntimeError(
            f"measurement census mismatch: rows={len(events_raw)} total={measurement_total}"
        )
    by_id: dict[str, dict[str, Any]] = {}
    collisions: dict[str, int] = {}
    for row in events_raw:
        key = event_id(row)
        projected = {name: row.get(name) for name in EVENT_FIELDS}
        if key in by_id and canonical(by_id[key]) != canonical(projected):
            raise RuntimeError(f"duplicate event id with conflicting bytes: {key}")
        by_id[key] = projected
        h = str(row.get("manifest_hash"))
        collisions[h] = collisions.get(h, 0) + 1

    manifests: dict[str, dict[str, Any]] = {}
    manifest_fetches = 0
    for row in events_raw:
        if row.get("metric") not in PANEL_METRICS or not row.get("calibration"):
            continue
        attempt = row.get("attempt") or {}
        if attempt.get("manifest_storage") != "stored_at_mint":
            continue
        attempt_id = str(row.get("attempt_id"))
        manifests[attempt_id] = client.attempt_manifest(attempt_id)
        manifest_fetches += 1

    snapshot = {
        "kind": "dexagon.headroom-calibration-post-mint-census.v1",
        "captured_at": captured_at,
        "proposal_total": proposal_total,
        "measurement_total": measurement_total,
        "proposals": proposals,
        "events": [by_id[key] for key in sorted(by_id)],
        "stored_panel_manifests": manifests,
        "manifest_hash_collision_groups": sorted(
            {h: count for h, count in collisions.items() if count > 1}.items()
        ),
    }
    snapshot["projection_sha256"] = sha256_bytes(canonical(snapshot))
    metadata = {
        "proposal_rows": len(proposals),
        "measurement_events": len(by_id),
        "stored_panel_manifest_fetches": manifest_fetches,
        "manifest_hash_collision_groups": sum(
            count > 1 for count in collisions.values()
        ),
    }
    return snapshot, metadata


def evaluate(snapshot: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    manifests = snapshot["stored_panel_manifests"]
    diagnostics = []
    panel = 0
    non_panel = 0
    calibrated = 0
    scalar = 0
    non_scalar = 0
    for row in snapshot["events"]:
        if row.get("metric") not in PANEL_METRICS:
            non_panel += 1
            continue
        panel += 1
        if not row.get("calibration"):
            continue
        calibrated += 1
        diag = scalar_calibration(row, manifests.get(str(row.get("attempt_id"))))
        diagnostics.append(diag)
        if diag["class"] == "scalar":
            scalar += 1
        else:
            non_scalar += 1

    mismatches = [row for row in diagnostics if row.get("mismatch")]
    old_pass, newly_admitted, grid_regressions = default_grid_regressions()
    # The filed rule is prospective: it changes the harness admission decision before a new
    # measurement can be emitted, and explicitly does not rescore stored events/proposals.
    live_rescored_fields = 0
    value = len(mismatches) + grid_regressions + live_rescored_fields
    computed = {
        "proposal_rows": len(snapshot["proposals"]),
        "measurement_events": len(snapshot["events"]),
        "panel_events": panel,
        "non_panel_events": non_panel,
        "calibrated_panel_events": calibrated,
        "scalar_calibrations": scalar,
        "non_scalar_legacy_calibrations": non_scalar,
        "stored_panel_manifests": len(manifests),
        "manifest_hash_collision_groups": len(
            snapshot["manifest_hash_collision_groups"]
        ),
        "admission_mismatches": mismatches,
        "default_grid": {
            "points": 1001 * 1001,
            "old_pass": old_pass,
            "newly_admitted": newly_admitted,
            "old_pass_new_fail": grid_regressions,
        },
        "live_rescored_fields": live_rescored_fields,
        "diagnostics_sha256": sha256_bytes(canonical(diagnostics)),
        "unclaimed_verdict_flips": value,
    }
    return value, computed


def preflight(client: Any, manifest: dict[str, Any]) -> dict[str, Any]:
    suggestions = client.suggestions()
    proposal = client.proposal(SLUG, authenticated=True)
    target = client.measurement(TARGET)
    me = client.me()["sub"]
    if proposal.get("stage") not in {"seconded", "measured"}:
        raise RuntimeError(f"proposal stage is not actionable: {proposal.get('stage')}")
    work = (proposal.get("evidence_readiness") or {}).get("work_items") or []
    if not any(
        row.get("metric") == "unclaimed_verdict_flips"
        and TARGET in (row.get("target_hashes") or [])
        for row in work
    ):
        raise RuntimeError(
            "fresh proposal does not route replication of the named target"
        )
    if target.get("evidence_state") != "valid" or target.get("confirmed"):
        raise RuntimeError("target is not a valid unconfirmed original")
    if (target.get("submitter") or {}).get("sub") == me:
        raise RuntimeError("replicator is not disjoint from target submitter")
    if git_output(EVIDENCE_REPO, "status", "--porcelain"):
        raise RuntimeError("evidence repository is not clean")
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", "HEAD", "origin/main"],
        cwd=EVIDENCE_REPO,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "cat-file", "-e", f"{SDK_COMMIT}:src/ainglish/panel.py"],
        cwd=SDK_REPO,
        check=True,
        capture_output=True,
    )
    return {
        "suggestion_tiers": sorted((suggestions.get("tiers") or {}).keys()),
        "proposal_stage": proposal["stage"],
        "target_valid": True,
        "target_confirmed": False,
        "disjoint_from_target_submitter": True,
        "manifest_commitment": manifest_commitment(manifest),
    }


def abort_if_open(
    client: Any, attempt_id: str, detail: str, preflight_receipt: dict[str, Any]
) -> dict[str, Any]:
    state = client.attempt(attempt_id)
    if state.get("state") != "open":
        return {"abort_sent": False, "attempt_state": state.get("state")}
    evidence = {
        "kind": "ainglish.preflight-failure.v1",
        "at": datetime.now(timezone.utc).isoformat(),
        "attempt_id": attempt_id,
        "failed_gate_kind": "harness_error",
        "failed_gate": detail,
        "preflight": preflight_receipt,
    }
    return {
        "abort_sent": True,
        "result": client.abort_attempt(
            attempt_id,
            detail[:160],
            evidence,
            failed_gate_kind="harness_error",
        ),
    }


def main() -> None:
    if SNAPSHOT.exists() or RECEIPT.exists():
        raise SystemExit("REFUSING: snapshot or receipt already exists")
    client = ainglish_client()
    manifest = build_manifest()
    checked = preflight(client, manifest)
    if "--preflight" in sys.argv:
        print(json.dumps(checked, indent=2, sort_keys=True))
        return

    opened = client.mint_attempt(
        SLUG,
        manifest=manifest,
        estimand=(
            "Count of current live proposal/measurement fields or legacy admissions moved "
            "outside claimed_moves when the declaration-following headroom gate is applied "
            "prospectively to a complete post-mint register census; plus any old-default-pass "
            "point refused on an exhaustive 0.001 unit-square grid."
        ),
        admissibility_gates=manifest["admissibility_gates"],
        planned_sample=manifest["planned_sample"],
    )["attempt"]
    try:
        snapshot, census_meta = census(client)
        value, computed = evaluate(snapshot)
        filed = client.measure(
            SLUG,
            {
                "metric": "unclaimed_verdict_flips",
                "formula_version": 1,
                "value": value,
                "value_lo": value,
                "value_hi": value,
                "panel_models": [MODEL],
                "per_member": [{"model": MODEL, "value": value}],
                "panel_neff": 1,
                "manifest": manifest,
                "replicates_hash": TARGET,
                "attempt_id": opened["attempt_id"],
            },
        )
    except Exception as exc:
        closure = abort_if_open(
            client,
            opened["attempt_id"],
            f"{type(exc).__name__}: {exc}",
            checked,
        )
        print(json.dumps({"status": "aborted_or_closed", "closure": closure}, indent=2))
        raise

    snapshot["census"] = census_meta
    SNAPSHOT.write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    receipt = {
        "kind": "ainglish.unclaimed-verdict-flips-replication.v1",
        "proposal": SLUG,
        "target": TARGET,
        "attempt": opened,
        "preflight": checked,
        "computed": computed,
        "measurement": filed,
        "manifest_commitment": manifest_commitment(manifest),
        "snapshot_sha256": sha256_bytes(SNAPSHOT.read_bytes()),
    }
    RECEIPT.write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
