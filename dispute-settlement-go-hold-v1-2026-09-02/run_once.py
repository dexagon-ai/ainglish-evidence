#!/usr/bin/env python3
"""Mint, execute, and file the frozen dispute replication exactly once."""

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
SCRIPTS = ROOT.parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402

TARGET = "7200b1736f5a760108c5f5305109d2a53f5c5b3415e3ff96bfa87ea389b5ff51"


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=15) as response:
        return json.load(response)


def gpu_preflight() -> dict:
    command = ["nvidia-smi", "--query-gpu=index,name,memory.used,memory.free,utilization.gpu", "--format=csv,noheader,nounits"]
    rows = []
    for line in subprocess.run(command, check=True, capture_output=True, text=True).stdout.splitlines():
        index, name, used, free, utilization = [part.strip() for part in line.split(",", 4)]
        rows.append({"index": int(index), "name": name, "used_mib": int(used), "free_mib": int(free), "utilization": int(utilization)})
    if not any(row["name"] == "NVIDIA GeForce RTX 3090" and row["free_mib"] >= 20_000 for row in rows):
        raise SystemExit("REFUSING: no RTX 3090 currently has at least 20,000 MiB free")
    if get_json("http://127.0.0.1:11434/api/ps").get("models"):
        raise SystemExit("REFUSING: the shared Ollama endpoint has a resident model before mint")
    return {"gpus": rows, "ollama": get_json("http://127.0.0.1:11434/api/version")}


def unload(spec: dict) -> None:
    for reader in spec["panel"]:
        request = urllib.request.Request(
            "http://127.0.0.1:11434/api/generate",
            data=json.dumps({"model": reader["model"], "keep_alive": 0}).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            urllib.request.urlopen(request, timeout=60).read()
        except Exception as exc:
            print(f"UNLOAD WARNING {reader['model']}: {exc}", flush=True)


def main() -> None:
    if sdk_version != "0.2.48":
        raise SystemExit(f"REFUSING: SDK {sdk_version} != frozen 0.2.48")
    if list(ROOT.glob("runspec.attempt-*.measurement.json")) or (ROOT / "result.json").exists():
        raise SystemExit("REFUSING: this one-shot directory already has a result receipt")
    spec = json.loads((ROOT / "runspec.json").read_text(encoding="utf-8"))
    preflight = gpu_preflight()
    print("RESOURCE PREFLIGHT:", json.dumps(preflight, sort_keys=True), flush=True)
    client = ainglish_client()
    suggestions = client.suggestions()
    offered = [row for row in suggestions.get("suggestions", []) if row.get("replicates_hash") == TARGET]
    if len(offered) != 1 or not offered[0].get("confirmation_capable") or not offered[0].get("executable_now"):
        raise SystemExit("REFUSING: the fresh personalised queue no longer offers the target as executable and confirmation-capable")
    proposal = client.proposal(spec["slug"], authenticated=True)
    if proposal.get("stage") != "measured" or proposal.get("superseded_by"):
        raise SystemExit("REFUSING: the target proposal is no longer the current measured row")
    if (proposal.get("proposer") or {}).get("sub") == suggestions.get("sub"):
        raise SystemExit("REFUSING: the current principal proposed the target")
    target_rows = [
        row for row in (proposal.get("evidence_readiness") or {}).get("work_items", [])
        if row.get("metric") == "comprehension_accuracy_delta" and TARGET in (row.get("target_hashes") or [])
    ]
    if len(target_rows) != 1:
        raise SystemExit("REFUSING: the live evidence contract no longer names this target")
    items, items_digest = panel_harness.fetch_items(spec["items_url"], spec["items_sha256"])
    manifest = dict(spec, items=items, items_sha256=items_digest)
    print(f"START after authenticated suggestions {suggestions.get('generated_at')}", flush=True)
    measurement = panel_harness._run_preregistered_panel(
        manifest, spec, panel_harness.ask, client,
        receipt_dir=str(ROOT), receipt_stem="runspec",
    )
    unload(spec)
    if measurement is None:
        raise SystemExit("ABORTED OR REFUSED: inspect the typed receipt; no measurement was emitted")
    proposal_after = client.proposal(spec["slug"], authenticated=True)
    result = {
        "kind": "dexagon.ainglish.go-hold-dispute-result.v1",
        "manifest_hash": manifest_commitment(measurement["manifest"]),
        "replicates_hash": TARGET,
        "value": measurement["value"], "value_lo": measurement["value_lo"], "value_hi": measurement["value_hi"],
        "arms": measurement["arms"], "calibration": measurement["calibration"],
        "panel_agreement": measurement["panel_agreement"], "per_member": measurement["per_member"],
        "stratum_results": measurement.get("stratum_results"),
        "post_filing_stage": proposal_after.get("stage"),
        "post_filing_consensus": proposal_after.get("replication_consensus"),
    }
    (ROOT / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
