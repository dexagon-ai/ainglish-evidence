#!/usr/bin/env python3
"""Run the frozen timing original once and file every finite outcome."""

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
EVIDENCE = ROOT.parent
SCRIPTS = ROOT.parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402

SLUG = "in-parallel-in-sequence-say-whether-listed-actions-may-overl-2"
METRIC = "comprehension_accuracy_delta"


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=EVIDENCE, check=True, text=True, capture_output=True,
    ).stdout.strip()


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.load(response)


def resource_preflight() -> dict:
    command = [
        "nvidia-smi", "--query-gpu=index,name,memory.used,memory.free,utilization.gpu",
        "--format=csv,noheader,nounits",
    ]
    rows = []
    for line in subprocess.run(command, check=True, capture_output=True, text=True).stdout.splitlines():
        index, name, used, free, utilization = [part.strip() for part in line.split(",", 4)]
        rows.append({
            "index": int(index), "name": name, "used_mib": int(used),
            "free_mib": int(free), "utilization": int(utilization),
        })
    resident = get_json("http://127.0.0.1:11434/api/ps").get("models") or []
    if resident:
        raise SystemExit("REFUSING: shared Ollama has resident models; another participant may be using the GPUs")
    if not any(row["name"] == "NVIDIA GeForce RTX 3090" and row["free_mib"] >= 20_000 for row in rows):
        raise SystemExit("REFUSING: no RTX 3090 currently has at least 20,000 MiB free")
    return {"gpus": rows, "ollama": get_json("http://127.0.0.1:11434/api/version")}


def unload(spec: dict) -> None:
    for reader in spec["panel"]:
        body = json.dumps({"model": reader["model"], "keep_alive": 0}).encode()
        request = urllib.request.Request(
            "http://127.0.0.1:11434/api/generate", data=body,
            headers={"Content-Type": "application/json"},
        )
        try:
            urllib.request.urlopen(request, timeout=60).read()
        except Exception as exc:
            print(f"UNLOAD WARNING {reader['model']}: {exc}", flush=True)


def main() -> None:
    if sdk_version != "0.2.53":
        raise SystemExit(f"REFUSING: SDK {sdk_version} != frozen 0.2.53")
    if list(ROOT.glob("runspec.attempt-*.json")):
        raise SystemExit("REFUSING: this one-shot campaign already has an attempt receipt")
    if git("status", "--porcelain"):
        raise SystemExit("REFUSING: evidence repository is not clean")
    git("merge-base", "--is-ancestor", "HEAD", "origin/main")
    resources = resource_preflight()
    print("RESOURCE PREFLIGHT", json.dumps(resources, sort_keys=True), flush=True)

    spec = json.loads((ROOT / "runspec.json").read_text(encoding="utf-8"))
    client = ainglish_client()
    suggestions = client.suggestions()
    proposal = client.proposal(SLUG, authenticated=True)
    work = [
        row for row in (proposal.get("evidence_readiness") or {}).get("work_items", [])
        if row.get("metric") == METRIC and row.get("state") == "submit_original"
    ]
    if len(work) != 1:
        raise SystemExit("REFUSING: fresh proposal no longer requests this original")
    offered = [
        row for row in suggestions.get("suggestions", [])
        if row.get("slug") == SLUG and row.get("tier") == "measurements" and row.get("executable_now") is True
    ]
    if not offered:
        raise SystemExit("REFUSING: personalized suggestions do not currently offer this original")
    if proposal.get("stage") != "seconded" or proposal.get("superseded_by"):
        raise SystemExit("REFUSING: proposal is no longer the current seconded revision")
    if any(
        row.get("metric") == METRIC and not row.get("replicates_hash")
        for row in proposal.get("measurements") or []
    ):
        raise SystemExit("REFUSING: a comprehension original appeared after carrier freeze")
    if any(
        row.get("state") not in {"completed", "aborted", "superseded"}
        for row in proposal.get("attempts") or []
    ):
        raise SystemExit("REFUSING: another attempt is already open on this proposal")

    items, items_digest = panel_harness.fetch_items(spec["items_url"], spec["items_sha256"])
    manifest = dict(spec, items=items, items_sha256=items_digest)
    attempt = spec["attempt"]
    panel_harness.prepare_reader_instruments(manifest)
    planned_manifest = panel_harness._planned_panel_manifest(manifest)
    preflight = client.preflight_attempt(
        SLUG, planned_manifest, attempt["estimand"], attempt["admissibility_gates"],
        attempt["planned_sample"], proposal_revision=attempt["proposal_revision"],
    )
    print("SERVER PREFLIGHT", json.dumps({"kind": preflight.get("kind")}), flush=True)
    try:
        measurement = panel_harness._run_preregistered_panel(
            manifest, spec, panel_harness.ask, client,
            receipt_dir=str(ROOT), receipt_stem="runspec",
        )
    finally:
        unload(spec)
    if measurement is None:
        raise SystemExit("Panel aborted or refused; retained receipts are authoritative")
    result = {
        "kind": "dexagon.ainglish.parallel-sequence-comprehension-result.v1",
        "manifest_hash": manifest_commitment(measurement["manifest"]),
        "value": measurement["value"],
        "value_lo": measurement["value_lo"],
        "value_hi": measurement["value_hi"],
        "arms": measurement["arms"],
        "calibration": measurement["calibration"],
        "panel_agreement": measurement["panel_agreement"],
        "per_member": measurement["per_member"],
        "stratum_results": measurement.get("stratum_results"),
        "server_preflight": preflight,
    }
    (ROOT / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
