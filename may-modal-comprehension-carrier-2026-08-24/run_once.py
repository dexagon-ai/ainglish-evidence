#!/usr/bin/env python3
"""Mint, run, and file the frozen may-as-* claim carrier once all gates clear."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

from ainglish import __version__ as sdk_version
from ainglish import panel as panel_harness


ROOT = Path(__file__).resolve().parent
EVIDENCE_REPO = ROOT.parent
SCRIPTS = EVIDENCE_REPO.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402
from build_runspec import build  # noqa: E402


SLUG = "may-as-permission-may-as-possibility-does-may-authorize-an-a"


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
    token_rows = [row for row in proposal.get("measurements", []) if row.get("metric") == "token_delta" and row.get("is_replication") is False]
    if not token_rows or token_rows[0].get("settlement_state") != "confirmed":
        state = token_rows[0].get("settlement_state") if token_rows else "absent"
        raise SystemExit(f"REFUSING: token prerequisite settlement is {state}, not confirmed")
    # This is intentionally stronger than the server's metric-presence routing. The proposal says
    # token_delta uses the same frozen items; the existing 16-pair original does not cover this
    # 120-item carrier. A public resolution or superseding same-item receipt must be recorded in
    # carrier-block.json before scientific reader spend.
    resolution = spec.get("carrier_qualification", {}).get("token_scope_resolution")
    if not isinstance(resolution, dict) or not resolution.get("thread_comment_url") or not resolution.get("resolution"):
        raise SystemExit("REFUSING: same-item token-scope mismatch has no public resolution receipt")
    return {
        "suggestions_generated_at": suggestions.get("generated_at"),
        "stage": proposal.get("stage"),
        "token_settlement": token_rows[0].get("settlement_state"),
        "token_scope_resolution": resolution,
    }


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
    measurement = panel_harness._run_preregistered_panel(
        spec, spec, panel_harness.ask, client,
        receipt_dir=str(ROOT), receipt_stem="may-modal-claim",
    )
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
