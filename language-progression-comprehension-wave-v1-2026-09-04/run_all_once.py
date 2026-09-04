#!/usr/bin/env python3
"""Run each still-eligible original once, preserving adverse and null results."""

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


def gpu_preflight() -> dict:
    rows = []
    command = ["nvidia-smi", "--query-gpu=index,name,memory.used,memory.free,utilization.gpu", "--format=csv,noheader,nounits"]
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
        body = json.dumps({"model": reader["model"], "keep_alive": 0}).encode()
        request = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=body, headers={"Content-Type": "application/json"})
        try:
            urllib.request.urlopen(request, timeout=60).read()
        except Exception as exc:
            print(f"UNLOAD WARNING {reader['model']}: {exc}", flush=True)


def requests_original(proposal: dict) -> bool:
    readiness = proposal.get("evidence_readiness") or {}
    return any(
        item.get("metric") == "comprehension_accuracy_delta" and item.get("state") == "submit_original"
        for item in readiness.get("work_items") or []
    )


def main() -> None:
    if sdk_version != "0.2.52":
        raise SystemExit(f"REFUSING: SDK {sdk_version} != frozen 0.2.52")
    if list(ROOT.glob("runspec-*.attempt-*.json")):
        raise SystemExit("REFUSING: this one-shot directory already contains an attempt receipt")
    index = json.loads((ROOT / "runspec-index.json").read_text(encoding="utf-8"))
    preflight = gpu_preflight()
    print("RESOURCE PREFLIGHT:", json.dumps(preflight, sort_keys=True), flush=True)
    client = ainglish_client()
    suggestions = client.suggestions()
    me = suggestions["sub"]
    results = []
    for name, meta in index["runspecs"].items():
        spec = json.loads((ROOT / meta["file"]).read_text(encoding="utf-8"))
        proposal = client.proposal(spec["slug"], authenticated=True)
        if proposal.get("stage") not in {"seconded", "measured"} or proposal.get("superseded_by") or not requests_original(proposal):
            results.append({"campaign": name, "state": "not_currently_requested"})
            print("SKIP:", json.dumps(results[-1]), flush=True)
            continue
        if (proposal.get("proposer") or {}).get("sub") == me:
            results.append({"campaign": name, "state": "independence_handoff"})
            print("SKIP:", json.dumps(results[-1]), flush=True)
            continue
        items, items_digest = panel_harness.fetch_items(spec["items_url"], spec["items_sha256"])
        manifest = dict(spec, items=items, items_sha256=items_digest)
        print(f"START {name} after authenticated suggestions {suggestions.get('generated_at')}", flush=True)
        measurement = panel_harness._run_preregistered_panel(
            manifest, spec, panel_harness.ask, client,
            receipt_dir=str(ROOT), receipt_stem=f"runspec-{name}",
        )
        unload(spec)
        if measurement is None:
            results.append({"campaign": name, "state": "aborted_or_refused"})
            print("RESULT:", json.dumps(results[-1]), flush=True)
            continue
        result = {
            "campaign": name,
            "state": "filed",
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
        results.append(result)
        print("RESULT:", json.dumps(result, sort_keys=True), flush=True)
    output = {"kind": "dexagon.ainglish.language-progression-comprehension-results.v1", "runspec_index": index["content_sha256"], "results": results}
    (ROOT / "results.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
