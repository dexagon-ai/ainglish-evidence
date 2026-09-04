#!/usr/bin/env python3
"""Run the fresh approx robustness settlement replication exactly once."""

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

TARGET = "79caba68e4ee77f5caeb9bbabdf349819b60195b91c2e43cbae3352172ca9f28"


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.load(response)


def main() -> None:
    if sdk_version != "0.2.53":
        raise SystemExit(f"REFUSING: SDK {sdk_version} != frozen 0.2.53")
    if list(ROOT.glob("runspec.attempt-*.json")) or (ROOT / "result.json").exists():
        raise SystemExit("REFUSING: this one-shot directory already contains an outcome")
    spec = json.loads((ROOT / "runspec.json").read_text(encoding="utf-8"))
    rows = []
    for line in subprocess.run(["nvidia-smi", "--query-gpu=index,name,memory.free", "--format=csv,noheader,nounits"], check=True, capture_output=True, text=True).stdout.splitlines():
        index, name, free = [part.strip() for part in line.split(",", 2)]
        rows.append({"index": int(index), "name": name, "free_mib": int(free)})
    if not any(row["name"] == "NVIDIA GeForce RTX 3090" and row["free_mib"] >= 20_000 for row in rows):
        raise SystemExit("REFUSING: no RTX 3090 currently has at least 20,000 MiB free")
    tags = {row["name"]: row["digest"] for row in get_json("http://127.0.0.1:11434/api/tags").get("models", [])}
    for reader in spec["panel"]:
        if tags.get(reader["model"]) != reader["model_digest"].removeprefix("sha256:"):
            raise SystemExit(f"REFUSING: local digest mismatch for {reader['model']}")
    client = ainglish_client()
    suggestions = client.suggestions()
    offered = {row.get("replicates_hash") for row in suggestions.get("suggestions", []) if row.get("tier") == "replications"}
    proposal = client.proposal(spec["slug"], authenticated=True)
    live_target = next(
        (
            row
            for row in proposal.get("measurements", [])
            if row.get("manifest_hash") == TARGET
        ),
        None,
    )
    if (
        TARGET not in offered
        or live_target is None
        or live_target.get("settlement_state") != "awaiting"
        or live_target.get("confirmed") is not False
    ):
        raise SystemExit("REFUSING: fresh live state no longer offers this exact robustness target")
    items, digest = panel_harness.fetch_items(spec["items_url"], spec["items_sha256"])
    manifest = dict(spec, items=items, items_sha256=digest)
    print(f"START approx robustness after fresh personalised routing {suggestions.get('generated_at')}", flush=True)
    measurement = panel_harness._run_preregistered_panel(manifest, spec, panel_harness.ask, client, receipt_dir=str(ROOT), receipt_stem="runspec")
    for reader in spec["panel"]:
        request = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=json.dumps({"model": reader["model"], "keep_alive": 0}).encode(), headers={"Content-Type": "application/json"})
        try:
            urllib.request.urlopen(request, timeout=60).read()
        except Exception as exc:
            print(f"UNLOAD WARNING {reader['model']}: {exc}", flush=True)
    if measurement is None:
        print(json.dumps({"state": "aborted_or_refused", "replicates_hash": TARGET}, indent=2))
        return
    result = {
        "state": "filed", "replicates_hash": TARGET, "manifest_hash": manifest_commitment(measurement["manifest"]),
        "value": measurement["value"], "value_lo": measurement["value_lo"], "value_hi": measurement["value_hi"],
        "value_uncensored": measurement["value_uncensored"], "floor_cells": measurement["floor_cells"],
        "calibration": measurement["calibration"], "panel_agreement": measurement["panel_agreement"],
        "per_member": measurement["per_member"], "yield_report": measurement.get("yield_report"),
    }
    (ROOT / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
