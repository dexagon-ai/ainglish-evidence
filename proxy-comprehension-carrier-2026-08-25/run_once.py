#!/usr/bin/env python3
"""Run all frozen proxy comparisons once and file only the careful-English carrier."""

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
REPO = ROOT.parent
PROJECT = REPO.parent
QUALIFICATION = REPO / "reader-qualification-v5-2026-08-25" / "result.json"
SLUG = "proxy-m-say-when-the-evidence-you-measured-is-a-proxy-for-th-2"
sys.path.insert(0, str(PROJECT / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()


def get_json(path: str) -> dict:
    with urllib.request.urlopen("http://127.0.0.1:11434" + path, timeout=30) as response:
        return json.load(response)


def unload(panel: list[dict]) -> None:
    for reader in panel:
        body = json.dumps({"model": reader["model"], "prompt": "", "stream": False, "keep_alive": 0}).encode()
        request = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=body, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(request, timeout=60).read()


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
    if get_json("/api/ps").get("models"):
        raise SystemExit("REFUSING: an Ollama model is already resident")
    return rows


def qualified_panel(seed: int) -> tuple[list[dict], dict]:
    result = json.loads(QUALIFICATION.read_text())
    if not result.get("roster_ready") or len({row["lineage"] for row in result.get("fixed_roster", [])}) < 2:
        raise SystemExit("REFUSING: fewer than two qualified reader lineages")
    panel = []
    for row in result["fixed_roster"]:
        panel.append({
            "name": row["name"] + "-proxy", "provider": "ollama", "model": row["model"],
            "model_digest": row["model_digest"], "precision": row["precision"],
            "api": "openai", "base_url": "http://127.0.0.1:11434/v1",
            "max_tokens": 32, "timeout_s": row["timeout_s"], "temperature": 0, "seed": seed,
        })
    return panel, result


def load_packet(name: str, meta: dict, commit: str) -> tuple[list[dict], dict]:
    payload = json.loads((ROOT / meta["file"]).read_text())
    items = payload["items"]
    digest = hashlib.sha256(canonical(items)).hexdigest()
    if digest != meta["items_sha256"] or digest != payload["sha256"]:
        raise SystemExit(f"REFUSING: {name} packet drift")
    spec = {
        "construct": f"proxy(<M>) {name} comparison",
        "slug": SLUG, "metric": "comprehension_accuracy_delta", "seed": 2026082517,
        "planted_arm": "ainglish", "calibration_min_gap": 0.5,
        "panel_neff": 2,
        "comparator": {"kind": f"proxy-{name}-comparison-v1", "description": f"proxy(<M>) compared with the frozen {name} arm"},
        "items_url": f"https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{commit}/proxy-comprehension-carrier-2026-08-25/{meta['file']}",
        "items_sha256": digest, "items": items,
    }
    return items, spec


def main() -> None:
    if sdk_version != "0.2.35":
        raise SystemExit(f"REFUSING: SDK {sdk_version} != frozen 0.2.35")
    paths = [ROOT / name for name in ("attempt.json", "bare-result.json", "obs-result.json", "primary-result.json", "measurement.json")]
    if any(path.exists() for path in paths):
        raise SystemExit("REFUSING: a proxy run receipt exists; never rerun")
    if git("status", "--porcelain"):
        raise SystemExit("REFUSING: repository is not clean")
    commit = git("rev-parse", "HEAD")
    if commit != git("rev-parse", "origin/main"):
        raise SystemExit("REFUSING: source commit is not public")
    devices = gpu_preflight()
    panel, qualification = qualified_panel(2026082517)
    index = json.loads((ROOT / "index.json").read_text())
    specs = {}
    for name in ("careful", "bare", "obs"):
        _items, spec = load_packet(name, index["panel_packets"][name], commit)
        spec["panel"] = panel
        specs[name] = spec
    client = ainglish_client()
    suggestions = client.suggestions()
    proposal = client.proposal(SLUG, authenticated=True)
    if proposal.get("stage") != "measured" or proposal.get("superseded_by"):
        raise SystemExit("REFUSING: proxy lifecycle is not the current measured surface")
    if any(row.get("metric") == "comprehension_accuracy_delta" and not row.get("is_replication") for row in proposal.get("measurements", [])):
        raise SystemExit("REFUSING: a proxy comprehension original already exists")
    planned = panel_harness._planned_panel_manifest(specs["careful"])
    opened = client.mint_attempt(
        SLUG, planned,
        estimand="Primary: percentage-point exact joint-classification accuracy of proxy(<M>) minus its complete careful-English disclosure over 96 frozen scenarios and the qualified cross-vendor reader roster. Bare and obs comparisons are preregistered diagnostics, not substitute denominators.",
        admissibility_gates=[
            "fresh authenticated suggestions and a fresh current-proposal read precede mint",
            "the proposal has no prior comprehension_accuracy_delta original",
            f"careful packet {index['panel_packets']['careful']['items_sha256']}, bare packet {index['panel_packets']['bare']['items_sha256']}, and obs packet {index['panel_packets']['obs']['items_sha256']} are public before mint",
            "all 96 scientific scenarios ask both registered proxy questions with four balanced polarity frames",
            "at least two distinct reader lineages passed the frozen ordinary-English qualification holdout",
            "the complete careful-English arm remains the only confirmatory comparator",
            "all diagnostic, null, adverse, refusal, calibration, and transport outcomes are retained without retry",
        ],
        planned_sample={
            "primary_items": 96, "diagnostic_items_per_comparison": 96, "calibration_items_per_run": 8,
            "readers": len(panel), "reader_lineages": [row["lineage"] for row in qualification["fixed_roster"]],
            "primary_items_sha256": index["panel_packets"]["careful"]["items_sha256"],
            "bare_items_sha256": index["panel_packets"]["bare"]["items_sha256"],
            "obs_items_sha256": index["panel_packets"]["obs"]["items_sha256"],
        },
        proposal_revision=SLUG,
    )["attempt"]
    (ROOT / "attempt.json").write_text(json.dumps({
        "attempt": opened, "source_commit": commit, "suggestions_generated_at": suggestions.get("generated_at"),
        "gpu_preflight": devices, "planned_manifest": planned,
    }, indent=2) + "\n")
    try:
        for name in ("bare", "obs"):
            result = panel_harness.run_panel(specs[name], ask_fn=panel_harness.ask)
            (ROOT / f"{name}-result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
            if result is None or panel_harness._is_panel_refusal(result):
                client.abort_attempt(opened["attempt_id"], f"proxy {name} diagnostic refused", result or {"state": "no_measurement"}, failed_gate_kind="diagnostic_refusal")
                return
        primary = panel_harness.run_panel(specs["careful"], ask_fn=panel_harness.ask)
        (ROOT / "primary-result.json").write_text(json.dumps(primary, indent=2, ensure_ascii=False) + "\n")
        if primary is None or panel_harness._is_panel_refusal(primary):
            client.abort_attempt(opened["attempt_id"], "proxy primary carrier refused", primary or {"state": "no_measurement"}, failed_gate_kind="panel_refusal")
            return
        if manifest_commitment(primary["manifest"]) != manifest_commitment(planned):
            client.abort_attempt(opened["attempt_id"], "proxy primary manifest diverged from preregistration", {
                "planned": manifest_commitment(planned), "actual": manifest_commitment(primary["manifest"]),
            }, failed_gate_kind="preflight_mismatch")
            return
        primary["attempt_id"] = opened["attempt_id"]
        filed = client.measure(SLUG, primary)
        (ROOT / "measurement.json").write_text(json.dumps({"request": primary, "receipt": filed}, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps({
            "attempt_id": opened["attempt_id"], "primary_value": primary["value"],
            "primary_arms": primary["arms"],
            "bare_diagnostic": json.loads((ROOT / "bare-result.json").read_text())["value"],
            "obs_diagnostic": json.loads((ROOT / "obs-result.json").read_text())["value"],
        }, indent=2))
    finally:
        unload(panel)


if __name__ == "__main__":
    main()
