#!/usr/bin/env python3
"""Execute the frozen verdict-fail/no-verdict replication once."""

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
PROJECT = EVIDENCE.parent
sys.path.insert(0, str(PROJECT / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.load(response)


def pairs(manifest: dict) -> set[tuple[str, str]]:
    rows = manifest.get("items") or manifest.get("test_set") or []
    return {
        (row["english"], row["ainglish"])
        for row in rows
        if isinstance(row, dict) and not row.get("calibration")
        and isinstance(row.get("english"), str) and isinstance(row.get("ainglish"), str)
    }


def resource_preflight(spec: dict) -> dict:
    rows = []
    command = ["nvidia-smi", "--query-gpu=index,name,memory.used,memory.free,utilization.gpu", "--format=csv,noheader,nounits"]
    for line in subprocess.run(command, check=True, capture_output=True, text=True).stdout.splitlines():
        index, name, used, free, utilization = [part.strip() for part in line.split(",", 4)]
        rows.append({"index": int(index), "name": name, "used_mib": int(used), "free_mib": int(free), "utilization": int(utilization)})
    if not any(row["name"] == "NVIDIA GeForce RTX 3090" and row["free_mib"] >= 20_000 for row in rows):
        raise SystemExit("REFUSING: no RTX 3090 has at least 20,000 MiB free")
    tags = {row["name"]: row["digest"] for row in get_json("http://127.0.0.1:11434/api/tags").get("models", [])}
    for reader in spec["panel"]:
        if tags.get(reader["model"]) != reader["model_digest"].removeprefix("sha256:"):
            raise SystemExit(f"REFUSING: local digest mismatch for {reader['model']}")
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
    if sdk_version != "0.2.52":
        raise SystemExit(f"REFUSING: SDK {sdk_version} != frozen 0.2.52")
    if list(ROOT.glob("runspec.attempt-*.json")) or (ROOT / "result.json").exists():
        raise SystemExit("REFUSING: this one-shot packet already contains an attempt outcome")
    if subprocess.run(["git", "status", "--porcelain"], cwd=EVIDENCE, check=True, capture_output=True, text=True).stdout.strip():
        raise SystemExit("REFUSING: evidence repository must be clean")
    subprocess.run(["git", "merge-base", "--is-ancestor", "HEAD", "origin/main"], cwd=EVIDENCE, check=True)
    spec = json.loads((ROOT / "runspec.json").read_text(encoding="utf-8"))
    print("RESOURCE PREFLIGHT", json.dumps(resource_preflight(spec), sort_keys=True), flush=True)
    client = ainglish_client()
    suggestions = client.suggestions()
    offered = {row.get("replicates_hash") for row in suggestions.get("suggestions", []) if row.get("tier") == "replications"}
    proposal = client.proposal(spec["slug"], authenticated=True)
    live_targets = {
        target
        for item in (proposal.get("evidence_readiness") or {}).get("work_items", [])
        for target in (item.get("target_hashes") or [])
    }
    if spec["replicates_hash"] not in offered or spec["replicates_hash"] not in live_targets:
        outcome = {"state": "not_currently_offered", "suggestions_generated_at": suggestions.get("generated_at"), "replicates_hash": spec["replicates_hash"]}
        (ROOT / "result.json").write_text(json.dumps(outcome, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(outcome, indent=2))
        return
    items, digest = panel_harness.fetch_items(spec["items_url"], spec["items_sha256"])
    manifest = dict(spec, items=items, items_sha256=digest)
    if any(field in manifest for field in ("settlement_strata", "settlement_item_field", "settlement_rule")):
        raise SystemExit("REFUSING: aggregate-only target cannot receive settlement strata")
    current = pairs(manifest)
    prior = set()
    for row in proposal.get("measurements") or []:
        prior_manifest = row.get("manifest")
        if not isinstance(prior_manifest, dict) and row.get("manifest_hash"):
            detail = client.measurement(row["manifest_hash"])
            prior_manifest = detail.get("measurement", detail).get("manifest")
        if isinstance(prior_manifest, dict):
            prior.update(pairs(prior_manifest))
    overlap = current & prior
    if overlap:
        raise SystemExit(f"REFUSING: {len(overlap)} exact complete-pair overlaps")
    print("LIVE PREFLIGHT", json.dumps({"generated_at": suggestions.get("generated_at"), "stage": proposal.get("stage"), "fresh_pair_overlap": 0}), flush=True)
    measurement = panel_harness._run_preregistered_panel(
        manifest, spec, panel_harness.ask, client,
        receipt_dir=str(ROOT), receipt_stem="runspec",
    )
    unload(spec)
    if measurement is None:
        outcome = {"state": "aborted_or_refused", "replicates_hash": spec["replicates_hash"]}
    else:
        outcome = {
            "state": "filed",
            "replicates_hash": spec["replicates_hash"],
            "manifest_hash": manifest_commitment(measurement["manifest"]),
            "value": measurement["value"],
            "value_lo": measurement["value_lo"],
            "value_hi": measurement["value_hi"],
            "arms": measurement["arms"],
            "calibration": measurement["calibration"],
            "panel_agreement": measurement["panel_agreement"],
            "per_member": measurement["per_member"],
            "yield_report": measurement.get("yield_report"),
        }
    (ROOT / "result.json").write_text(json.dumps(outcome, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(outcome, indent=2))


if __name__ == "__main__":
    main()
