#!/usr/bin/env python3
"""Summarize the frozen development calibration result without model calls."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path

from analyze import canonical, checked


ROOT = Path(__file__).resolve().parent


def entropy(counts: Counter, total: int) -> float:
    if not total:
        return 0.0
    return round(-sum((count / total) * math.log2(count / total) for count in counts.values()), 6)


def build() -> dict:
    plan = checked(ROOT / "run-plan.json")
    packet = checked(ROOT / "development-packet.json")
    result = checked(ROOT / "development-result.json")
    if result["plan_sha256"] != plan["content_sha256"] or result["packet_sha256"] != packet["content_sha256"]:
        raise SystemExit("REFUSING: development result binding drift")
    readers = [row["name"] for row in plan["panel"]]
    items = {row["id"]: row for row in packet["items"]}
    rows = result["rows"]
    if len(rows) != len(readers) * len(items):
        raise SystemExit("REFUSING: incomplete development matrix")
    by_item = defaultdict(list)
    for row in rows:
        by_item[row["item_id"]].append(row)
    item_rows = []
    support_histogram = Counter()
    for item in packet["items"]:
        cells = by_item[item["id"]]
        counts = Counter(row["parsed_answer"] for row in cells if row["parsed_answer"] is not None)
        support = counts[item["answer"]]
        support_histogram[support] += 1
        item_rows.append({
            "item_id": item["id"],
            "axis": item["axis"],
            "answer": item["answer"],
            "key_support": support,
            "response_counts": {
                "entailed": counts["entailed"],
                "contradicted": counts["contradicted"],
                "not determined": counts["not determined"],
                "unparsed": sum(row["parsed_answer"] is None for row in cells),
            },
            "response_entropy_bits": entropy(counts, sum(counts.values())),
        })
    labels = []
    for label in packet["labels"]:
        own = [row for row in rows if row["expected"] == label]
        correct = sum(row["correct"] for row in own)
        labels.append({"label": label, "cells": len(own), "correct": correct, "accuracy": round(correct / len(own), 6)})
    axes = []
    for axis in packet["axes"]:
        own = [row for row in rows if row["axis"] == axis]
        correct = sum(row["correct"] for row in own)
        axes.append({"axis": axis, "cells": len(own), "correct": correct, "accuracy": round(correct / len(own), 6)})
    total_correct = sum(row["correct"] for row in rows)
    report = {
        "kind": "ainglish.panel.reader-qualification-development-analysis.v1",
        "evidentiary_status": "development-only exposed-control diagnosis; never qualification or proposal evidence",
        "model_calls": 0,
        "network_calls": 0,
        "source_receipts": {
            "run_plan_sha256": plan["content_sha256"],
            "development_packet_sha256": packet["content_sha256"],
            "development_result_sha256": result["content_sha256"],
        },
        "population": {"readers": len(readers), "items": len(items), "response_cells": len(rows)},
        "overall": {
            "correct_cells": total_correct,
            "accuracy": round(total_correct / len(rows), 6),
            "exact_code_cells": sum(row["exact_code"] for row in rows),
            "thinking_bytes": sum(row["thinking_bytes"] for row in rows),
            "fault_cells": sum(row["fault"] is not None for row in rows),
        },
        "key_support_histogram": {str(value): support_histogram[value] for value in range(len(readers) + 1)},
        "labels": labels,
        "axes": axes,
        "readers": result["summaries"],
        "items": item_rows,
        "findings": [
            "All eight contradicted controls were answered correctly by all six readers.",
            "Entailed controls received 44/48 correct responses; not-determined controls received only 18/48.",
            "Thirty of the run's 34 errors occurred on not-determined controls.",
            "The uniform contract removes the polar meta-question overlap but does not remove the readers' tendency to over-infer.",
            "The result is descriptive and cannot be compared causally with v7 because the item population and answer labels changed.",
        ],
        "next_development_step": {
            "action": "Freeze one generic prompt clarification and deliberately reuse these exposed controls once.",
            "clarification": "Define entailed as true in every situation consistent with the premise, contradicted as false in every such situation, and not determined as both the hypothesis and its negation remaining possible. Instruct the reader not to choose the most likely completion.",
            "guard": "The tuned reuse remains development-only. Only readers passing a prospectively frozen development gate may enter a later fresh, disjoint v8 holdout; no result here can qualify them.",
        },
    }
    report["content_sha256"] = hashlib.sha256(canonical(report)).hexdigest()
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    report = build()
    target = ROOT / "development-analysis.json"
    if args.write:
        if target.exists():
            raise SystemExit("REFUSING: development-analysis.json already exists")
        target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"overall": report["overall"], "labels": report["labels"], "sha256": report["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
