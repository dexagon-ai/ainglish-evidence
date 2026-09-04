#!/usr/bin/env python3
"""Run the frozen same-identity replication once and file every finite outcome."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import urllib.request

from ainglish import __version__ as sdk_version
from ainglish import panel as panel_harness
from ainglish.client import manifest_commitment


ROOT = Path(__file__).resolve().parent
EVIDENCE_REPO = ROOT.parent
SCRIPTS = ROOT.parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402

SLUG = "same-one-same-kind-same-name"
METRIC = "comprehension_accuracy_delta"
TARGET = "bacb9d4ab57a95aae9fb6d9d4764ef930a3dabaac94f5c9fbf0f5e9f4a1c3621"


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=EVIDENCE_REPO, check=True, text=True, capture_output=True
    ).stdout.strip()


def unload(spec: dict) -> None:
    for reader in spec["panel"]:
        body = json.dumps({"model": reader["model"], "keep_alive": 0}).encode()
        request = urllib.request.Request(
            "http://127.0.0.1:11434/api/generate",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(request, timeout=60).read()


def main() -> None:
    if sdk_version != "0.2.53":
        raise SystemExit(f"REFUSING: SDK {sdk_version} != frozen 0.2.53")
    if list(ROOT.glob("runspec.attempt-*.json")):
        raise SystemExit("REFUSING: this one-shot campaign already has an attempt receipt")
    if git("status", "--porcelain"):
        raise SystemExit("REFUSING: evidence repository is not clean")
    git("merge-base", "--is-ancestor", "HEAD", "origin/main")
    spec = json.loads((ROOT / "runspec.json").read_text(encoding="utf-8"))
    unload(spec)

    client = ainglish_client()
    identity = client.whoami()
    suggestions = client.suggestions()
    proposal = client.proposal(SLUG, authenticated=True)
    work_items = (proposal.get("evidence_readiness") or {}).get("work_items") or []
    matching_work = [
        row for row in work_items
        if row.get("metric") == METRIC
        and row.get("state") == "replicate_original"
        and TARGET in (row.get("target_hashes") or [])
    ]
    if len(matching_work) != 1:
        raise SystemExit("REFUSING: the fresh proposal no longer requests this exact replication")
    suggested = [row for row in suggestions.get("suggestions", []) if row.get("slug") == SLUG]
    if suggested and not any(row.get("executable_now") is True for row in suggested):
        raise SystemExit("REFUSING: personalised suggestions mark this work non-executable")
    if proposal.get("stage") != "measured" or proposal.get("superseded_by"):
        raise SystemExit("REFUSING: proposal is no longer current at measured stage")
    if (proposal.get("proposer") or {}).get("sub") == identity.get("sub"):
        raise SystemExit("REFUSING: executing principal is the proposer")
    targets = [row for row in proposal.get("measurements", []) if row.get("manifest_hash") == TARGET]
    if len(targets) != 1 or (targets[0].get("submitter") or {}).get("sub") == identity.get("sub"):
        raise SystemExit("REFUSING: target is missing or is not independently measurable")
    if any(
        row.get("replicates_hash") == TARGET
        and (row.get("submitter") or {}).get("sub") == identity.get("sub")
        and row.get("settlement_eligible") is True
        for row in proposal.get("measurements") or []
    ):
        raise SystemExit("REFUSING: this identity already supplied a settlement-bearing replication")
    active_attempts = [
        row for row in proposal.get("attempts", [])
        if row.get("state") not in {"completed", "aborted", "superseded"}
    ]
    if active_attempts:
        raise SystemExit("REFUSING: another open attempt is already present on this proposal")

    items, items_digest = panel_harness.fetch_items(spec["items_url"], spec["items_sha256"])
    manifest = dict(spec, items=items, items_sha256=items_digest)
    print(
        "LIVE PREFLIGHT PASS:",
        identity.get("display_name") or identity.get("sub"),
        suggestions.get("generated_at"),
        "proposal-work-item=exact",
        "suggestion-row=" + ("present" if suggested else "rotated-out"),
        flush=True,
    )
    measurement = panel_harness._run_preregistered_panel(
        manifest,
        spec,
        panel_harness.ask,
        client,
        receipt_dir=str(ROOT),
        receipt_stem="runspec",
    )
    unload(spec)
    if measurement is None:
        raise SystemExit("Panel aborted or refused; retained receipts are authoritative")
    result = {
        "kind": "dexagon.ainglish.same-identity-qualified-replication-result.v1",
        "manifest_hash": manifest_commitment(measurement["manifest"]),
        "replicates_hash": TARGET,
        "value": measurement["value"],
        "value_lo": measurement["value_lo"],
        "value_hi": measurement["value_hi"],
        "arms": measurement["arms"],
        "calibration": measurement["calibration"],
        "panel_agreement": measurement["panel_agreement"],
        "per_member": measurement["per_member"],
    }
    (ROOT / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
