#!/usr/bin/env python3
"""Apply the frozen scorer and create reader-paired benchmark reports."""

from __future__ import annotations

import argparse
import importlib.util
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
BENCHMARK_ROOT = ROOT.parent / "end-to-end-agent-task-benchmark-v0.1-2026-08-28"


def load_benchmark() -> Any:
    path = BENCHMARK_ROOT / "benchmark.py"
    spec = importlib.util.spec_from_file_location("ainglish_agent_task_benchmark", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load benchmark module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BENCHMARK = load_benchmark()


def parse_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: row is not an object")
            value["_line"] = line_number
            rows.append(value)
    return rows


def paired(classified: list[dict[str, Any]], comparator: str) -> list[dict[str, Any]]:
    cells = {
        (row["reader_id"], row["track"], row["item_id"], row["arm"]): row
        for row in classified
    }
    reader_tracks = sorted({(row["reader_id"], row["track"]) for row in classified})
    output = []
    for reader_id, track in reader_tracks:
        item_ids = sorted({
            row["item_id"] for row in classified
            if row["reader_id"] == reader_id and row["track"] == track
        })
        pairs = []
        for item_id in item_ids:
            ainglish = cells.get((reader_id, track, item_id, "ainglish"))
            other = cells.get((reader_id, track, item_id, comparator))
            if ainglish is not None and other is not None:
                a = int(ainglish["zero_repair_success"])
                b = int(other["zero_repair_success"])
                pairs.append((item_id, a, b, a - b))
        differences = [record[3] for record in pairs]
        output.append({
            "reader_id": reader_id,
            "track": track,
            "comparison": f"ainglish_minus_{comparator}",
            "paired_items": len(pairs),
            "mean_difference": round(statistics.fmean(differences), 6) if differences else None,
            "ainglish_only_success": sum(a == 1 and b == 0 for _, a, b, _ in pairs),
            f"{comparator}_only_success": sum(a == 0 and b == 1 for _, a, b, _ in pairs),
            "both_success": sum(a == 1 and b == 1 for _, a, b, _ in pairs),
            "neither_success": sum(a == 0 and b == 0 for _, a, b, _ in pairs),
            "item_differences": [{"item_id": item, "difference": difference} for item, _, _, difference in pairs],
        })
    return output


def construct_summary(classified: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in classified:
        groups[(row["reader_id"], row["track"], row["construct"], row["arm"])].append(row)
    output = []
    for (reader, track, construct, arm), rows in sorted(groups.items()):
        output.append({
            "reader_id": reader,
            "track": track,
            "construct": construct,
            "arm": arm,
            "n": len(rows),
            "zero_repair_success_rate": round(sum(row["zero_repair_success"] for row in rows) / len(rows), 6),
            "final_success_rate": round(sum(row["final_success"] for row in rows) / len(rows), 6),
            "clarification_rate": round(sum(row["clarified"] for row in rows) / len(rows), 6),
            "wrong_action_rate": round(sum(row["wrong_action"] for row in rows) / len(rows), 6),
            "invalid_output_rate": round(sum(row["invalid_output"] for row in rows) / len(rows), 6),
        })
    return output


def distribution(records: list[dict[str, Any]], comparison: str, track: str) -> dict[str, Any]:
    values = [
        row["mean_difference"] for row in records
        if row["comparison"] == comparison and row["track"] == track and row["mean_difference"] is not None
    ]
    return {
        "comparison": comparison,
        "track": track,
        "readers": len(values),
        "minimum": min(values) if values else None,
        "median": statistics.median(values) if values else None,
        "maximum": max(values) if values else None,
        "positive_readers": sum(value > 0 for value in values),
        "zero_readers": sum(value == 0 for value in values),
        "negative_readers": sum(value < 0 for value in values),
    }


def markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# Existing-reader benchmark results",
        "",
        f"Status: **{report['status']}**",
        "",
        "This is project-operated internal benchmark evidence over already-installed local model artifacts.",
        "Cold means prompt-cold; model training exposure is unknown. The one-exposure track includes a",
        "task-local Ainglish definition. Tracks are not pooled, and no call-level independence is claimed.",
        "",
        "## Completeness",
        "",
        f"- Observations: {report['observed_rows']} / {report['planned_rows']}",
        f"- Unique readers observed: {report['observed_readers']} / {report['planned_readers']}",
        "",
        "## Primary paired comparison: Ainglish minus careful English",
        "",
        "| Reader | Track | Pairs | Difference | Ainglish only | Careful only | Both | Neither |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in report["primary_paired"]:
        lines.append(
            f"| `{row['reader_id']}` | {row['track']} | {row['paired_items']} | "
            f"{row['mean_difference'] if row['mean_difference'] is not None else 'NA'} | "
            f"{row['ainglish_only_success']} | {row['careful_only_success']} | "
            f"{row['both_success']} | {row['neither_success']} |"
        )
    lines.extend([
        "",
        "A positive difference means more zero-repair successes for Ainglish on the same frozen items;",
        "zero means parity; negative means careful English did better. This table does not establish human",
        "intuitiveness, external adoption, pretraining exposure, or future token efficiency.",
        "",
        "## Across-reader descriptive distribution",
        "",
        "| Comparison | Track | Readers | Min | Median | Max | Positive | Zero | Negative |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for row in report["reader_distributions"]:
        lines.append(
            f"| {row['comparison']} | {row['track']} | {row['readers']} | {row['minimum']} | "
            f"{row['median']} | {row['maximum']} | {row['positive_readers']} | "
            f"{row['zero_readers']} | {row['negative_readers']} |"
        )
    lines.extend([
        "",
        "These are descriptive distributions of reader-level paired effects, not confidence intervals.",
        "Complete arm metrics, item differences, construct strata, token coverage, and latency coverage are",
        "preserved in `RESULTS.json`; complete raw observations remain in `results/responses.jsonl`.",
        "",
    ])
    return "\n".join(lines)


def analyse(responses: Path) -> dict[str, Any]:
    raw = parse_jsonl(responses)
    packet = BENCHMARK.load_tasks()
    classified = BENCHMARK.classify_rows(packet, [dict(row) for row in raw])
    roster = json.loads((ROOT / "reader-roster.json").read_text(encoding="utf-8"))
    plan = json.loads((ROOT / "RUN_PLAN.json").read_text(encoding="utf-8"))
    primary = paired(classified, "careful")
    secondary = paired(classified, "bare")
    all_pairs = primary + secondary
    distributions = [
        distribution(all_pairs, comparison, track)
        for comparison in ("ainglish_minus_careful", "ainglish_minus_bare")
        for track in BENCHMARK.TRACKS
    ]
    planned = plan["planned_observations"]
    return {
        "schema": "ainglish.agent-task-ollama-analysis.v0.1",
        "status": "complete" if len(raw) == planned else "partial",
        "observed_rows": len(raw),
        "planned_rows": planned,
        "observed_readers": len({row["reader_id"] for row in raw}),
        "planned_readers": len(roster["readers"]),
        "linkage": plan["linkage"],
        "benchmark_summary": BENCHMARK.summarize(classified),
        "primary_paired": primary,
        "secondary_paired": secondary,
        "reader_distributions": distributions,
        "construct_summary": construct_summary(classified),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("responses", type=Path)
    parser.add_argument("--json", type=Path, default=ROOT / "RESULTS.json")
    parser.add_argument("--markdown", type=Path, default=ROOT / "RESULTS.md")
    args = parser.parse_args()
    try:
        report = analyse(args.responses)
        args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        args.markdown.write_text(markdown_report(report), encoding="utf-8")
        print(json.dumps({
            "ok": True,
            "status": report["status"],
            "rows": report["observed_rows"],
            "readers": report["observed_readers"],
        }, sort_keys=True))
    except (OSError, ValueError, RuntimeError, BENCHMARK.ContractError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

