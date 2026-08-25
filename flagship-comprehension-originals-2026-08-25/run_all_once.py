#!/usr/bin/env python3
"""Mint, run, and file each frozen flagship carrier exactly once."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request

from ainglish import __version__ as sdk_version
from ainglish import panel as panel_harness
from ainglish.client import manifest_commitment


ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT.parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402


def json_url(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.load(response)


def gpu_preflight() -> dict:
    command = ["nvidia-smi", "--query-gpu=index,name,memory.used,memory.free,utilization.gpu", "--format=csv,noheader,nounits"]
    rows = []
    for line in subprocess.run(command, check=True, capture_output=True, text=True).stdout.splitlines():
        index, name, used, free, utilization = [part.strip() for part in line.split(",", 4)]
        rows.append({"index": int(index), "name": name, "used_mib": int(used), "free_mib": int(free), "utilization": int(utilization)})
    selected = next((row for row in rows if row["index"] == 0), None)
    if selected is None or selected["name"] != "NVIDIA GeForce RTX 3090" or selected["free_mib"] < 20_000:
        raise SystemExit("REFUSING: dedicated RTX 3090 GPU 0 does not have 20,000 MiB free")
    json_url("http://127.0.0.1:11435/api/ps")
    return selected


def unload(spec: dict) -> None:
    for endpoint in spec["panel"]:
        body = json.dumps({"model": endpoint["model"], "keep_alive": 0}).encode()
        request = urllib.request.Request("http://127.0.0.1:11435/api/generate", data=body, headers={"Content-Type": "application/json"})
        try:
            urllib.request.urlopen(request, timeout=30).read()
        except Exception as exc:
            print(f"UNLOAD WARNING for {endpoint['model']}: {exc}", flush=True)


def main() -> None:
    if sdk_version != "0.2.35":
        raise SystemExit(f"REFUSING: SDK {sdk_version} != frozen 0.2.35")
    index = json.loads((ROOT / "runspec-index.json").read_text())
    selected = gpu_preflight()
    print("GPU PREFLIGHT:", json.dumps(selected, sort_keys=True), flush=True)
    client = ainglish_client()
    results = []
    for name, meta in index["campaigns"].items():
        stem = "flagship-" + name
        if list(ROOT.glob(stem + ".attempt-*")):
            print(f"SKIP {name}: an attempt receipt already exists; no rerun", flush=True)
            continue
        path = ROOT / meta["runspec"]
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != meta["runspec_sha256"]:
            raise SystemExit(f"REFUSING: {name} runspec drifted ({actual})")
        spec = json.loads(path.read_text())
        suggestions = client.suggestions()
        proposal = client.proposal(spec["slug"], authenticated=True)
        if proposal["slug"] != spec["slug"] or proposal["stage"] != "ratified" or proposal.get("superseded_by"):
            raise SystemExit(f"REFUSING: {name} live surface is not the frozen current ratified proposal")
        items, items_digest = panel_harness.fetch_items(spec["items_url"], spec["items_sha256"])
        manifest = dict(spec, items=items, items_sha256=items_digest)
        print(f"START {name} after suggestions {suggestions.get('generated_at')}", flush=True)
        measurement = panel_harness._run_preregistered_panel(
            manifest, spec, panel_harness.ask, client, receipt_dir=str(ROOT), receipt_stem=stem,
        )
        unload(spec)
        if measurement is None:
            results.append({"campaign": name, "state": "aborted_or_refused"})
            continue
        results.append({
            "campaign": name, "state": "filed", "manifest_hash": manifest_commitment(measurement["manifest"]),
            "value": measurement["value"], "value_lo": measurement["value_lo"], "value_hi": measurement["value_hi"],
            "arms": measurement["arms"], "calibration": measurement["calibration"],
            "panel_agreement": measurement["panel_agreement"], "per_member": measurement["per_member"],
        })
        print("RESULT:", json.dumps(results[-1], sort_keys=True), flush=True)
    payload = {"kind": "ainglish.flagship-comprehension-original-results.v1", "runspec_index": index["content_sha256"], "results": results}
    (ROOT / "results.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
