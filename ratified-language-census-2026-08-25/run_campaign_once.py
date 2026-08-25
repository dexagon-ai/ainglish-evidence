#!/usr/bin/env python3
"""Run one proposal-level cold/reference census campaign under one minted attempt."""

from __future__ import annotations

import argparse
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
REPO = ROOT.parent
PROJECT = REPO.parent
QUALIFICATION = REPO / "reader-qualification-v5-2026-08-25" / "selected-result.json"
sys.path.insert(0, str(PROJECT / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()


def gpu_preflight() -> list[dict]:
    output = subprocess.run([
        "nvidia-smi", "--query-gpu=index,name,memory.free,utilization.gpu", "--format=csv,noheader,nounits",
    ], check=True, capture_output=True, text=True).stdout
    rows = []
    for line in output.splitlines():
        index, name, free, utilization = [part.strip() for part in line.split(",", 3)]
        rows.append({"index": int(index), "name": name, "free_mib": int(free), "utilization": int(utilization)})
    if sum(row["free_mib"] for row in rows) < 36_000 or max(row["utilization"] for row in rows) > 35:
        raise SystemExit("REFUSING: GPU gate failed")
    with urllib.request.urlopen("http://127.0.0.1:11434/api/ps", timeout=30) as response:
        if json.load(response).get("models"):
            raise SystemExit("REFUSING: an Ollama model is already resident")
    return rows


def qualified_panel(seed: int) -> tuple[list[dict], dict]:
    result = json.loads(QUALIFICATION.read_text())
    fixed = result.get("fixed_roster", [])
    if not result.get("roster_ready") or len({row["lineage"] for row in fixed}) < 2:
        raise SystemExit("REFUSING: fewer than two qualified reader lineages")
    panel = [{
        "name": row["name"] + "-census", "provider": "ollama", "model": row["model"],
        "model_digest": row["model_digest"], "precision": row["precision"],
        "api": "openai", "base_url": "http://127.0.0.1:11434/v1",
        "max_tokens": 32, "timeout_s": row["timeout_s"], "temperature": 0, "seed": seed,
    } for row in fixed]
    return panel, result


def unload(panel: list[dict]) -> None:
    for reader in panel:
        data = json.dumps({"model": reader["model"], "prompt": "", "stream": False, "keep_alive": 0}).encode()
        request = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(request, timeout=60).read()


def load_packet(meta: dict, commit: str, panel: list[dict], seed: int) -> dict:
    payload = json.loads((ROOT / meta["file"]).read_text())
    items = payload["items"]
    digest = hashlib.sha256(canonical(items)).hexdigest()
    if digest != meta["items_sha256"] or digest != payload["sha256"]:
        raise SystemExit(f"REFUSING: packet drift in {meta['file']}")
    return {
        "construct": f"{meta['campaign']} {meta['condition']} post-ratification census",
        "slug": meta["slug"], "metric": "comprehension_accuracy_delta", "seed": seed,
        "planted_arm": "ainglish", "calibration_min_gap": 0.5,
        "panel_neff": len(panel), "panel": panel,
        "comparator": {
            "kind": f"ratified-census-{meta['condition']}-careful-english-v1",
            "description": (
                "The registered compact form compared with its complete careful-English meaning in a cold standalone condition."
                if meta["condition"] == "cold" else
                "Both arms receive the same frozen concise construct reference before compact-form versus complete-English comparison."
            ),
        },
        "items_url": f"https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{commit}/ratified-language-census-2026-08-25/{meta['file']}",
        "items_sha256": digest, "items": items,
    }


def form_summary(cells: list[dict]) -> dict:
    out = {}
    forms = sorted({row.get("strata", {}).get("form") for row in cells if row.get("strata", {}).get("form")})
    for form in forms:
        own = [row for row in cells if row.get("strata", {}).get("form") == form]
        arms = {}
        for arm in ("english", "ainglish"):
            arm_rows = [row for row in own if row["arm"] == arm and row.get("correct") is not None]
            arms[arm] = sum(bool(row["correct"]) for row in arm_rows) / len(arm_rows) if arm_rows else None
        out[form] = {"cells": len(own), "arms": arms, "delta_pp": round(100 * (arms["ainglish"] - arms["english"]), 4) if None not in arms.values() else None}
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign", required=True)
    args = parser.parse_args()
    if sdk_version != "0.2.35":
        raise SystemExit(f"REFUSING: SDK {sdk_version} != frozen 0.2.35")
    index = json.loads((ROOT / "index.json").read_text())
    key_cold = f"{args.campaign}:cold"
    key_reference = f"{args.campaign}:reference"
    if key_cold not in index["proposal_packets"] or key_reference not in index["proposal_packets"]:
        raise SystemExit(f"unknown campaign {args.campaign!r}")
    stem = ROOT / f"campaign-{args.campaign}"
    paths = [Path(str(stem) + suffix) for suffix in (".attempt.json", ".reference.cells.json", ".reference.result.json", ".cold.cells.json", ".cold.result.json", ".measurement.json")]
    if any(path.exists() for path in paths):
        raise SystemExit("REFUSING: campaign receipt exists; never rerun")
    if git("status", "--porcelain"):
        raise SystemExit("REFUSING: repository is not clean")
    commit = git("rev-parse", "HEAD")
    if commit != git("rev-parse", "origin/main"):
        raise SystemExit("REFUSING: source commit is not public")
    devices = gpu_preflight()
    seed = 2026082521 + sorted({key.split(":")[0] for key in index["proposal_packets"]}).index(args.campaign)
    panel, qualification = qualified_panel(seed)
    cold_meta = index["proposal_packets"][key_cold]
    ref_meta = index["proposal_packets"][key_reference]
    cold = load_packet(cold_meta, commit, panel, seed)
    reference = load_packet(ref_meta, commit, panel, seed)
    client = ainglish_client()
    suggestions = client.suggestions()
    queue = client.queue()
    proposal = client.proposal(cold_meta["slug"], authenticated=True)
    if proposal.get("stage") != "ratified" or proposal.get("superseded_by"):
        raise SystemExit("REFUSING: proposal is not the current ratified lifecycle")
    if not any((row.get("slug") or row.get("proposal_slug")) == cold_meta["slug"] for row in queue.get("needs_recertification", [])):
        raise SystemExit("REFUSING: live recertification queue no longer routes this proposal")
    planned = panel_harness._planned_panel_manifest(cold)
    opened = client.mint_attempt(
        cold_meta["slug"], planned,
        estimand=f"Post-ratification cold census for {args.campaign}: percentage-point exact consequence accuracy of the compact form minus its complete careful-English meaning across the frozen balanced proposal-level packet. A same-item, same-reader reference-loaded comparison is a separately reported deployment diagnostic and not pooled into the filed scalar.",
        admissibility_gates=[
            "fresh authenticated suggestions, recertification queue, and current proposal are read before mint",
            f"cold packet {cold_meta['items_sha256']} and reference-loaded packet {ref_meta['items_sha256']} are public before mint",
            "both reference-loaded arms receive a byte-identical concise construct card",
            "cold and reference-loaded conditions are reported separately and never pooled",
            "all sibling forms remain visible in per-form strata even though the filed proposal-level scalar is balanced",
            "at least two distinct reader lineages passed the frozen ordinary-English qualification holdout",
            "every supportive, adverse, null, calibration-refused, or transport outcome is retained without retry",
        ],
        planned_sample={
            "cold_scientific_items": cold_meta["scientific"], "reference_scientific_items": ref_meta["scientific"],
            "forms": cold_meta["forms"], "calibration_items_per_condition": 8,
            "readers": len(panel), "reader_lineages": [row["lineage"] for row in qualification["fixed_roster"]],
            "cold_items_sha256": cold_meta["items_sha256"], "reference_items_sha256": ref_meta["items_sha256"],
        },
        proposal_revision=cold_meta["slug"],
    )["attempt"]
    paths[0].write_text(json.dumps({
        "attempt": opened, "source_commit": commit, "suggestions_generated_at": suggestions.get("generated_at"),
        "gpu_preflight": devices, "planned_manifest": planned,
    }, indent=2) + "\n")
    try:
        reference_cells = []
        reference_calibration = []
        ref_result = panel_harness.run_panel(reference, ask_fn=panel_harness.ask, cell_results=reference_cells, calibration_results=reference_calibration)
        paths[1].write_text(json.dumps({"scientific": reference_cells, "calibration": reference_calibration}, indent=2) + "\n")
        paths[2].write_text(json.dumps(ref_result, indent=2, ensure_ascii=False) + "\n")
        if ref_result is None or panel_harness._is_panel_refusal(ref_result):
            client.abort_attempt(opened["attempt_id"], "reference-loaded census condition refused", ref_result or {"state": "no_measurement"}, failed_gate_kind="diagnostic_refusal")
            return
        cold_cells = []
        cold_calibration = []
        cold_result = panel_harness.run_panel(cold, ask_fn=panel_harness.ask, cell_results=cold_cells, calibration_results=cold_calibration)
        paths[3].write_text(json.dumps({"scientific": cold_cells, "calibration": cold_calibration}, indent=2) + "\n")
        paths[4].write_text(json.dumps(cold_result, indent=2, ensure_ascii=False) + "\n")
        if cold_result is None or panel_harness._is_panel_refusal(cold_result):
            client.abort_attempt(opened["attempt_id"], "cold census carrier refused", cold_result or {"state": "no_measurement"}, failed_gate_kind="panel_refusal")
            return
        if manifest_commitment(cold_result["manifest"]) != manifest_commitment(planned):
            client.abort_attempt(opened["attempt_id"], "cold census manifest diverged from preregistration", {
                "planned": manifest_commitment(planned), "actual": manifest_commitment(cold_result["manifest"]),
            }, failed_gate_kind="preflight_mismatch")
            return
        cold_result["attempt_id"] = opened["attempt_id"]
        filed = client.measure(cold_meta["slug"], cold_result)
        summary = {
            "campaign": args.campaign, "attempt_id": opened["attempt_id"],
            "cold": {"value": cold_result["value"], "arms": cold_result["arms"], "per_form": form_summary(cold_cells)},
            "reference": {"value": ref_result["value"], "arms": ref_result["arms"], "per_form": form_summary(reference_cells)},
        }
        paths[5].write_text(json.dumps({"request": cold_result, "receipt": filed, "summary": summary}, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps(summary, indent=2))
    finally:
        unload(panel)


if __name__ == "__main__":
    main()
