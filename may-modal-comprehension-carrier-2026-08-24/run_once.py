#!/usr/bin/env python3
"""Mint, run, and file the frozen may-as-* claim carrier once all gates clear."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from ainglish import __version__ as sdk_version
from ainglish import panel as panel_harness
from ainglish.client import AinglishError, manifest_commitment


ROOT = Path(__file__).resolve().parent
EVIDENCE_REPO = ROOT.parent
SCRIPTS = EVIDENCE_REPO.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402
from build_runspec import build  # noqa: E402


SLUG = "may-as-permission-may-as-possibility-does-may-authorize-an-a"
TOKEN_MEASUREMENT = "285d943697fc1567fc3c3d00ffd160942226b712aee71ed244f16829b8601e7e"
TOKEN_ITEMS_SHA256 = "93f211fac85d0631a69d63d861f137f5cd1c18294c24a239435dce88c6e6d2cb"


def git_output(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=EVIDENCE_REPO, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    ).stdout.strip()


def preflight(client, spec: dict) -> dict:
    if sdk_version != "0.2.35":
        raise SystemExit(f"REFUSING: SDK {sdk_version} != frozen 0.2.35")
    if git_output("status", "--porcelain"):
        raise SystemExit("REFUSING: evidence repository is not clean")
    if git_output("rev-parse", "HEAD") != git_output("rev-parse", "origin/main"):
        raise SystemExit("REFUSING: evidence packet is not published at origin/main")
    suggestions = client.suggestions()
    proposal = client.proposal(SLUG, authenticated=True)
    if proposal.get("stage") not in ("seconded", "measured"):
        raise SystemExit(f"REFUSING: live stage is {proposal.get('stage')!r}")
    if any(row.get("metric") == "comprehension_accuracy_delta" and row.get("evidence_state") == "valid" for row in proposal.get("measurements", [])):
        raise SystemExit("REFUSING: a valid comprehension original already exists")
    token_rows = [
        row for row in proposal.get("measurements", [])
        if row.get("metric") == "token_delta" and row.get("is_replication") is False
    ]
    exact = next((row for row in token_rows if row.get("manifest_hash") == TOKEN_MEASUREMENT), None)
    if exact is None:
        raise SystemExit("REFUSING: exact 120-item token prerequisite is absent")
    exact_detail = client.measurement(TOKEN_MEASUREMENT)
    if (exact_detail.get("manifest") or {}).get("items_sha256") != TOKEN_ITEMS_SHA256:
        raise SystemExit("REFUSING: exact 120-item token prerequisite is absent or has drifted")
    if exact.get("confirmed") is not True:
        raise SystemExit(
            f"REFUSING: exact 120-item token prerequisite is {exact.get('settlement_state')}, not confirmed"
        )
    if exact_detail.get("stance") != "supports":
        raise SystemExit(
            "REFUSING: exact 120-item token prerequisite has protocol stance "
            f"{exact_detail.get('stance')!r}; the proposal's +4 prose allowance conflicts with "
            "the generic token_delta prerequisite and must be amended or formally represented"
        )
    return {
        "suggestions_generated_at": suggestions.get("generated_at"),
        "stage": proposal.get("stage"),
        "token_measurement": exact.get("manifest_hash"),
        "token_settlement": exact.get("settlement_state"),
        "token_stance": exact_detail.get("stance"),
    }


def diagnostic_spec(spec: dict, mode: str) -> dict:
    filename = {"bare": "bare-items.json", "allowed-to": "allowed-to-items.json"}[mode]
    document = json.loads((ROOT / filename).read_text(encoding="utf-8"))
    derived = json.loads(json.dumps(spec))
    derived["items"] = document["items"]
    derived["items_sha256"] = document["sha256"]
    commit = git_output("rev-parse", "HEAD")
    derived["items_url"] = (
        "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
        f"{commit}/may-modal-comprehension-carrier-2026-08-24/{filename}"
    )
    if mode == "bare":
        derived["comparator"] = {
            "kind": "bare-may-v1",
            "description": "Neutral bare may with the same contexts, later facts, questions, and keyed writer intent.",
        }
    else:
        derived["comparator"] = {
            "kind": "ratified-allowed-to-v1",
            "description": "Permission-only practical comparison against the ratified allowed-to surface.",
        }
    derived.pop("attempt", None)
    return derived


def write_json_once(path: Path, value: object) -> None:
    if path.exists():
        raise SystemExit(f"REFUSING: receipt already exists at {path}")
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def abort(client, attempt_id: str, kind: str, gate: str, details: dict) -> None:
    panel_harness._abort_panel_attempt(
        client, attempt_id, SLUG, kind, gate, details,
        receipt_dir=str(ROOT), receipt_stem="may-modal-claim",
    )


def run_after_mint(client, spec: dict, attempt_id: str, planned: dict) -> dict | None:
    main_cells: list[dict] = []
    main_calibration: list[dict] = []
    try:
        main_measurement = panel_harness.run_panel(
            spec, ask_fn=panel_harness.ask,
            cell_results=main_cells, calibration_results=main_calibration,
        )
    except (Exception, SystemExit) as exc:
        abort(client, attempt_id, "harness_error", "claim panel raised before measurement emission", {
            "exception": type(exc).__name__, "message": str(exc),
            "completed_real_cells": len(main_cells),
            "completed_calibration_cells": len(main_calibration),
        })
        raise
    main_calibration_receipt = panel_harness._write_cell_results(
        attempt_id, SLUG, main_calibration, str(ROOT), "may-modal-claim", stage="calibration",
    )
    main_cell_receipt = panel_harness._write_cell_results(
        attempt_id, SLUG, main_cells, str(ROOT), "may-modal-claim",
    )
    if main_measurement is None or panel_harness._is_panel_refusal(main_measurement):
        refusal = main_measurement or {"stage": "unknown", "reason": "no measurement"}
        kind = (
            panel_harness._panel_refusal_failed_gate_kind(refusal)
            if main_measurement is not None else "no_measurement"
        )
        abort(client, attempt_id, kind, "claim panel refused before diagnostics", {
            "refusal": refusal,
            "calibration_cell_results": main_calibration_receipt,
            "cell_results": main_cell_receipt,
        })
        return None
    if manifest_commitment(main_measurement["manifest"]) != manifest_commitment(planned):
        abort(client, attempt_id, "preflight_mismatch", "claim manifest diverged from preregistration", {
            "expected": manifest_commitment(planned),
            "actual": manifest_commitment(main_measurement["manifest"]),
            "calibration_cell_results": main_calibration_receipt,
            "cell_results": main_cell_receipt,
        })
        return None

    diagnostic_receipts = {}
    for mode in ("bare", "allowed-to"):
        diag = diagnostic_spec(spec, mode)
        cells: list[dict] = []
        calibration: list[dict] = []
        try:
            result = panel_harness.run_panel(
                diag, ask_fn=panel_harness.ask,
                cell_results=cells, calibration_results=calibration,
            )
        except (Exception, SystemExit) as exc:
            abort(client, attempt_id, "harness_error", f"{mode} diagnostic raised", {
                "exception": type(exc).__name__, "message": str(exc),
                "completed_real_cells": len(cells),
                "completed_calibration_cells": len(calibration),
                "claim_cell_results": main_cell_receipt,
            })
            raise
        cal_receipt = panel_harness._write_cell_results(
            attempt_id, SLUG, calibration, str(ROOT), f"may-modal-{mode}", stage="calibration",
        )
        cell_receipt = panel_harness._write_cell_results(
            attempt_id, SLUG, cells, str(ROOT), f"may-modal-{mode}",
        )
        if result is None or panel_harness._is_panel_refusal(result):
            refusal = result or {"stage": "unknown", "reason": "no measurement"}
            kind = (
                panel_harness._panel_refusal_failed_gate_kind(refusal)
                if result is not None else "no_measurement"
            )
            abort(client, attempt_id, kind, f"{mode} diagnostic refused", {
                "refusal": refusal, "calibration_cell_results": cal_receipt,
                "cell_results": cell_receipt, "claim_cell_results": main_cell_receipt,
            })
            return None
        result_path = ROOT / f"may-modal-{mode}.attempt-{attempt_id}.diagnostic.json"
        write_json_once(result_path, result)
        diagnostic_receipts[mode] = {
            "result_path": str(result_path),
            "result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
            "calibration_cell_results": cal_receipt,
            "cell_results": cell_receipt,
            "value": result.get("value"),
            "arms": result.get("arms"),
        }

    write_json_once(ROOT / f"diagnostics.attempt-{attempt_id}.receipt.json", {
        "kind": "ainglish.may-modal.preregistered-diagnostics.v1",
        "attempt_id": attempt_id,
        "claim_items_sha256": spec["items_sha256"],
        "diagnostics": diagnostic_receipts,
        "reader_calls_before_attempt_mint": 0,
        "claim_executed_before_repeated_diagnostic_items": True,
    })
    main_measurement["attempt_id"] = attempt_id
    panel_harness._write_measurement_request(
        attempt_id, main_measurement, str(ROOT), "may-modal-claim",
    )
    response = None
    for submission in range(2):
        try:
            response = client.measure(SLUG, main_measurement)
            break
        except AinglishError as exc:
            if exc.error not in ("transport_error", "invalid_response"):
                raise
            state = client.attempt(attempt_id)
            if state.get("state") == "completed":
                response = {"attempt": state, "recovered_after_lost_response": True}
                break
            if state.get("state") != "open" or submission == 1:
                raise
    print("SUBMITTED:", json.dumps(response, ensure_ascii=False)[:400])
    return main_measurement


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    spec = build()
    if args.dry_run:
        preview = {**spec, "_dry_run": True}
        measurement = panel_harness.run_panel(
            preview, ask_fn=panel_harness.dry_reader(preview["items"], preview),
        )
        if measurement is None or panel_harness._is_panel_refusal(measurement):
            raise SystemExit(1)
        print(json.dumps({
            "reader_calls": 0,
            "items_sha256": spec["items_sha256"],
            "preview_value": measurement["value"],
            "arms": measurement["arms"],
        }, indent=2))
        return
    client = ainglish_client()
    receipt = preflight(client, spec)
    print("PREFLIGHT", json.dumps(receipt, ensure_ascii=False))
    for pattern in ("may-modal-claim.attempt-*", "diagnostics.attempt-*", "may-modal-bare.attempt-*", "may-modal-allowed-to.attempt-*"):
        if list(ROOT.glob(pattern)):
            raise SystemExit(f"REFUSING: prior receipt matches {pattern}")
    settings = panel_harness._attempt_settings(spec["attempt"])
    panel_harness._validate_real_reader_configuration(spec, panel_harness.ask)
    planned = panel_harness._planned_panel_manifest(spec)
    opened = client.mint_attempt(
        SLUG, planned,
        estimand=settings["estimand"],
        admissibility_gates=settings["admissibility_gates"],
        planned_sample=settings["planned_sample"],
        proposal_revision=settings["proposal_revision"],
    )
    attempt_id = opened["attempt"]["attempt_id"]
    expected = manifest_commitment(planned)
    retained = client.attempt_manifest(attempt_id)
    if manifest_commitment(retained) != expected:
        abort(client, attempt_id, "preflight_mismatch", "server retained different manifest bytes", {
            "expected": expected, "actual": manifest_commitment(retained),
        })
        raise SystemExit(1)
    print(f"ATTEMPT MINTED BEFORE READER SPEND: {attempt_id} (manifest {expected})")
    measurement = run_after_mint(client, spec, attempt_id, planned)
    if measurement is None:
        raise SystemExit(1)
    print(json.dumps({
        "value": measurement["value"],
        "value_lo": measurement["value_lo"],
        "value_hi": measurement["value_hi"],
        "arms": measurement["arms"],
        "calibration": measurement["calibration"],
        "per_member": measurement["per_member"],
    }, indent=2))


if __name__ == "__main__":
    main()
