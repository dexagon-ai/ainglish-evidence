#!/usr/bin/env python3
"""Freeze the controlled base-versus-adapter agent-task study."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import random
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
BENCHMARK_ROOT = REPO / "end-to-end-agent-task-benchmark-v0.1-2026-08-28"
LEARNING_ROOT = REPO / "ainglish-learning-program-2026-08-25"
CELLS_PATH = ROOT / "cells.jsonl"
EXPOSURE_PATH = ROOT / "exposure-map.json"
PLAN_PATH = ROOT / "RUN_PLAN.json"
CHECKSUM_PATH = ROOT / "SHA256SUMS.preregistered"
SCHEDULE_SEED = 2026082902
DECODING_SEED = 2026082901
BASE_MODEL = "Qwen/Qwen2.5-7B-Instruct"
BASE_REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def pretty(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def load_benchmark():
    path = BENCHMARK_ROOT / "benchmark.py"
    spec = importlib.util.spec_from_file_location("ainglish_agent_task_benchmark", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    generated = (CELLS_PATH, EXPOSURE_PATH, PLAN_PATH, CHECKSUM_PATH)
    existing = [path.name for path in generated if path.exists()]
    if existing:
        raise SystemExit("REFUSING: frozen artifacts already exist: " + ", ".join(existing))

    benchmark = load_benchmark()
    packet = benchmark.load_tasks()
    manifest_path = LEARNING_ROOT / "manifest.json"
    receipt_path = LEARNING_ROOT / "adapter-artifact-receipt.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    withheld_slugs = set(manifest["transfer_holdout_constructs"])

    constructs: dict[str, dict[str, Any]] = {}
    for item in packet["items"]:
        source_slug = item["source_slug"]
        exposure_class = "withheld_surface" if source_slug in withheld_slugs else "trained_surface"
        previous = constructs.setdefault(item["construct"], {
            "construct": item["construct"],
            "source_slug": source_slug,
            "exposure_class": exposure_class,
            "item_ids": [],
        })
        if previous["source_slug"] != source_slug or previous["exposure_class"] != exposure_class:
            raise RuntimeError(f"inconsistent exposure mapping for {item['construct']}")
        previous["item_ids"].append(item["id"])

    mapped_withheld = {record["source_slug"] for record in constructs.values() if record["exposure_class"] == "withheld_surface"}
    if mapped_withheld != withheld_slugs:
        raise RuntimeError(f"benchmark/manifest holdout mismatch: mapped={mapped_withheld} expected={withheld_slugs}")
    if len(constructs) != 11 or sum(v["exposure_class"] == "withheld_surface" for v in constructs.values()) != 4:
        raise RuntimeError("expected 11 constructs with four withheld surfaces")

    cells = []
    for item in packet["items"]:
        exposure_class = constructs[item["construct"]]["exposure_class"]
        for track in benchmark.TRACKS:
            for arm in benchmark.ARMS:
                prompt = benchmark.prompt_for(item, arm, track)
                cells.append({
                    "item_id": item["id"],
                    "construct": item["construct"],
                    "source_slug": item["source_slug"],
                    "exposure_class": exposure_class,
                    "arm": arm,
                    "track": track,
                    "prompt": prompt,
                    "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                    "clarification": item["clarification"],
                    "clarification_sha256": hashlib.sha256(item["clarification"].encode()).hexdigest(),
                })
    random.Random(SCHEDULE_SEED).shuffle(cells)
    scheduled = [{"order": index, "cell_id": f"cell-{index:03d}", **cell} for index, cell in enumerate(cells, 1)]
    if len(scheduled) != 132:
        raise RuntimeError(f"expected 132 cells, got {len(scheduled)}")

    exposure_doc = {
        "schema": "ainglish.controlled-training-exposure-map.v1",
        "source_manifest_sha256": digest(manifest_path),
        "development_training_rows": manifest["outputs"]["train-dev.jsonl"]["rows"],
        "exact_marker_holdout_boundary": manifest["contamination_boundary"],
        "constructs": sorted(constructs.values(), key=lambda row: row["construct"]),
    }
    exposure_doc["content_sha256"] = hashlib.sha256(canonical(exposure_doc)).hexdigest()
    cells_bytes = b"".join(canonical(cell) for cell in scheduled)
    plan = {
        "schema": "ainglish.controlled-training-exposure-run-plan.v1",
        "planned_observations": 264,
        "cells_per_condition": 132,
        "conditions": ["base", "adapter"],
        "base_model": BASE_MODEL,
        "base_revision": BASE_REVISION,
        "adapter_local_path": receipt["local_path"],
        "adapter_directory_sha256": receipt["directory_sha256"],
        "adapter_receipt_sha256": digest(receipt_path),
        "benchmark_tasks_sha256": digest(BENCHMARK_ROOT / "tasks.json"),
        "cells_sha256": hashlib.sha256(cells_bytes).hexdigest(),
        "exposure_map_sha256": exposure_doc["content_sha256"],
        "schedule_seed": SCHEDULE_SEED,
        "decoding": {"seed": DECODING_SEED, "do_sample": False, "max_new_tokens": 96},
        "quantization": {"bits": 4, "type": "nf4", "double_quant": True, "compute_dtype": "bfloat16"},
        "fresh_conversation_per_cell": True,
        "retry_policy": "no inference retries; interrupted calls become invalid observations",
        "downloads": 0,
        "governance_evidence": False,
    }

    EXPOSURE_PATH.write_bytes(pretty(exposure_doc))
    CELLS_PATH.write_bytes(cells_bytes)
    PLAN_PATH.write_bytes(pretty(plan))

    checksum_inputs = (
        ROOT / "README.md", ROOT / "RUN_PROTOCOL.md", ROOT / "build.py", ROOT / "run.py", ROOT / "analyse.py",
        CELLS_PATH, EXPOSURE_PATH, PLAN_PATH,
        BENCHMARK_ROOT / "README.md", BENCHMARK_ROOT / "SCORING.md", BENCHMARK_ROOT / "MANIFEST.json",
        BENCHMARK_ROOT / "tasks.json", BENCHMARK_ROOT / "benchmark.py",
        manifest_path, receipt_path,
    )
    missing = [str(path) for path in checksum_inputs if not path.exists()]
    if missing:
        raise RuntimeError("missing checksum inputs: " + ", ".join(missing))
    CHECKSUM_PATH.write_text("".join(
        f"{digest(path)}  {os.path.relpath(path, ROOT)}\n" for path in checksum_inputs
    ), encoding="utf-8")
    print(json.dumps({
        "ok": True,
        "cells": len(scheduled),
        "planned_observations": 2 * len(scheduled),
        "trained_constructs": 7,
        "withheld_constructs": 4,
        "downloads": 0,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
