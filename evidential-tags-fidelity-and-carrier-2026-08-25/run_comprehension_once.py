#!/usr/bin/env python3
"""Run the evidential-tags comprehension carrier only after confirmed prerequisites."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import urllib.request

from ainglish import __version__ as sdk_version
from ainglish import panel as panel_harness


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
PROJECT = REPO.parent
QUALIFICATION = REPO / "reader-qualification-v5-2026-08-25" / "result.json"
SLUG = "evidential-tags-obs-inf-rep-src-with-instrument-recall-and-p-2"
sys.path.insert(0, str(PROJECT / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()


def unload(panel: list[dict]) -> None:
    for reader in panel:
        data = json.dumps({"model": reader["model"], "prompt": "", "stream": False, "keep_alive": 0}).encode()
        request = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(request, timeout=60).read()


def main() -> None:
    if sdk_version != "0.2.35":
        raise SystemExit(f"REFUSING: SDK {sdk_version} != frozen 0.2.35")
    if list(ROOT.glob("comprehension.attempt-*")) or (ROOT / "comprehension-summary.json").exists():
        raise SystemExit("REFUSING: comprehension receipt exists; never rerun")
    if git("status", "--porcelain"):
        raise SystemExit("REFUSING: repository is not clean")
    commit = git("rev-parse", "HEAD")
    if commit != git("rev-parse", "origin/main"):
        raise SystemExit("REFUSING: source commit is not public")
    qualification = json.loads(QUALIFICATION.read_text())
    fixed = qualification.get("fixed_roster", [])
    if not qualification.get("roster_ready") or len({row["lineage"] for row in fixed}) < 2:
        raise SystemExit("REFUSING: fewer than two qualified reader lineages")
    panel = [{
        "name": row["name"] + "-evidential-comprehension", "provider": "ollama", "model": row["model"],
        "model_digest": row["model_digest"], "precision": row["precision"],
        "api": "openai", "base_url": "http://127.0.0.1:11434/v1", "max_tokens": 32,
        "timeout_s": row["timeout_s"], "temperature": 0, "seed": 2026082519,
    } for row in fixed]
    client = ainglish_client()
    suggestions = client.suggestions()
    proposal = client.proposal(SLUG, authenticated=True)
    measurements = proposal.get("measurements", [])
    fidelity = [row for row in measurements if row.get("metric") == "tag_fidelity"]
    if not any(row.get("confirmed") and row.get("value", 0) >= 0.5 for row in fidelity):
        raise SystemExit("REFUSING: tag_fidelity is not independently confirmed at or above 0.5")
    token = [row for row in measurements if row.get("metric") == "token_delta"]
    if not any(row.get("confirmed") and row.get("value", 0) < 0 for row in token):
        raise SystemExit("REFUSING: the negative token prerequisite is not confirmed")
    if any(row.get("metric") == "comprehension_accuracy_delta" and not row.get("is_replication") for row in measurements):
        raise SystemExit("REFUSING: a comprehension original already exists")
    payload = json.loads((ROOT / "comprehension-panel.json").read_text())
    items = payload["items"]
    digest = hashlib.sha256(canonical(items)).hexdigest()
    if digest != payload["sha256"]:
        raise SystemExit("REFUSING: comprehension packet drift")
    spec = {
        "construct": "evidential-tags source-class comprehension original",
        "slug": SLUG, "metric": "comprehension_accuracy_delta", "seed": 2026082519,
        "planted_arm": "ainglish", "calibration_min_gap": 0.5,
        "panel_neff": len(panel), "panel": panel,
        "comparator": {
            "kind": "complete-honest-evidential-english-v1",
            "description": "Each compact evidential prefix is compared with a complete honest-English statement of the same evidence source.",
        },
        "items_url": f"https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{commit}/evidential-tags-fidelity-and-carrier-2026-08-25/comprehension-panel.json",
        "items_sha256": digest, "items": items,
        "attempt": {
            "proposal_revision": SLUG,
            "estimand": "Percentage-point difference in exact held-out evidence-source recovery, evidential tag minus its complete honest-English provenance clause, over 120 balanced frozen pairs and the qualified cross-vendor reader roster.",
            "admissibility_gates": [
                "fresh authenticated suggestions and current proposal are read immediately before mint",
                "tag_fidelity is independently confirmed at or above 0.5",
                "the negative token prerequisite remains independently confirmed",
                f"the public 120+8 packet has canonical items digest {digest}",
                "all six declared tag forms contribute exactly twenty scientific items",
                "at least two distinct reader lineages passed the frozen ordinary-English qualification holdout",
                "construct-free calibration runs first and every finite or refused outcome is retained without retry",
            ],
            "planned_sample": {
                "scientific_items": 120, "calibration_items": 8, "forms": 6,
                "readers": len(panel), "reader_lineages": [row["lineage"] for row in fixed],
                "items_sha256": digest, "suggestions_generated_at": suggestions.get("generated_at"),
            },
        },
    }
    try:
        result = panel_harness._run_preregistered_panel(
            spec, spec, panel_harness.ask, client, receipt_dir=str(ROOT), receipt_stem="comprehension",
        )
        (ROOT / "comprehension-summary.json").write_text(json.dumps({
            "state": "filed" if result else "aborted_or_refused", "response": result,
        }, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps({"state": "filed" if result else "aborted_or_refused", "response": result}, indent=2))
    finally:
        unload(panel)


if __name__ == "__main__":
    main()
