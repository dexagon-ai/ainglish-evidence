#!/usr/bin/env python3
"""Mint, run, and file the fresh Nuwa proposal-by comprehension replication once."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import sys

from ainglish import __version__ as sdk_version
from ainglish import panel


ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT.parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402


SLUG = "proposal-by-p-decision-by-a-say-whether-an-option-is-offered"
REPLICATES_HASH = "312b0fb0a5ae0f7fe2693597d5391ea95458cd87648097307666dea0ceb2ac6a"
READER = {
    "name": "Dexagon-local-Qwen2.5-7B-Q4_K_M",
    "provider": "ollama",
    "model": "qwen2.5:7b",
    "precision": "q4_k_m",
    "api": "openai",
    "base_url": "http://127.0.0.1:11434/v1",
    "max_tokens": 128,
    "timeout_s": 120,
    "temperature": 0,
    "seed": 2026082361,
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def load_packet() -> tuple[dict, list[dict], list[dict]]:
    doc = json.loads((ROOT / "items.json").read_text(encoding="utf-8"))
    receipt = json.loads((ROOT / "freeze-receipt.json").read_text(encoding="utf-8"))
    if hashlib.sha256(canonical(doc["items"])).hexdigest() != doc["sha256"]:
        raise SystemExit("REFUSING: item-array digest mismatch")
    if doc["sha256"] != receipt["items_sha256"] or receipt["reader_calls"] != 0:
        raise SystemExit("REFUSING: freeze receipt mismatch or prior reader spend")
    calibration = [row for row in doc["items"] if row.get("calibration")]
    real = [row for row in doc["items"] if not row.get("calibration")]
    if len(calibration) != 6 or len(real) != 48:
        raise SystemExit("REFUSING: packet cardinality drift")
    return doc, calibration, real


def bootstrap(differences: list[int], seed: int, draws: int = 5000) -> tuple[float, float]:
    rng = random.Random(seed)
    values = []
    for _ in range(draws):
        sample = [differences[rng.randrange(len(differences))] for _ in differences]
        values.append(100 * sum(sample) / len(sample))
    values.sort()
    return values[int(0.025 * draws)], values[min(draws - 1, int(0.975 * draws))]


def make_manifest(doc: dict, freeze_commit: str, prepared_reader: dict) -> dict:
    url = (
        "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
        f"{freeze_commit}/proposal-decision-nuwa-replication-2026-08-23/items.json"
    )
    label = prepared_reader["name"] + "@" + prepared_reader["precision"]
    return {
        "construct": "proposal-by(<P>) fresh replication of Nuwa's proposal-form short comparator",
        "metric": "comprehension_accuracy_delta",
        "seed": doc["seed"],
        "items_url": url,
        "items_sha256": doc["sha256"],
        "models": [label],
        "readers": [panel.reader_receipt(prepared_reader)],
        "answer_protocol": panel.ANSWER_PROTOCOL,
        "transport": {label: panel.transport_settings(prepared_reader)},
        "harness": f"ainglish-panel/{sdk_version} paired-both-arms replication wrapper",
        "protocol": (
            "The one Qwen2.5-7B Q4_K_M reader answers both surfaces of every frozen scenario, "
            "matching the replicated original's paired 48-item estimator. Opaque-choice-v1 maps "
            "one-byte responses back to the complete declared profile. Calibration runs first; "
            "any absent, truncated, faulted, or off-option cell aborts rather than changing a denominator."
        ),
        "comparison": "proposal-by marker versus a short natural proposal surface",
        "item_counts": {"real": 48, "calibration": 6},
        "input_authorship": {
            "author": "Dexagon",
            "relationship": "proposal author and replication operator; distinct from original measurer Nuwa",
            "freshness": "all complete pairs are new and exact-overlap checked against the original published file",
        },
        "supersession": {
            "attempt_id": doc.get("supersedes_attempt"),
            "reason": doc.get("supersession_reason"),
            "prior_calibration_calls": doc.get("prior_calibration_calls_on_superseded_packet"),
            "prior_real_calls": 0,
        },
    }


def score_rows(rows: list[dict], items: list[dict]) -> tuple[dict, list[int]]:
    by_id = {row["id"]: row for row in items}
    accuracy = {}
    for arm in ("english", "ainglish"):
        cells = [row for row in rows if row["arm"] == arm]
        accuracy[arm] = sum(row["correct"] for row in cells) / len(cells)
    differences = []
    for item_id in by_id:
        pair = {row["arm"]: row for row in rows if row["item_id"] == item_id}
        differences.append(int(pair["ainglish"]["correct"]) - int(pair["english"]["correct"]))
    return accuracy, differences


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze-commit", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--successor-of")
    args = parser.parse_args()
    if sdk_version != "0.2.34":
        raise SystemExit(f"REFUSING: SDK {sdk_version} != frozen 0.2.34")
    if len(args.freeze_commit) != 40 or any(c not in "0123456789abcdef" for c in args.freeze_commit):
        raise SystemExit("--freeze-commit must be lowercase 40-hex")
    doc, calibration, real = load_packet()
    if args.dry_run:
        print(json.dumps({
            "reader_calls": 0,
            "items_sha256": doc["sha256"],
            "real_items": len(real),
            "calibration_items": len(calibration),
            "answer_protocol": panel.ANSWER_PROTOCOL,
        }, indent=2))
        return

    prior_attempts = list(ROOT.glob("attempt-*.json"))
    if prior_attempts:
        if args.successor_of != doc.get("supersedes_attempt"):
            raise SystemExit(
                "REFUSING: prior attempt exists and --successor-of does not match the frozen supersession receipt"
            )
        if not (ROOT / f"attempt-{args.successor_of}.abort.json").exists():
            raise SystemExit("REFUSING: frozen predecessor has no local abort receipt")
        if list(ROOT.glob("attempt-*.measurement-response.json")):
            raise SystemExit("REFUSING: a completed measurement response already exists")
    client = ainglish_client()
    proposal = client.proposal(SLUG, authenticated=True)
    if proposal.get("stage") != "measured":
        raise SystemExit(f"REFUSING: live stage is {proposal.get('stage')!r}")
    original = client.measurement(REPLICATES_HASH)
    if original.get("evidence_state") != "valid" or original.get("metric") != "comprehension_accuracy_delta":
        raise SystemExit("REFUSING: replicated original is no longer valid/comparable")
    prior_digests = {
        (row.get("manifest") or {}).get("items_sha256") for row in proposal.get("measurements", [])
    }
    if doc["sha256"] in prior_digests:
        raise SystemExit("REFUSING: packet digest already appears on the proposal")

    prepared = dict(READER)
    panel.prepare_reader_instruments({"panel": [prepared]})
    manifest = make_manifest(doc, args.freeze_commit, prepared)
    estimand = (
        "Percentage-point exact three-part-profile accuracy difference, proposal-by marked surface "
        "minus short natural proposal English, over 48 wholly fresh scenarios. The same one "
        "Qwen2.5-7B Q4_K_M reader answers both surfaces of every scenario, preserving Nuwa's "
        "paired estimator; each scenario is one bootstrap unit."
    )
    gates = [
        f"the canonical 54-row item array remains {doc['sha256']}",
        "all 48 real complete pairs are absent from Nuwa's published original input file",
        "the live proposal remains measured and the referenced original remains valid comprehension evidence",
        "the prepared reader is exactly Qwen2.5 7B at Q4_K_M and its live Ollama digest is retained in the manifest",
        "all six calibration rows are answered in both arms before any real cell and marked-minus-English accuracy is at least 0.5",
        "every real item is answered in both arms; any absence, truncation, transport fault, or off-option response aborts with no retry",
        "the exact 48 paired item differences determine the scalar and bootstrap interval; every finite direction files",
    ]
    planned = {
        "metric": "comprehension_accuracy_delta",
        "real_items": 48,
        "calibration_items": 6,
        "arms_per_real_item": 2,
        "readers": 1,
        "reader_family": "Qwen2.5 7B",
        "precision": "Q4_K_M",
        "panel_neff": 1,
        "real_calls": 96,
        "calibration_calls": 12,
        "bootstrap_units": 48,
        "seed": doc["seed"],
    }
    minted = client.mint_attempt(SLUG, manifest, estimand, gates, planned)
    attempt = minted.get("attempt", minted)
    attempt_id = attempt["attempt_id"]
    (ROOT / f"attempt-{attempt_id}.json").write_text(
        json.dumps(attempt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    cells = []
    try:
        for stage, items in (("calibration", calibration), ("real", real)):
            for item in items:
                for arm in ("english", "ainglish"):
                    answer = panel.ask(prepared, item[arm], item["question"], item["options"])
                    if panel.is_absent(answer) or str(answer) not in item["options"]:
                        reason = getattr(answer, "reason", "off_option")
                        raise RuntimeError(f"{stage} cell {item['id']} {arm} failed: {reason}")
                    cells.append({
                        "kind": "ainglish.panel.cell-result.v1",
                        "stage": stage,
                        "item_id": item["id"],
                        "arm": arm,
                        "reader": prepared["name"],
                        "answer": str(answer),
                        "expected": item["answer"],
                        "correct": str(answer).casefold() == item["answer"].casefold(),
                        "strata": item.get("strata", {}),
                    })
            if stage == "calibration":
                cacc, _ = score_rows(cells, calibration)
                if cacc["ainglish"] - cacc["english"] < 0.5:
                    raise RuntimeError(
                        f"calibration gap {cacc['ainglish'] - cacc['english']:.4f} is below 0.5"
                    )
    except Exception as exc:
        receipt = {
            "kind": "ainglish.panel.abort.v1",
            "attempt_id": attempt_id,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "cells_completed": len(cells),
            "retried": False,
        }
        client.abort_attempt(
            attempt_id,
            "paired reader or calibration gate failed",
            receipt,
            failed_gate_kind="harness_refuse",
        )
        (ROOT / f"attempt-{attempt_id}.abort.json").write_text(
            json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
        )
        raise

    real_cells = [row for row in cells if row["stage"] == "real"]
    calibration_cells = [row for row in cells if row["stage"] == "calibration"]
    acc, differences = score_rows(real_cells, real)
    cacc, _ = score_rows(calibration_cells, calibration)
    value = round(100 * (acc["ainglish"] - acc["english"]), 2)
    lo, hi = bootstrap(differences, doc["seed"])
    lo, hi = round(min(lo, value), 4), round(max(hi, value), 4)

    rng = random.Random(str(doc["seed"]) + ":resample")
    sensitivity = []
    for fraction in (0.75, 0.5):
        keep = int(len(differences) * fraction)
        indices = rng.sample(range(len(differences)), keep)
        subset = round(100 * sum(differences[i] for i in indices) / keep, 2)
        sensitivity.append({
            "kept_fraction": fraction,
            "items": keep,
            "value": subset,
            "sign_flipped": value != 0 and (subset > 0) != (value > 0),
            "outside_interval": subset < lo or subset > hi,
        })

    label = prepared["name"] + "@" + prepared["precision"]
    resolution = {
        "unit": "percentage_points",
        "scored_cells": {"english": 48, "ainglish": 48},
        "one_cell_pp": {"english": "2.0833", "ainglish": "2.0833"},
        "delta_grid": {"numerator_pp": 100, "denominator_lcm": 48, "step_pp": "2.0833"},
    }
    payload = {
        "metric": "comprehension_accuracy_delta",
        "value": value,
        "value_lo": lo,
        "value_hi": hi,
        "arms": {"english": round(acc["english"], 4), "ainglish": round(acc["ainglish"], 4), "chance": 0.2},
        "panel_models": [label],
        "panel_members": 1,
        "panel_neff": 1,
        "panel_neff_basis": "declared:reader-axis-unvalidated",
        "per_member": [{"model": prepared["name"], "precision": prepared["precision"], "value": value}],
        "resample_down": sensitivity,
        "calibration": {
            "planted_arm": "ainglish",
            "detectable": round(cacc["ainglish"], 4),
            "other": round(cacc["english"], 4),
            "gap": round(cacc["ainglish"] - cacc["english"], 4),
            "min_gap": 0.5,
            "passed": True,
        },
        "yield_report": {
            "cells": 96,
            "empty": 0,
            "unparsed": 0,
            "dead_rate": 0,
            "per_cell": {
                f"{prepared['name']}/english": {"n": 48, "empty": 0, "unparsed": 0},
                f"{prepared['name']}/ainglish": {"n": 48, "empty": 0, "unparsed": 0},
            },
        },
        "accuracy_resolution": resolution,
        "is_adversarial": False,
        "manifest": manifest,
        "replicates_hash": REPLICATES_HASH,
        "attempt_id": attempt_id,
    }
    (ROOT / f"attempt-{attempt_id}.cells.json").write_text(
        json.dumps(cells, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (ROOT / f"attempt-{attempt_id}.measurement-request.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    result = client.measure(SLUG, payload)
    (ROOT / f"attempt-{attempt_id}.measurement-response.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "attempt_id": attempt_id,
        "value": value,
        "value_lo": lo,
        "value_hi": hi,
        "arms": payload["arms"],
        "calibration": payload["calibration"],
        "measurement": result,
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
