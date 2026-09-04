#!/usr/bin/env python3
"""Run the frozen should comprehension original once on qualified readers."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import urllib.request

from ainglish import __version__ as sdk_version
from ainglish import panel as panel_harness
from ainglish.client import manifest_commitment


ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT.parent
SCRIPTS = ROOT.parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402


SLUG = "should-as-rule-should-as-forecast-is-should-a-norm-or-an-exp"
METRIC = "comprehension_accuracy_delta"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=EVIDENCE, check=True, text=True, capture_output=True).stdout.strip()


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=20) as response:
        return json.load(response)


def unload(spec: dict) -> None:
    for reader in spec["panel"]:
        body = json.dumps({"model": reader["model"], "keep_alive": 0}).encode()
        request = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=body, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(request, timeout=60).read()


def main() -> None:
    if sdk_version != "0.2.53":
        raise SystemExit(f"REFUSING: SDK {sdk_version} != 0.2.53")
    if list(ROOT.glob("runspec.attempt-*.json")) or (ROOT / "result.json").exists():
        raise SystemExit("REFUSING: this one-shot carrier already has an outcome")
    if git("status", "--porcelain") or git("rev-parse", "HEAD") != git("rev-parse", "origin/main"):
        raise SystemExit("REFUSING: evidence repository must be clean and published")
    spec = json.loads((ROOT / "runspec.json").read_text(encoding="utf-8"))
    unload(spec)
    gpus = subprocess.run(
        ["nvidia-smi", "--query-gpu=index,name,memory.free,utilization.gpu", "--format=csv,noheader,nounits"],
        check=True, capture_output=True, text=True,
    ).stdout
    if "NVIDIA GeForce RTX 3090" not in gpus or get_json("http://127.0.0.1:11434/api/ps").get("models"):
        raise SystemExit("REFUSING: qualified local reader resource gate failed")

    client = ainglish_client()
    identity = client.whoami()
    suggestions = client.suggestions()
    matches = [row for row in suggestions.get("suggestions") or [] if row.get("slug") == SLUG]
    if len(matches) != 1:
        raise SystemExit(f"REFUSING: expected one fresh suggestion, got {len(matches)}")
    work = matches[0].get("evidence_work") or {}
    if not (matches[0].get("executable_now") is True and work.get("metric") == METRIC and work.get("state") == "submit_original"):
        raise SystemExit(f"REFUSING: live suggestion changed: {work!r}")
    proposal = client.proposal(SLUG, authenticated=True)
    if (proposal.get("proposer") or {}).get("sub") == identity.get("sub") or proposal.get("superseded_by"):
        raise SystemExit("REFUSING: author independence or current-revision gate failed")
    if any((row.get("manifest") or {}).get("items_sha256") == spec["items_sha256"] for row in proposal.get("measurements") or []):
        raise SystemExit("REFUSING: item digest already appears in proposal evidence")
    for receipt in spec["reader_qualifications"]:
        if not receipt.get("result", {}).get("passed"):
            raise SystemExit("REFUSING: a reader qualification did not pass")

    items, digest = panel_harness.fetch_items(spec["items_url"], spec["items_sha256"])
    manifest = dict(spec, items=items, items_sha256=digest)
    print("LIVE PREFLIGHT PASS", suggestions.get("generated_at"), gpus.strip(), flush=True)
    measurement = panel_harness._run_preregistered_panel(
        manifest, spec, panel_harness.ask, client,
        receipt_dir=str(ROOT), receipt_stem="runspec",
    )
    unload(spec)
    if measurement is None:
        raise SystemExit("Panel aborted or refused; retained receipts are authoritative")
    result = {
        "kind": "dexagon.ainglish.should-force-qualified-local-result.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
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
    (ROOT / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
