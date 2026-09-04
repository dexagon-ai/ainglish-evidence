#!/usr/bin/env python3
"""Run the frozen snapshot/live-view carrier once on qualified local readers."""

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

SLUG = "send-snapshot-version-ref-to-recipient-grant-live-view"
METRIC = "comprehension_accuracy_delta"
RUNSPEC = ROOT / "runspec-local-qualified.json"


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=EVIDENCE_REPO, check=True, text=True, capture_output=True
    ).stdout.strip()


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=20) as response:
        return json.load(response)


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
    if sdk_version != "0.2.52":
        raise SystemExit(f"REFUSING: SDK {sdk_version} != frozen 0.2.52")
    if list(ROOT.glob("runspec-local-qualified.attempt-*.json")):
        raise SystemExit("REFUSING: this qualified one-shot run already has an attempt receipt")
    if git("status", "--porcelain"):
        raise SystemExit("REFUSING: evidence repository is not clean")
    git("merge-base", "--is-ancestor", "HEAD", "origin/main")
    spec = json.loads(RUNSPEC.read_text(encoding="utf-8"))
    unload(spec)
    client = ainglish_client()
    identity = client.whoami()
    suggestions = client.suggestions()
    matches = [row for row in suggestions.get("suggestions", []) if row.get("slug") == SLUG]
    if len(matches) != 1:
        raise SystemExit(f"REFUSING: expected one live suggestion for {SLUG}, got {len(matches)}")
    work = matches[0].get("evidence_work") or {}
    if not (
        matches[0].get("executable_now") is True
        and work.get("metric") == METRIC
        and work.get("role") == "claim_carrier"
        and work.get("state") == "submit_original"
    ):
        raise SystemExit(f"REFUSING: live suggestion changed: {work!r}")
    proposal = client.proposal(SLUG, authenticated=True)
    if (proposal.get("proposer") or {}).get("sub") == identity.get("sub"):
        raise SystemExit("REFUSING: executing principal is the proposer")
    if proposal.get("stage") != "measured" or proposal.get("superseded_by"):
        raise SystemExit("REFUSING: proposal is no longer current at measured stage")
    for receipt in spec.get("reader_qualifications") or []:
        if not receipt.get("result", {}).get("passed"):
            raise SystemExit("REFUSING: a reader qualification did not pass")
    items, items_digest = panel_harness.fetch_items(spec["items_url"], spec["items_sha256"])
    manifest = dict(spec, items=items, items_sha256=items_digest)
    print(
        "LIVE PREFLIGHT PASS:",
        identity.get("display_name") or identity.get("sub"),
        suggestions.get("generated_at"),
        get_json("http://127.0.0.1:11434/api/version"),
        flush=True,
    )
    measurement = panel_harness._run_preregistered_panel(
        manifest,
        spec,
        panel_harness.ask,
        client,
        receipt_dir=str(ROOT),
        receipt_stem="runspec-local-qualified",
    )
    unload(spec)
    if measurement is None:
        raise SystemExit("Panel aborted or refused; retained receipts are authoritative")
    result = {
        "kind": "dexagon.ainglish.snapshot-live-qualified-local-result.v1",
        "manifest_hash": manifest_commitment(measurement["manifest"]),
        "value": measurement["value"],
        "value_lo": measurement["value_lo"],
        "value_hi": measurement["value_hi"],
        "arms": measurement["arms"],
        "calibration": measurement["calibration"],
        "panel_agreement": measurement["panel_agreement"],
        "per_member": measurement["per_member"],
        "stratum_results": measurement.get("stratum_results"),
    }
    (ROOT / "local-qualified-result.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
