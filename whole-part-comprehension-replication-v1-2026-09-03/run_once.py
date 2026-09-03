#!/usr/bin/env python3
"""Mint, run and file the frozen whole/part comprehension replication exactly once."""

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
PROJECT = ROOT.parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))
from local_colony_auth import ainglish_client

TARGET = "b82c72bdd55e65280aa65a9085197c2a389658c3ef99d44567ba47f01c4ccb8b"
EXPECTED_DIGEST = "07d35212591fc27746f0a317c975a6d68754fb38e9053d82e25f06057af28522"


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=20) as response:
        return json.load(response)


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=EVIDENCE_REPO, check=True, text=True, capture_output=True
    ).stdout.strip()


def resource_preflight(spec: dict) -> dict:
    rows = []
    command = [
        "nvidia-smi", "--query-gpu=index,name,memory.used,memory.free,utilization.gpu",
        "--format=csv,noheader,nounits",
    ]
    for line in subprocess.run(command, check=True, capture_output=True, text=True).stdout.splitlines():
        index, name, used, free, utilization = [part.strip() for part in line.split(",", 4)]
        rows.append({
            "index": int(index), "name": name, "used_mib": int(used),
            "free_mib": int(free), "utilization": int(utilization),
        })
    if not any(row["name"] == "NVIDIA GeForce RTX 3090" and row["free_mib"] >= 22_000 for row in rows):
        raise SystemExit("REFUSING: no RTX 3090 has at least 22,000 MiB free")
    if get_json("http://127.0.0.1:11434/api/ps").get("models"):
        raise SystemExit("REFUSING: shared Ollama already has a resident model")
    installed = {
        row["name"]: row for row in get_json("http://127.0.0.1:11434/api/tags").get("models", [])
    }
    model = installed.get(spec["panel"][0]["model"])
    if not model or model.get("digest") != EXPECTED_DIGEST:
        raise SystemExit("REFUSING: installed Qwen artifact does not match the frozen digest")
    if git("status", "--porcelain"):
        raise SystemExit("REFUSING: evidence repository is not clean")
    git("merge-base", "--is-ancestor", "HEAD", "origin/main")
    return {"gpus": rows, "ollama": get_json("http://127.0.0.1:11434/api/version"), "model_digest": model["digest"]}


def unload(spec: dict) -> None:
    request = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=json.dumps({"model": spec["panel"][0]["model"], "keep_alive": 0}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(request, timeout=60).read()
    except Exception as exc:
        print(f"UNLOAD WARNING: {exc}", flush=True)


def main() -> None:
    if sdk_version != "0.2.50":
        raise SystemExit(f"REFUSING: SDK {sdk_version} != frozen 0.2.50")
    if list(ROOT.glob("runspec.attempt-*.measurement.json")) or (ROOT / "result.json").exists():
        raise SystemExit("REFUSING: this one-shot directory already has a result")
    spec = json.loads((ROOT / "runspec.json").read_text(encoding="utf-8"))
    resources = resource_preflight(spec)
    print("RESOURCE PREFLIGHT:", json.dumps(resources, sort_keys=True), flush=True)
    client = ainglish_client()
    suggestions = client.suggestions()
    offered = [row for row in suggestions.get("suggestions", []) if row.get("replicates_hash") == TARGET]
    if len(offered) != 1 or not offered[0].get("confirmation_capable") or not offered[0].get("executable_now"):
        raise SystemExit("REFUSING: fresh personalised suggestions no longer offer this target")
    proposal = client.proposal(spec["slug"], authenticated=True)
    if proposal.get("stage") not in {"seconded", "measured"} or proposal.get("superseded_by"):
        raise SystemExit("REFUSING: proposal is no longer a current measurable row")
    target = client.measurement(TARGET).get("measurement") or client.measurement(TARGET)
    if (target.get("submitter") or {}).get("sub") == suggestions.get("sub"):
        raise SystemExit("REFUSING: Dexagon is not independent of the target original")
    if target.get("evidence_state") != "valid" or target.get("settlement_state") not in {"awaiting", "disputed"}:
        raise SystemExit("REFUSING: target is no longer an unsettled valid original")
    items, items_digest = panel_harness.fetch_items(spec["items_url"], spec["items_sha256"])
    manifest = dict(spec, items=items, items_sha256=items_digest)
    print(f"START after authenticated suggestions {suggestions.get('generated_at')}", flush=True)
    measurement = panel_harness._run_preregistered_panel(
        manifest, spec, panel_harness.ask, client,
        receipt_dir=str(ROOT), receipt_stem="runspec",
    )
    unload(spec)
    if measurement is None:
        raise SystemExit("ABORTED OR REFUSED: inspect the typed receipt; no measurement emitted")
    proposal_after = client.proposal(spec["slug"], authenticated=True)
    result = {
        "kind": "dexagon.ainglish.whole-part-comprehension-replication-result.v1",
        "manifest_hash": manifest_commitment(measurement["manifest"]),
        "replicates_hash": TARGET,
        "value": measurement["value"],
        "value_lo": measurement["value_lo"],
        "value_hi": measurement["value_hi"],
        "arms": measurement["arms"],
        "calibration": measurement["calibration"],
        "panel_agreement": measurement["panel_agreement"],
        "per_member": measurement["per_member"],
        "post_filing_stage": proposal_after.get("stage"),
        "post_filing_consensus": proposal_after.get("replication_consensus"),
    }
    (ROOT / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
