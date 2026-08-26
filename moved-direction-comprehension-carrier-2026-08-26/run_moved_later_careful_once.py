#!/usr/bin/env python3
"""Replicate the moved-later careful-English original exactly once."""

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


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
PROJECT = REPO.parent
SLUG = "moved-earlier-moved-later-which-way-did-the-meeting-move-2"
TARGET = "3965fddd5d31ea9f9948a113dd549cd84bac61223b61941ec69bde0b0d326635"
CAMPAIGN = "moved-later-vs-careful"
ITEMS_FILE = "items-moved-later-vs-careful.json"
SEED = 2026082661
sys.path.insert(0, str(PROJECT / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    sealed = dict(value)
    expected = sealed.pop("content_sha256", None)
    if not expected or hashlib.sha256(canonical(sealed)).hexdigest() != expected:
        raise RuntimeError(f"digest drift: {path}")
    return value


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO, check=True, capture_output=True, text=True
    ).stdout.strip()


def git_blob(commit: str, relative: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{relative}"], cwd=REPO, check=True, capture_output=True
    ).stdout


def qualification(path_text: str, commit: str) -> tuple[dict, list[dict]]:
    path = (REPO / path_text).resolve()
    try:
        relative = str(path.relative_to(REPO))
    except ValueError as exc:
        raise RuntimeError("qualification path escapes evidence repository") from exc
    value = checked(path)
    raw = value.get("fixed_roster", [])
    if not value.get("roster_ready") or len({row.get("lineage") for row in raw}) < 2:
        raise RuntimeError("fewer than two qualified reader lineages")
    if any(not row.get("lineage") or not row.get("model") or not row.get("model_digest") for row in raw):
        raise RuntimeError("qualification roster misses lineage, model, or digest")
    git("ls-files", "--error-unmatch", relative)
    if git_blob(commit, relative) != path.read_bytes():
        raise RuntimeError("qualification bytes differ from the public source commit")
    panel = []
    for index, row in enumerate(raw):
        reader = {
            "name": (row.get("name") or row["lineage"]) + "-moved-later-careful",
            "provider": "ollama",
            "model": row["model"],
            "model_digest": "sha256:" + row["model_digest"].removeprefix("sha256:"),
            "api": "openai",
            "base_url": "http://127.0.0.1:11434/v1",
            "max_tokens": 32,
            "timeout_s": row.get("timeout_s", 600),
            "temperature": 0,
            "seed": SEED + index,
            "reasoning_effort": "none",
        }
        if row.get("precision"):
            reader["precision"] = row["precision"]
        panel.append(reader)
    return value, panel


def gpu_preflight() -> list[dict]:
    output = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=index,name,memory.total,memory.free,utilization.gpu",
            "--format=csv,noheader,nounits",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    rows = []
    for line in output.splitlines():
        index, name, total, free, utilization = [part.strip() for part in line.split(",", 4)]
        rows.append(
            {
                "index": int(index),
                "name": name,
                "total_mib": int(total),
                "free_mib": int(free),
                "utilization": int(utilization),
            }
        )
    if any(row["free_mib"] < row["total_mib"] - 512 or row["utilization"] > 5 for row in rows):
        raise RuntimeError("GPU gate failed: at least one device is in use")
    return rows


def unload(panel: list[dict]) -> None:
    for reader in panel:
        request = urllib.request.Request(
            "http://127.0.0.1:11434/api/generate",
            data=json.dumps(
                {"model": reader["model"], "prompt": "", "stream": False, "keep_alive": 0}
            ).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            urllib.request.urlopen(request, timeout=60).read()
        except Exception:
            pass


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--qualification",
        required=True,
        help="repo-relative immutable selected-result JSON with roster_ready=true",
    )
    args = parser.parse_args()
    summary_path = ROOT / "moved-later-careful-summary.json"
    if list(ROOT.glob("moved-later-careful.attempt-*")) or summary_path.exists():
        raise SystemExit("REFUSING: moved-later careful replication receipt exists; never rerun")
    if sdk_version != "0.2.39":
        raise SystemExit(f"REFUSING: SDK {sdk_version} != frozen 0.2.39")
    if git("status", "--porcelain"):
        raise SystemExit("REFUSING: evidence repository is not clean")
    commit = git("rev-parse", "HEAD")
    if commit != git("rev-parse", "origin/main"):
        raise SystemExit("REFUSING: source commit is not public")
    qualified, panel = qualification(args.qualification, commit)
    index = checked(ROOT / "index.json")
    campaign = index["campaigns"][CAMPAIGN]
    packet = json.loads((ROOT / ITEMS_FILE).read_text(encoding="utf-8"))
    items = packet["items"]
    digest = hashlib.sha256(canonical(items)).hexdigest()
    if digest != packet["items_sha256"] or digest != campaign["items_sha256"]:
        raise SystemExit("REFUSING: moved-later careful item digest drift")
    if len(items) != 128 or sum(not row.get("calibration") for row in items) != 120:
        raise SystemExit("REFUSING: moved-later careful population drift")
    if any(
        row.get("strata", {}).get("form") != "moved-later"
        or row.get("strata", {}).get("comparator") != "careful"
        for row in items
        if not row.get("calibration")
    ):
        raise SystemExit("REFUSING: form or comparator drift")
    devices = gpu_preflight()
    client = ainglish_client()
    suggestions = client.suggestions()
    proposal = client.proposal(SLUG, authenticated=True)
    if proposal.get("stage") != "measured" or proposal.get("superseded_by"):
        raise SystemExit("REFUSING: moved-direction proposal is not the current measured surface")
    target = client.measurement(TARGET)
    target_manifest = target.get("manifest") or {}
    if (
        target.get("metric") != "comprehension_accuracy_delta"
        or target_manifest.get("construct") != "moved-later"
        or (target_manifest.get("comparator") or {}).get("kind") != "complete-careful-english-v1"
        or target.get("settlement_state") != "awaiting"
    ):
        raise SystemExit("REFUSING: target identity or settlement state drift")
    work = next(
        (
            row
            for row in (proposal.get("evidence_readiness") or {}).get("work_items", [])
            if row.get("metric") == "comprehension_accuracy_delta"
            and TARGET in row.get("target_hashes", [])
        ),
        None,
    )
    if not work or work.get("state") != "replicate_original":
        raise SystemExit("REFUSING: live contract no longer requests this replication")
    fidelity = [row for row in proposal.get("measurements", []) if row.get("metric") == "tag_fidelity"]
    if not any(not row.get("is_replication") and row.get("value", 0) >= 0.5 for row in fidelity):
        raise SystemExit("REFUSING: moved-direction tag_fidelity original is absent or below 0.5")
    spec = {
        "construct": "moved-later",
        "slug": SLUG,
        "metric": "comprehension_accuracy_delta",
        "formula_version": 2,
        "replicates_hash": TARGET,
        "seed": SEED,
        "planted_arm": "ainglish",
        "calibration_min_gap": 0.5,
        "panel": panel,
        "comparator": {
            "kind": "complete-careful-english-v1",
            "description": "moved-later versus a complete force-matched careful-English mapping",
        },
        "items_url": (
            "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
            f"{commit}/moved-direction-comprehension-carrier-2026-08-26/{ITEMS_FILE}"
        ),
        "items_sha256": digest,
        "items": items,
        "qualification": {
            "content_sha256": qualified["content_sha256"],
            "lineages": [row["lineage"] for row in qualified["fixed_roster"]],
        },
        "attempt": {
            "proposal_revision": SLUG,
            "estimand": (
                "Percentage-point exact consequence-accuracy difference, moved-later minus its "
                "complete careful-English mapping, over 120 fresh items. This form and comparator "
                "are a separate estimand and are never pooled with moved-earlier or bare wording."
            ),
            "admissibility_gates": [
                "fresh authenticated suggestions and current proposal read precede mint",
                "the 3965fddd moved-later careful original remains awaiting a disjoint replication",
                "a controlled moved-direction tag_fidelity original at or above 0.5 exists",
                f"the public 120+8 packet has canonical item digest {digest}",
                "all real rows are moved-later with the complete careful-English comparator",
                "at least two distinct lineages passed the immutable ordinary-English holdout",
                "construct-free calibration runs first and every finite or refused result is retained",
            ],
            "planned_sample": {
                "scientific_items": 120,
                "calibration_items": 8,
                "form": "moved-later",
                "comparator": "careful",
                "readers": len(panel),
                "reader_lineages": [row["lineage"] for row in qualified["fixed_roster"]],
                "qualification_sha256": qualified["content_sha256"],
                "qualification_path": args.qualification,
                "items_sha256": digest,
                "suggestions_generated_at": suggestions.get("generated_at"),
                "gpu_preflight": devices,
            },
        },
    }
    try:
        result = panel_harness._run_preregistered_panel(
            spec,
            spec,
            panel_harness.ask,
            client,
            receipt_dir=str(ROOT),
            receipt_stem="moved-later-careful",
        )
        summary_path.write_text(
            json.dumps(
                {"state": "filed" if result else "aborted_or_refused", "response": result},
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        print(json.dumps({"state": "filed" if result else "aborted_or_refused"}, indent=2))
    finally:
        unload(panel)


if __name__ == "__main__":
    main()
