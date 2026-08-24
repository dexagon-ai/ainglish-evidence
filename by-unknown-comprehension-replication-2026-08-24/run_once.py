#!/usr/bin/env python3
"""Mint, execute, and file the frozen by-unknown replication once."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import urllib.request

from ainglish import __version__ as sdk_version
from ainglish import panel as panel_harness
from ainglish.client import manifest_commitment


ROOT = Path(__file__).resolve().parent
RUNSPEC = ROOT / "runspec-gpu0.json"
RUNSPEC_SHA256 = "a47a9a709a2cf69c8f6109c0969a6df7f3fa36890052000dce771da6d45bd38a"
ORIGINAL_ITEMS_SHA256 = "4865276dd1616fc4464c008fb23f728431da283b931f9a7834d3f63b0e8ac2cf"
SCRIPTS = ROOT.parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.load(response)


def gpu_preflight() -> dict:
    command = [
        "nvidia-smi",
        "--query-gpu=index,pci.bus_id,name,memory.used,memory.free,utilization.gpu",
        "--format=csv,noheader,nounits",
    ]
    rows = []
    for line in subprocess.run(command, check=True, capture_output=True, text=True).stdout.splitlines():
        index, pci, name, used, free, utilization = [part.strip() for part in line.split(",", 5)]
        rows.append({
            "index": int(index),
            "pci_bus_id": pci,
            "name": name,
            "memory_used_mib": int(used),
            "memory_free_mib": int(free),
            "utilization_percent": int(utilization),
        })
    selected = next((row for row in rows if row["index"] == 0), None)
    if selected is None or selected["name"] != "NVIDIA GeForce RTX 3090":
        raise SystemExit("REFUSING: frozen RTX 3090 GPU 0 is unavailable")
    if selected["memory_free_mib"] < 20_000:
        raise SystemExit("REFUSING: GPU 0 has less than 20,000 MiB free")
    if get_json("http://127.0.0.1:11435/api/ps").get("models"):
        raise SystemExit("REFUSING: dedicated reader already has a resident model")
    return selected


def main() -> None:
    if sdk_version != "0.2.35":
        raise SystemExit(f"REFUSING: SDK {sdk_version} != frozen 0.2.35")
    digest = hashlib.sha256(RUNSPEC.read_bytes()).hexdigest()
    if digest != RUNSPEC_SHA256:
        raise SystemExit(f"REFUSING: runspec drifted: {digest}")
    if list(ROOT.glob("by-unknown.attempt-*.json")):
        raise SystemExit("REFUSING: an attempt receipt already exists; do not rerun")
    selected = gpu_preflight()
    spec = json.loads(RUNSPEC.read_text())
    items, items_digest = panel_harness.fetch_items(
        spec["items_url"], spec.get("items_sha256"),
    )
    manifest = dict(spec, items=items, items_sha256=items_digest)

    client = ainglish_client()
    proposal = client.proposal(spec["slug"], authenticated=True)
    targets = {row.get("manifest_hash"): row for row in proposal.get("measurements", [])}
    target = targets.get(spec["replicates_hash"])
    if target is None or target.get("metric") != spec["metric"]:
        raise SystemExit("REFUSING: frozen target is absent or metric-mismatched")
    source = client.measurement(spec["replicates_hash"])
    if source.get("settlement_state") != "awaiting":
        raise SystemExit("REFUSING: target no longer awaits settlement")
    if source.get("replication_count", 0) or source.get("disagreement_count", 0):
        raise SystemExit("REFUSING: target already has an eligible replication; reselect work")
    if source.get("manifest", {}).get("items_sha256") != ORIGINAL_ITEMS_SHA256:
        raise SystemExit("REFUSING: target's original carrier digest drifted")

    print("GPU PREFLIGHT:", json.dumps(selected, sort_keys=True), flush=True)
    measurement = panel_harness._run_preregistered_panel(
        manifest,
        spec,
        panel_harness.ask,
        client,
        receipt_dir=str(ROOT),
        receipt_stem="by-unknown",
    )
    if measurement is None:
        raise SystemExit(1)
    print(json.dumps({
        "manifest_hash": manifest_commitment(measurement["manifest"]),
        "value": measurement["value"],
        "value_lo": measurement["value_lo"],
        "value_hi": measurement["value_hi"],
        "arms": measurement["arms"],
        "calibration": measurement["calibration"],
        "panel_agreement": measurement["panel_agreement"],
        "per_member": measurement["per_member"],
    }, indent=2))


if __name__ == "__main__":
    main()
