#!/usr/bin/env python3
"""Mint, run, and file the fresh paired proposal-by comprehension replication."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import urllib.parse

from ainglish import panel as panel_harness
from ainglish.client import manifest_commitment


ROOT = Path(__file__).resolve().parent
EVIDENCE_REPO = ROOT.parent
SCRIPTS = EVIDENCE_REPO.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402


SLUG = "proposal-by-p-decision-by-a-say-whether-an-option-is-offered"
TARGET = "312b0fb0a5ae0f7fe2693597d5391ea95458cd87648097307666dea0ceb2ac6a"
SEED = 2026082511
ITEMS = ROOT / "items.json"
RECEIPT = ROOT / "replication-receipt.json"
ABORT_RECEIPT = ROOT / "abort-receipt.json"
CELLS_RECEIPT = ROOT / "cells.json"
CALIBRATION_RECEIPT = ROOT / "calibration-cells.json"
READER = {
    "name": "qwen2.5-7b-instruct", "provider": "ollama",
    "model": "dexagon-qwen2.5-7b-literal-v3:ctx4k",
    "model_digest": "sha256:ba3f85f29dd86fdf52a87f20b1d30634c7fc1460341e1cd23a2463c2eaa5fd68",
    "precision": "q4_k_m", "api": "openai", "base_url": "http://127.0.0.1:11434/v1",
    "max_tokens": 32, "timeout_s": 120, "temperature": 0, "seed": SEED,
}


def git_output(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=EVIDENCE_REPO, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    ).stdout.strip()


def source_state() -> dict:
    if git_output("status", "--porcelain"):
        raise RuntimeError("evidence repository is not clean")
    commit = git_output("rev-parse", "HEAD")
    if commit != git_output("rev-parse", "origin/main"):
        raise RuntimeError("source commit is not published")
    return {"commit": commit, "items_url": f"https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{commit}/proposal-by-comprehension-replication-2026-08-25/items.json"}


def load_items() -> tuple[list[dict], str]:
    doc = json.loads(ITEMS.read_text(encoding="utf-8"))
    rows = doc["items"]
    digest = hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    if digest != doc.get("sha256") or len([row for row in rows if not row.get("calibration")]) != 48:
        raise RuntimeError("frozen item artifact is inconsistent")
    return rows, digest


def build_manifest(state: dict, items: list[dict], digest: str) -> dict:
    return {
        "construct": SLUG, "metric": "comprehension_accuracy_delta", "formula_version": 2,
        "seed": SEED, "models": ["qwen2.5-7b-instruct@q4_k_m"], "panel": [READER],
        "panel_neff": 1, "replicates_hash": TARGET,
        "items": items, "items_sha256": digest, "items_url": state["items_url"],
        "comparator": {"kind": "short-natural-proposal-v1", "description": "Natural short proposal wording, preserving Nuwa's proposal-short comparator."},
        "method": (
            "One Qwen2.5-7B Q4_K_M reader receives both arms of all 48 real items after both "
            "arms of eight calibration items. Exact opaque one-byte choice binding is used; arm "
            "accuracy is exact recovery of the three-part profile. The scalar is 100*(Ainglish-English). "
            "A paired 2,000-draw item bootstrap supplies the percentile interval."
        ),
        "instrument_difference": (
            "Nuwa used an exact copied-option parser at temperature 0.2 on llama.cpp; this run uses "
            "the current opaque-code binding at deterministic temperature 0 on a digest-pinned Ollama "
            "wrapper over the same Qwen2.5-7B Q4_K_M weight blob. The register refuses non-portable "
            "0.2 floats in canonical manifests, so the sampling difference is explicit."
        ),
        "source_commit": state["commit"],
    }


def fresh_preflight(client, manifest: dict) -> dict:
    suggestions = client.suggestions()
    proposal = client.proposal(SLUG, authenticated=True)
    target = client.measurement(TARGET)
    card = next((row for row in suggestions.get("suggestions", []) if row.get("slug") == SLUG and row.get("replicates_hash") == TARGET and row.get("executable_now")), None)
    if card is None or target.get("settlement_state") != "awaiting":
        raise RuntimeError("fresh queue no longer offers the awaiting target")
    target_items, _ = panel_harness.fetch_items(target["manifest"]["items_url"], target["manifest"]["items_sha256"])
    ours = {(row["english"], row["ainglish"]) for row in manifest["items"] if not row.get("calibration")}
    theirs = {(row["english"], row["ainglish"]) for row in target_items if not row.get("calibration")}
    if len(ours) != 48 or ours & theirs:
        raise RuntimeError("different-input gate failed")
    return {
        "suggestions_generated_at": suggestions.get("generated_at"), "proposal_stage": proposal.get("stage"),
        "target_state": target.get("settlement_state"), "fresh_complete_pairs": 48,
        "target_complete_pairs": len(theirs), "overlap": 0,
        "manifest_commitment": manifest_commitment(manifest),
    }


def paired_interval(cells: list[dict]) -> tuple[float, float]:
    by_item = {}
    for cell in cells:
        by_item.setdefault(cell["item_id"], {})[cell["arm"]] = int(cell["correct"])
    pairs = [row for row in by_item.values() if set(row) == {"english", "ainglish"}]
    rng = random.Random(SEED)
    values = []
    for _ in range(2000):
        sample = [rng.choice(pairs) for _ in pairs]
        values.append(100 * sum(row["ainglish"] - row["english"] for row in sample) / len(sample))
    values.sort()
    return values[int(0.025 * len(values))], values[int(0.975 * len(values))]


def run_cells(manifest: dict, items: list[dict], *, dry_run: bool) -> tuple[dict | None, list[dict], list[dict]]:
    endpoint = dict(READER)
    if dry_run:
        def ask(_ep, text, _question, options):
            return options[0] if "does not say whether" in text else "offered / no / no"
    else:
        prepared = {"panel": [endpoint]}
        panel_harness.prepare_reader_instruments(prepared)
        endpoint = prepared["panel"][0]
        ask = panel_harness.ask
    cal_cells = []
    real_cells = []
    for item in [row for row in items if row.get("calibration")]:
        for arm in ("english", "ainglish"):
            answer = ask(endpoint, item[arm], item["question"], item["options"])
            cal_cells.append({"item_id": item["id"], "arm": arm, "answer": str(answer), "correct": str(answer).casefold() == item["answer"].casefold()})
    cal_acc = {arm: sum(cell["correct"] for cell in cal_cells if cell["arm"] == arm) / 8 for arm in ("english", "ainglish")}
    calibration = {"planted_arm": "ainglish", "detectable": cal_acc["ainglish"], "other": cal_acc["english"], "gap": cal_acc["ainglish"] - cal_acc["english"], "min_gap": 0.5}
    calibration["passed"] = calibration["gap"] >= calibration["min_gap"]
    if not calibration["passed"]:
        return None, real_cells, cal_cells
    for item in [row for row in items if not row.get("calibration")]:
        for arm in ("english", "ainglish"):
            answer = ask(endpoint, item[arm], item["question"], item["options"])
            real_cells.append({"item_id": item["id"], "arm": arm, "answer": str(answer), "correct": str(answer).casefold() == item["answer"].casefold()})
    arms = {arm: sum(cell["correct"] for cell in real_cells if cell["arm"] == arm) / 48 for arm in ("english", "ainglish")}
    value = 100 * (arms["ainglish"] - arms["english"])
    lo, hi = paired_interval(real_cells)
    measurement = {
        "metric": "comprehension_accuracy_delta", "formula_version": 2,
        "value": value, "value_lo": lo, "value_hi": hi, "arms": arms,
        "panel_models": ["qwen2.5-7b-instruct@q4_k_m"], "panel_neff": 1,
        "per_member": [{"model": "qwen2.5-7b-instruct", "precision": "q4_k_m", "value": value}],
        "calibration": calibration, "manifest": manifest, "replicates_hash": TARGET,
    }
    return measurement, real_cells, cal_cells


def abort(client, attempt_id: str, kind: str, message: str, detail: dict) -> None:
    receipt = {"kind": "ainglish.panel.abort.v1", "at": datetime.now(timezone.utc).isoformat(), "attempt_id": attempt_id, "failed_gate_kind": kind, "failed_gate": message, "details": detail}
    encoded = json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    ABORT_RECEIPT.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    client.post(f"/api/v1/attempts/{urllib.parse.quote(attempt_id, safe='')}/abort", {"failed_gate_kind": kind, "failed_gate": message, "preflight_receipt": encoded, "preflight_receipt_hash": hashlib.sha256(encoded.encode()).hexdigest()})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--submit", action="store_true")
    args = parser.parse_args()
    if args.dry_run == args.submit:
        raise SystemExit("choose exactly one of --dry-run or --submit")
    items, digest = load_items()
    state = source_state() if args.submit else {"commit": "dry-run", "items_url": str(ITEMS)}
    manifest = build_manifest(state, items, digest)
    if args.dry_run:
        result, cells, calibration = run_cells(manifest, items, dry_run=True)
        print(json.dumps({"reader_calls": 0, "result": result, "real_cells": len(cells), "calibration_cells": len(calibration)}, indent=2))
        if result is None:
            raise SystemExit(1)
        return
    if any(path.exists() for path in (RECEIPT, ABORT_RECEIPT, CELLS_RECEIPT, CALIBRATION_RECEIPT)):
        raise SystemExit("REFUSING: local attempt artifacts already exist")
    client = ainglish_client()
    checked = fresh_preflight(client, manifest)
    opened = client.mint_attempt(
        SLUG, manifest=manifest,
        estimand="Paired comprehension_accuracy_delta for proposal-by versus natural short proposal wording: both arms of 48 wholly fresh items, one Qwen2.5-7B Q4_K_M reader, exact three-part profile.",
        admissibility_gates=[
            "fresh suggestions still offer Nuwa's awaiting original",
            "all 48 complete pairs are disjoint from the target artifact",
            "both arms of every calibration item run before all 96 real cells",
            "the planted calibration gap is at least 0.5",
            "the digest-pinned Qwen weight edition matches before reader spend",
            "all 48 paired units survive with one exact opaque-code choice per arm",
            "every finite agreement, disagreement, null or adverse result is filed",
        ],
        planned_sample={"metric": "comprehension_accuracy_delta", "items": 48, "arms": 2, "readers": 1, "real_calls": 96, "calibration_calls": 16, "replicates_hash": TARGET},
        proposal_revision=SLUG,
    )["attempt"]
    try:
        measurement, cells, calibration = run_cells(manifest, items, dry_run=False)
        CALIBRATION_RECEIPT.write_text(json.dumps(calibration, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if measurement is None:
            abort(client, opened["attempt_id"], "calibration", "planted calibration gap below 0.5", {"calibration_cells": str(CALIBRATION_RECEIPT)})
            print("ABORTED: calibration")
            return
        CELLS_RECEIPT.write_text(json.dumps(cells, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        measurement["attempt_id"] = opened["attempt_id"]
        filed = client.measure(SLUG, measurement)
    except Exception as exc:
        if client.attempt(opened["attempt_id"]).get("state") == "open":
            abort(client, opened["attempt_id"], "harness_error", "paired reader harness failed", {"exception": type(exc).__name__, "message": str(exc), "preflight": checked})
        raise
    receipt = {"kind": "ainglish.proposal-by.comprehension-replication.v1", "target": TARGET, "attempt": opened, "preflight": checked, "measurement": filed, "manifest_commitment": manifest_commitment(manifest)}
    RECEIPT.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
