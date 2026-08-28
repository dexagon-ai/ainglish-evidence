#!/usr/bin/env python3
"""Apply the frozen benchmark scorer and paired exposure contrasts."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
BENCHMARK_ROOT = REPO / "end-to-end-agent-task-benchmark-v0.1-2026-08-28"
CELLS_PATH = ROOT / "cells.jsonl"
PLAN_PATH = ROOT / "RUN_PLAN.json"


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def load_benchmark():
    path = BENCHMARK_ROOT / "benchmark.py"
    spec = importlib.util.spec_from_file_location("ainglish_agent_task_benchmark", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def rate(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    successes = sum(bool(row[field]) for row in rows)
    return {"successes": successes, "total": len(rows), "rate": round(successes / len(rows), 6) if rows else None}


def numeric(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    values = [float(row[field]) for row in rows if row[field] is not None]
    return {
        "coverage": len(values),
        "denominator": len(rows),
        "mean": round(statistics.fmean(values), 4) if values else None,
        "median": round(statistics.median(values), 4) if values else None,
    }


def group_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "n": len(rows),
        "zero_repair_success": rate(rows, "zero_repair_success"),
        "final_success": rate(rows, "final_success"),
        "clarification": rate(rows, "clarified"),
        "wrong_action": rate(rows, "wrong_action"),
        "invalid_output": rate(rows, "invalid_output"),
        "repair_missing": rate(rows, "repair_missing"),
        "total_tokens": numeric(rows, "total_tokens"),
        "latency_ms": numeric(rows, "latency_ms"),
    }


def paired(left: list[dict[str, Any]], right: list[dict[str, Any]], field: str, keys: tuple[str, ...]) -> dict[str, Any]:
    left_map = {tuple(row[key] for key in keys): row for row in left}
    right_map = {tuple(row[key] for key in keys): row for row in right}
    if left_map.keys() != right_map.keys():
        raise RuntimeError(f"paired populations differ for {field}")
    pairs = [(left_map[key], right_map[key]) for key in sorted(left_map)]
    left_only = sum(bool(a[field]) and not bool(b[field]) for a, b in pairs)
    right_only = sum(bool(b[field]) and not bool(a[field]) for a, b in pairs)
    both = sum(bool(a[field]) and bool(b[field]) for a, b in pairs)
    neither = len(pairs) - left_only - right_only - both
    return {
        "field": field,
        "pairs": len(pairs),
        "left_only_successes": left_only,
        "right_only_successes": right_only,
        "both_success": both,
        "neither_success": neither,
        "mean_difference_left_minus_right": round((left_only - right_only) / len(pairs), 6) if pairs else None,
    }


def paired_token_delta(left: list[dict[str, Any]], right: list[dict[str, Any]], outcome: str, keys: tuple[str, ...]) -> dict[str, Any]:
    left_map = {tuple(row[key] for key in keys): row for row in left}
    right_map = {tuple(row[key] for key in keys): row for row in right}
    deltas = []
    for key in sorted(left_map.keys() & right_map.keys()):
        a, b = left_map[key], right_map[key]
        if bool(a[outcome]) == bool(b[outcome]) and a["total_tokens"] is not None and b["total_tokens"] is not None:
            deltas.append(float(a["total_tokens"]) - float(b["total_tokens"]))
    return {
        "eligibility": f"both conditions have the same {outcome} outcome and complete token counts",
        "pairs": len(deltas),
        "mean_left_minus_right": round(statistics.fmean(deltas), 4) if deltas else None,
        "median_left_minus_right": round(statistics.median(deltas), 4) if deltas else None,
    }


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: analyse.py results/responses.jsonl")
    result_path = Path(sys.argv[1])
    raw = load_jsonl(result_path)
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    if len(raw) != plan["planned_observations"]:
        raise SystemExit(f"REFUSING: expected {plan['planned_observations']} rows, got {len(raw)}")
    keys = [(row["condition"], row["cell_id"]) for row in raw]
    if len(keys) != len(set(keys)):
        raise SystemExit("REFUSING: duplicate condition/cell")

    benchmark = load_benchmark()
    packet = benchmark.load_tasks()
    classified = benchmark.classify_rows(packet, [dict(row) for row in raw])
    metadata = {(row["reader_id"], row["item_id"], row["arm"], row["track"]): row for row in raw}
    for row in classified:
        source = metadata[(row["reader_id"], row["item_id"], row["arm"], row["track"])]
        row["condition"] = source["condition"]
        row["exposure_class"] = source["exposure_class"]
        row["cell_id"] = source["cell_id"]

    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in classified:
        grouped[(row["condition"], row["track"], row["arm"], row["exposure_class"])].append(row)
    summaries = [
        {"condition": condition, "track": track, "arm": arm, "exposure_class": exposure, **group_summary(rows)}
        for (condition, track, arm, exposure), rows in sorted(grouped.items())
    ]

    training_contrasts = []
    pair_keys = ("item_id", "arm", "track")
    for track in benchmark.TRACKS:
        for exposure in ("trained_surface", "withheld_surface"):
            for arm in benchmark.ARMS:
                base = [r for r in classified if r["condition"] == "base" and r["track"] == track and r["arm"] == arm and r["exposure_class"] == exposure]
                adapter = [r for r in classified if r["condition"] == "adapter" and r["track"] == track and r["arm"] == arm and r["exposure_class"] == exposure]
                training_contrasts.append({
                    "left": "adapter", "right": "base", "track": track, "arm": arm, "exposure_class": exposure,
                    "zero_repair": paired(adapter, base, "zero_repair_success", pair_keys),
                    "final": paired(adapter, base, "final_success", pair_keys),
                    "tokens_same_zero_repair_outcome": paired_token_delta(adapter, base, "zero_repair_success", pair_keys),
                    "tokens_same_final_outcome": paired_token_delta(adapter, base, "final_success", pair_keys),
                })

    surface_contrasts = []
    surface_keys = ("item_id", "track", "condition")
    for condition in ("base", "adapter"):
        for track in benchmark.TRACKS:
            for exposure in ("trained_surface", "withheld_surface"):
                ainglish = [r for r in classified if r["condition"] == condition and r["track"] == track and r["arm"] == "ainglish" and r["exposure_class"] == exposure]
                careful = [r for r in classified if r["condition"] == condition and r["track"] == track and r["arm"] == "careful" and r["exposure_class"] == exposure]
                # Add constant labels so the declared key tuple can verify the aligned populations.
                for row in ainglish + careful:
                    row["condition"] = condition
                surface_contrasts.append({
                    "left": "ainglish", "right": "careful", "condition": condition, "track": track, "exposure_class": exposure,
                    "zero_repair": paired(ainglish, careful, "zero_repair_success", surface_keys),
                    "final": paired(ainglish, careful, "final_success", surface_keys),
                    "tokens_same_zero_repair_outcome": paired_token_delta(ainglish, careful, "zero_repair_success", surface_keys),
                    "tokens_same_final_outcome": paired_token_delta(ainglish, careful, "final_success", surface_keys),
                })

    output = {
        "schema": "ainglish.controlled-training-exposure-analysis.v1",
        "plan_sha256": hashlib.sha256(PLAN_PATH.read_bytes()).hexdigest(),
        "responses_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
        "observations": len(classified),
        "summaries": summaries,
        "adapter_minus_base": training_contrasts,
        "ainglish_minus_careful": surface_contrasts,
        "claim_limits": [
            "The intervention is one project-trained adapter on one pinned base model; this is not a model-family result.",
            "Withheld-surface means exact registered markers were absent from development adapter training, not that related concepts were absent from base pretraining.",
            "Cold means no definition in this prompt, not proof of no prior Ainglish exposure.",
            "Token deltas do not establish efficiency unless correctness remains acceptable and do not predict future-tokenizer behaviour.",
            "The adapter, task designer, and operator are project-linked; this is not independent governance evidence.",
        ],
        "governance_evidence": False,
        "model_downloads": 0,
    }
    output["content_sha256"] = hashlib.sha256(canonical(output)).hexdigest()
    target = ROOT / "analysis.json"
    if target.exists():
        raise SystemExit("REFUSING: analysis.json already exists")
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "ok": True,
        "observations": len(classified),
        "content_sha256": output["content_sha256"],
        "primary": [row for row in training_contrasts if row["arm"] == "ainglish"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
