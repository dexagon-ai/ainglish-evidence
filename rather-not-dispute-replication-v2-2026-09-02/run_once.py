#!/usr/bin/env python3
"""Run the fresh rather-not replication exactly once."""

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


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.load(response)


def main() -> None:
    if sdk_version != "0.2.50":
        raise SystemExit(f"REFUSING: SDK {sdk_version} != frozen 0.2.50")
    if list(ROOT.glob("runspec.attempt-*.json")):
        raise SystemExit("REFUSING: this one-shot directory already contains an attempt receipt")
    spec = json.loads((ROOT / "runspec.json").read_text(encoding="utf-8"))
    rows = []
    command = ["nvidia-smi", "--query-gpu=index,name,memory.free", "--format=csv,noheader,nounits"]
    for line in subprocess.run(command, check=True, capture_output=True, text=True).stdout.splitlines():
        index, name, free = [part.strip() for part in line.split(",", 2)]
        rows.append({"index": int(index), "name": name, "free_mib": int(free)})
    if sum(row["free_mib"] for row in rows if row["name"] == "NVIDIA GeForce RTX 3090") < 35_000:
        raise SystemExit("REFUSING: the two RTX 3090s do not expose 35,000 MiB aggregate free memory")
    tags = {row["name"]: row["digest"] for row in get_json("http://127.0.0.1:11434/api/tags").get("models", [])}
    for reader in spec["panel"]:
        if tags.get(reader["model"]) != reader["model_digest"].removeprefix("sha256:"):
            raise SystemExit(f"REFUSING: local digest mismatch for {reader['model']}")
    client = ainglish_client()
    suggestions = client.suggestions()
    targets = {row.get("replicates_hash") for row in suggestions.get("suggestions", []) if row.get("tier") == "replications"}
    if spec["replicates_hash"] not in targets:
        raise SystemExit("REFUSING: fresh authenticated suggestions no longer route this disputed original to Dexagon")
    proposal = client.proposal(spec["slug"], authenticated=True)
    original = next((row for row in proposal.get("measurements", []) if row.get("manifest_hash") == spec["replicates_hash"]), None)
    if not original or original.get("settlement_state") != "disputed" or proposal.get("stage") != "measured" or proposal.get("superseded_by"):
        raise SystemExit("REFUSING: the live proposal or disputed original changed before mint")
    items, items_digest = panel_harness.fetch_items(spec["items_url"], spec["items_sha256"])
    manifest = dict(spec, items=items, items_sha256=items_digest)
    print("START fresh disputed replication after authenticated suggestions and proposal read", flush=True)
    measurement = panel_harness._run_preregistered_panel(
        manifest, spec, panel_harness.ask, client,
        receipt_dir=str(ROOT), receipt_stem="runspec",
    )
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
    if measurement is None:
        print(json.dumps({"state": "aborted_or_refused"}))
        return
    result = {
        "state": "filed",
        "manifest_hash": manifest_commitment(measurement["manifest"]),
        "replicates_hash": spec["replicates_hash"],
        "value": measurement["value"],
        "value_lo": measurement["value_lo"],
        "value_hi": measurement["value_hi"],
        "arms": measurement["arms"],
        "calibration": measurement["calibration"],
        "panel_agreement": measurement["panel_agreement"],
        "per_member": measurement["per_member"],
        "stratum_results": measurement.get("stratum_results"),
        "yield_report": measurement.get("yield_report"),
    }
    (ROOT / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
