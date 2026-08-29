#!/usr/bin/env python3
"""Expand the frozen atlas, apply prospective classifications, and render results."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
CONDITIONS = ["ainglish_cold", "ainglish_defined", "careful_english", "bare_english", "corrupted_ainglish"]


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def stat(rows: list[dict[str, Any]]) -> dict[str, Any]:
    correct = sum(row["correct"] for row in rows)
    invalid = sum(row["invalid_batch"] for row in rows)
    return {"correct": correct, "total": len(rows), "accuracy": round(correct / len(rows), 6) if rows else None, "invalid_batch_cells": invalid}


def classify(condition_stats: dict[str, dict[str, Any]], cold_by_reader: dict[str, float]) -> tuple[str, list[str], dict[str, float]]:
    acc = {condition: condition_stats[condition]["accuracy"] for condition in CONDITIONS}
    contrasts = {
        "cold_minus_careful": round(acc["ainglish_cold"] - acc["careful_english"], 6),
        "defined_minus_cold": round(acc["ainglish_defined"] - acc["ainglish_cold"], 6),
        "corrupted_minus_cold": round(acc["corrupted_ainglish"] - acc["ainglish_cold"], 6),
    }
    invalid = sum(condition_stats[condition]["invalid_batch_cells"] for condition in CONDITIONS)
    reader_values = list(cold_by_reader.values())
    flags = []
    if contrasts["cold_minus_careful"] < -0.10:
        flags.append("cold_careful_gap")
    if contrasts["defined_minus_cold"] >= 0.10:
        flags.append("definition_gain")
    if contrasts["corrupted_minus_cold"] <= -0.15:
        flags.append("corruption_drop")
    if acc["bare_english"] < 0.75:
        flags.append("bare_ambiguity_failure")
    if reader_values and max(reader_values) - min(reader_values) >= 0.375:
        flags.append("reader_heterogeneity")
    if invalid:
        flags.append("invalid_channel")

    below_half = sum(value < 0.50 for value in reader_values)
    if acc["ainglish_defined"] < 0.75 or acc["careful_english"] < 0.80 or acc["ainglish_cold"] < 0.60:
        primary = "amendment_candidate"
    elif acc["ainglish_cold"] >= 0.80 and acc["careful_english"] >= 0.85 and acc["ainglish_defined"] >= 0.85 and acc["corrupted_ainglish"] >= 0.75 and contrasts["cold_minus_careful"] >= -0.10:
        primary = "strong"
    elif contrasts["corrupted_minus_cold"] <= -0.15 or below_half >= 2:
        primary = "fragile"
    elif acc["ainglish_defined"] >= 0.80 and contrasts["defined_minus_cold"] >= 0.10:
        primary = "learnable"
    else:
        primary = "amendment_candidate"
    return primary, flags, contrasts


def pct(value: float | None) -> str:
    return "n/a" if value is None else f"{100 * value:.1f}%"


def main() -> None:
    target = ROOT / "analysis.json"
    report_path = ROOT / "RESULT.md"
    if target.exists() or report_path.exists():
        raise SystemExit("REFUSING: analysis output already exists")
    plan = json.loads((ROOT / "RUN_PLAN.json").read_text(encoding="utf-8"))
    items = json.loads((ROOT / "items.json").read_text(encoding="utf-8"))["items"]
    constructs = json.loads((ROOT / "constructs.json").read_text(encoding="utf-8"))["constructs"]
    calls = []
    response_files = sorted(RESULTS.glob("reader-*.jsonl"))
    for path in response_files:
        calls.extend(jsonl(path))
    if len(calls) != plan["planned_calls"]:
        raise SystemExit(f"REFUSING: expected {plan['planned_calls']} calls, got {len(calls)}")
    call_keys = [(row["reader_id"], row["key"], row["condition"]) for row in calls]
    if len(call_keys) != len(set(call_keys)):
        raise SystemExit("REFUSING: duplicate reader/construct/condition call")
    items_by_key: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        items_by_key[(item["key"], item["condition"])].append(item)
    cells = []
    for call in calls:
        answers = call["answers"] if call["valid"] else {}
        for item in items_by_key[(call["key"], call["condition"])]:
            observed = answers.get(item["id"])
            cells.append({
                "reader_id": call["reader_id"], "model": call["model"], "key": item["key"], "slug": item["slug"],
                "condition": item["condition"], "frame_id": item["frame_id"], "pole": item["pole"], "id": item["id"],
                "expected": item["expected"], "expected_semantic": item["expected_semantic"], "observed": observed,
                "correct": observed == item["expected"], "invalid_batch": not call["valid"], "batch_error": call["error"],
            })
    if len(cells) != plan["planned_cells"]:
        raise RuntimeError("expanded cell count drift")

    models = [row["model"] for row in sorted(calls, key=lambda row: row["reader_number"]) if row["condition"] == CONDITIONS[0] and row["key"] == constructs[0]["key"]]
    model_summary = {
        model: {condition: stat([row for row in cells if row["model"] == model and row["condition"] == condition]) for condition in CONDITIONS}
        for model in models
    }
    construct_results = []
    for construct in constructs:
        key = construct["key"]
        condition_stats = {condition: stat([row for row in cells if row["key"] == key and row["condition"] == condition]) for condition in CONDITIONS}
        cold_by_reader = {model: stat([row for row in cells if row["key"] == key and row["condition"] == "ainglish_cold" and row["model"] == model])["accuracy"] for model in models}
        primary, flags, contrasts = classify(condition_stats, cold_by_reader)
        construct_results.append({
            "rank": construct["rank"], "key": key, "slug": construct["slug"], "title": construct["title"],
            "classification": primary, "flags": flags, "conditions": condition_stats, "contrasts": contrasts,
            "cold_accuracy_by_reader": cold_by_reader,
        })

    ordered_calls = sorted(calls, key=lambda row: (row["reader_number"], row["rank"], CONDITIONS.index(row["condition"])))
    responses_digest = hashlib.sha256(b"".join(canonical(row) for row in ordered_calls)).hexdigest()
    failures = [row for row in cells if not row["correct"]]
    output = {
        "schema": "ainglish.flagship-cold-clarity-analysis.v1",
        "responses_content_sha256": responses_digest,
        "response_file_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in response_files},
        "calls": len(calls), "cells": len(cells), "invalid_calls": sum(not row["valid"] for row in calls),
        "models": models, "model_summary": model_summary, "construct_results": construct_results,
        "failures": failures,
        "classification_boundary": "Model-facing development triage under RUN_PROTOCOL.md; not human validation, governance evidence, or a ratification recommendation.",
        "training_caveat": "Current models and tokenizers were trained on ordinary English, not this Ainglish register. Cold disadvantages are current-state observations; future-trained performance remains prospective.",
        "governance_evidence": False, "development_only": True, "model_downloads": 0,
    }
    output["content_sha256"] = hashlib.sha256(canonical(output)).hexdigest()
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Flagship cold-clarity atlas result", "", "Status: **complete**", "",
        f"All {len(calls)} frozen calls expanded to {len(cells)} scored cells. Invalid batches: **{output['invalid_calls']}**. No model was downloaded and no inference call was retried.", "",
        f"Raw response content digest: `{responses_digest}`. Analysis content digest: `{output['content_sha256']}`.", "",
        "## Model results", "",
        "| Installed model | Cold | One card | Careful English | Bare ambiguity | Corrupted |", "|---|---:|---:|---:|---:|---:|",
    ]
    for model in models:
        row = model_summary[model]
        lines.append(f"| `{model}` | {pct(row['ainglish_cold']['accuracy'])} | {pct(row['ainglish_defined']['accuracy'])} | {pct(row['careful_english']['accuracy'])} | {pct(row['bare_english']['accuracy'])} | {pct(row['corrupted_ainglish']['accuracy'])} |")
    lines.extend(["", "## Prospective development classification", "", "| Construct | Class | Cold | One card | Careful | Bare | Corrupted | Defined-cold | Corrupt-cold | Flags |", "|---|---|---:|---:|---:|---:|---:|---:|---:|---|"])
    for row in construct_results:
        conditions = row["conditions"]
        lines.append(
            f"| {row['title']} | `{row['classification']}` | {pct(conditions['ainglish_cold']['accuracy'])} | {pct(conditions['ainglish_defined']['accuracy'])} | {pct(conditions['careful_english']['accuracy'])} | {pct(conditions['bare_english']['accuracy'])} | {pct(conditions['corrupted_ainglish']['accuracy'])} | {row['contrasts']['defined_minus_cold']:+.3f} | {row['contrasts']['corrupted_minus_cold']:+.3f} | {', '.join(row['flags']) or 'none'} |"
        )
    lines.extend([
        "", "## Interpretation boundary", "",
        "These classifications answer a narrow model-facing development question. They do not establish how ordinary humans understand the forms, provide independent settlement voices, or change any proposal's lifecycle state.", "",
        "The one-card condition is immediate accommodation, not proof that a model was trained on Ainglish. Current models and tokenizers inherit an English training advantage; a cold Ainglish loss is an honest present-state result, while future pretraining benefits remain unproven.", "",
        "Every failed cell and channel error remains in `analysis.json`; no adverse result is discarded.", "",
    ])
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"ok": True, "models": len(models), "calls": len(calls), "cells": len(cells), "invalid_calls": output["invalid_calls"], "classifications": {row["key"]: row["classification"] for row in construct_results}, "content_sha256": output["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
