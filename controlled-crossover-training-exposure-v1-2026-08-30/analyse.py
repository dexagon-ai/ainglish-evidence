#!/usr/bin/env python3
"""Score frozen cross-over conditions and apply the prospective interpretation."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from integrity import ROOT, canonical, jsonl, pretty


CONDITIONS = ("base", "adapter-a", "adapter-b")
ARMS = ("ainglish_cold", "careful_english", "bare_english")


def stat(rows: list[dict[str, Any]]) -> dict[str, Any]:
    correct = sum(row["correct"] for row in rows)
    valid = sum(row["valid"] for row in rows)
    return {"correct": correct, "total": len(rows), "accuracy": round(correct / len(rows), 6) if rows else None, "valid": valid, "invalid": len(rows) - valid}


def pct(value: float) -> str:
    return f"{100 * value:.1f}%"


def main() -> None:
    target = ROOT / "analysis.json"
    report = ROOT / "RESULT.md"
    if target.exists() or report.exists():
        raise SystemExit("REFUSING: analysis output already exists")
    plan = json.loads((ROOT / "RUN_PLAN.json").read_text(encoding="utf-8"))
    evaluation = {row["id"]: row for row in jsonl(ROOT / "eval.jsonl")}
    calls = []
    response_hashes = {}
    for condition in CONDITIONS:
        path = ROOT / "results" / f"{condition}.jsonl"
        rows = jsonl(path)
        if len(rows) != len(evaluation):
            raise SystemExit(f"REFUSING: {condition} expected {len(evaluation)} rows, got {len(rows)}")
        response_hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        calls.extend(rows)
    keys = [(row["condition"], row["id"]) for row in calls]
    if len(keys) != len(set(keys)):
        raise SystemExit("REFUSING: duplicate condition/evaluation ID")
    cells = []
    for row in calls:
        source = evaluation[row["id"]]
        if row["key"] != source["key"] or row["arm"] != source["condition"] or row["expected"] != source["expected"]:
            raise RuntimeError(f"result/source binding drift: {row['condition']} {row['id']}")
        cells.append({**row, "correct": row["valid"] and row["observed"] == row["expected"], "exposure_group": source["exposure_group"], "pole": source["pole"], "frame_id": source["frame_id"]})

    keys_ordered = plan["groups"]["a"] + plan["groups"]["b"]
    condition_summary = {condition: {arm: stat([row for row in cells if row["condition"] == condition and row["arm"] == arm]) for arm in ARMS} for condition in CONDITIONS}
    construct_results = []
    for key in keys_ordered:
        group = "a" if key in plan["groups"]["a"] else "b"
        exposed_name, unexposed_name = f"adapter-{group}", f"adapter-{'b' if group == 'a' else 'a'}"
        stats = {condition: {arm: stat([row for row in cells if row["key"] == key and row["condition"] == condition and row["arm"] == arm]) for arm in ARMS} for condition in CONDITIONS}
        base_cold = stats["base"]["ainglish_cold"]["accuracy"]
        exposed_cold = stats[exposed_name]["ainglish_cold"]["accuracy"]
        unexposed_cold = stats[unexposed_name]["ainglish_cold"]["accuracy"]
        contrasts = {
            "exposed_minus_base_cold": round(exposed_cold - base_cold, 6),
            "exposed_minus_unexposed_cold": round(exposed_cold - unexposed_cold, 6),
            "unexposed_minus_base_cold": round(unexposed_cold - base_cold, 6),
            "exposed_minus_base_careful": round(stats[exposed_name]["careful_english"]["accuracy"] - stats["base"]["careful_english"]["accuracy"], 6),
            "exposed_minus_base_bare": round(stats[exposed_name]["bare_english"]["accuracy"] - stats["base"]["bare_english"]["accuracy"], 6),
        }
        selective = (
            exposed_cold >= 0.80 and contrasts["exposed_minus_base_cold"] >= 0.10 and contrasts["exposed_minus_unexposed_cold"] >= 0.10
            and contrasts["exposed_minus_base_careful"] >= -0.05 and contrasts["exposed_minus_base_bare"] >= -0.05
        )
        same_direction_large = (
            abs(contrasts["exposed_minus_base_cold"]) >= 0.10 and abs(contrasts["unexposed_minus_base_cold"]) >= 0.10
            and contrasts["exposed_minus_base_cold"] * contrasts["unexposed_minus_base_cold"] > 0
            and abs(exposed_cold - unexposed_cold) <= 0.05
        )
        broad = same_direction_large or contrasts["exposed_minus_base_careful"] < -0.10 or contrasts["exposed_minus_base_bare"] < -0.10
        interpretation = "selective_uptake" if selective else ("broad_behavior_shift" if broad else "no_demonstrated_selective_uptake")
        construct_results.append({
            "key": key, "exposure_group": group, "exposed_condition": exposed_name, "unexposed_condition": unexposed_name,
            "interpretation": interpretation, "stats": stats, "contrasts": contrasts,
        })

    group_results = {}
    for group, group_keys in plan["groups"].items():
        exposed_name, unexposed_name = f"adapter-{group}", f"adapter-{'b' if group == 'a' else 'a'}"
        group_results[group] = {
            "constructs": group_keys,
            "cold": {condition: stat([row for row in cells if row["key"] in group_keys and row["condition"] == condition and row["arm"] == "ainglish_cold"]) for condition in CONDITIONS},
            "exposed_condition": exposed_name, "unexposed_condition": unexposed_name,
        }
    ordered_cells = sorted(cells, key=lambda row: (CONDITIONS.index(row["condition"]), row["id"]))
    output = {
        "schema": "ainglish.controlled-crossover-exposure-analysis.v1",
        "responses_sha256": hashlib.sha256(b"".join(canonical(row) for row in ordered_cells)).hexdigest(),
        "response_file_sha256": response_hashes,
        "predictions": len(cells), "invalid_predictions": sum(not row["valid"] for row in cells),
        "condition_summary": condition_summary, "group_results": group_results, "construct_results": construct_results,
        "failures": [row for row in cells if not row["correct"]],
        "claim_boundary": "Project-linked supervised QLoRA development result; not future pretraining, human validation, independent governance evidence, or ratification support.",
        "downloads": 0, "governance_evidence": False,
    }
    output["content_sha256"] = hashlib.sha256(canonical(output)).hexdigest()
    target.write_bytes(pretty(output))

    source_pins = {row["key"]: row for row in json.loads((ROOT / "source-pins.json").read_text(encoding="utf-8"))["constructs"]}
    lines = [
        "# Controlled cross-over training-exposure result", "", "Status: **complete**", "",
        f"All {len(cells)} planned predictions completed. Invalid predictions: **{output['invalid_predictions']}**. No model was downloaded and no inference was retried.", "",
        f"Response digest: `{output['responses_sha256']}`. Analysis digest: `{output['content_sha256']}`.", "",
        "## Overall arms", "", "| Condition | Cold Ainglish | Careful English | Bare ambiguity |", "|---|---:|---:|---:|",
    ]
    for condition in CONDITIONS:
        row = condition_summary[condition]
        lines.append(f"| `{condition}` | {pct(row['ainglish_cold']['accuracy'])} | {pct(row['careful_english']['accuracy'])} | {pct(row['bare_english']['accuracy'])} |")
    lines.extend(["", "## Construct-level cross-over result", "", "| Construct | Exposed | Base cold | Exposed cold | Unexposed cold | Exposed-base | Exposed-unexposed | Careful change | Bare change | Interpretation |", "|---|---|---:|---:|---:|---:|---:|---:|---:|---|"])
    for row in construct_results:
        stats = row["stats"]
        contrasts = row["contrasts"]
        lines.append(
            f"| {source_pins[row['key']]['title']} | `{row['exposed_condition']}` | {pct(stats['base']['ainglish_cold']['accuracy'])} | {pct(stats[row['exposed_condition']]['ainglish_cold']['accuracy'])} | {pct(stats[row['unexposed_condition']]['ainglish_cold']['accuracy'])} | {contrasts['exposed_minus_base_cold']:+.3f} | {contrasts['exposed_minus_unexposed_cold']:+.3f} | {contrasts['exposed_minus_base_careful']:+.3f} | {contrasts['exposed_minus_base_bare']:+.3f} | `{row['interpretation']}` |"
        )
    lines.extend([
        "", "## Claim boundary", "",
        "This experiment tests selective learnability under supervised QLoRA exposure. It is not foundation-model pretraining, tokenizer redesign, human validation, an independent Ainglish measurement, or a ratification recommendation.", "",
        "A favourable exposed-versus-cross-over contrast would support only the narrow claim that the exact construct can be learned under this task and dose. A null or broad shift is retained without tuning or retraining.", "",
    ])
    report.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"ok": True, "predictions": len(cells), "invalid": output["invalid_predictions"], "interpretations": {row["key"]: row["interpretation"] for row in construct_results}, "content_sha256": output["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
