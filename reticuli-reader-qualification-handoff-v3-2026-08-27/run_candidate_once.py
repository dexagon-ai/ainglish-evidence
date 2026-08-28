#!/usr/bin/env python3
"""Run a frozen candidate through format, then exposed semantic development if eligible."""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import time
import urllib.error
import urllib.request

from build_candidate_plan import canonical, checked


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
CODES = tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
ANSWER_CODES = frozenset(CODES[:3])


def get(endpoint: str, path: str) -> dict:
    with urllib.request.urlopen(endpoint + path, timeout=30) as response:
        return json.load(response)


def post(endpoint: str, path: str, payload: dict, timeout: int = 600) -> dict:
    request = urllib.request.Request(endpoint + path, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def gpu_rows() -> list[dict]:
    output = subprocess.run([
        "nvidia-smi", "--query-gpu=index,name,memory.free,utilization.gpu",
        "--format=csv,noheader,nounits",
    ], check=True, capture_output=True, text=True).stdout
    rows = []
    for line in output.splitlines():
        index, name, free, utilization = [part.strip() for part in line.split(",", 3)]
        rows.append({"index": int(index), "name": name, "free_mib": int(free), "utilization": int(utilization)})
    return rows


def compute_process_rows() -> list[dict]:
    completed = subprocess.run([
        "nvidia-smi", "--query-compute-apps=pid,process_name,used_gpu_memory",
        "--format=csv,noheader,nounits",
    ], check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise SystemExit("REFUSING: cannot enumerate CUDA compute contexts")
    rows = []
    for line in completed.stdout.splitlines():
        if not line.strip() or "No running processes found" in line:
            continue
        parts = [part.strip() for part in line.split(",", 2)]
        if len(parts) != 3:
            raise SystemExit("REFUSING: unparseable CUDA compute context")
        pid, process_name, used_memory = parts
        rows.append({"pid": int(pid), "process_name": process_name, "used_memory_mib": int(used_memory)})
    return rows


def sampled_gpu_receipt(sample_count: int, interval_ms: int) -> dict:
    samples = []
    for ordinal in range(sample_count):
        samples.append(gpu_rows())
        if ordinal + 1 < sample_count:
            time.sleep(interval_ms / 1000)
    device_shapes = [[(row["index"], row["name"]) for row in sample] for sample in samples]
    if not device_shapes or any(shape != device_shapes[0] for shape in device_shapes[1:]):
        raise SystemExit("REFUSING: GPU inventory changed during resource sampling")
    maximum_utilizations = [max(row["utilization"] for row in sample) for sample in samples]
    total_free = [sum(row["free_mib"] for row in sample) for sample in samples]
    ordered = sorted(maximum_utilizations)
    p95 = ordered[math.ceil(0.95 * len(ordered)) - 1]
    return {
        "samples": samples,
        "minimum_total_free_mib_observed": min(total_free),
        "maximum_device_utilization_median_percent": statistics.median(maximum_utilizations),
        "maximum_device_utilization_p95_percent": p95,
        "p95_method": "nearest-rank",
    }


def journal_write(handle, value: dict) -> None:
    handle.write(json.dumps(value, sort_keys=True, ensure_ascii=False) + "\n")
    handle.flush()
    os.fsync(handle.fileno())


def fault_label(exc: Exception) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        return f"http_{exc.code}"
    if isinstance(exc, urllib.error.URLError):
        return "url_error"
    if isinstance(exc, TimeoutError):
        return "timeout"
    return type(exc).__name__


def decode(raw: str) -> tuple[object, str | None, bool]:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, f"json_decode:{exc.msg}", False
    exact = (
        isinstance(parsed, dict)
        and set(parsed) == {"answer"}
        and isinstance(parsed["answer"], str)
        and parsed["answer"] in ANSWER_CODES
    )
    return parsed, None, exact


def request_cell(endpoint: str, plan: dict, prompt: str) -> tuple[dict, str | None]:
    transport = plan["transport"]
    try:
        response = post(endpoint, "/api/chat", {
            "model": plan["candidate"]["source_model"],
            "messages": [{"role": "user", "content": prompt}],
            "format": transport["format"],
            "think": transport["think"],
            "stream": False,
            "keep_alive": -1,
            "options": {
                "temperature": transport["temperature"], "seed": transport["seed"],
                "num_predict": transport["max_tokens"], "num_ctx": transport["num_ctx"],
            },
        }, timeout=transport["timeout_s"])
        return response, None
    except Exception as exc:
        return {}, fault_label(exc)


def observed_format(rows: list[dict]) -> dict:
    return {
        "valid_json_cells": sum(row["valid_json"] for row in rows),
        "schema_exact_cells": sum(row["schema_exact"] for row in rows),
        "target_correct_cells": sum(row["target_correct"] for row in rows),
        "thinking_bytes": sum(row["thinking_bytes"] for row in rows),
        "fault_cells": sum(row["fault"] is not None for row in rows),
    }


def format_passed(plan: dict, observed: dict) -> bool:
    gate = plan["format_stage"]["gate"]
    return (
        observed["valid_json_cells"] == gate["valid_json_cells_required"]
        and observed["schema_exact_cells"] == gate["schema_exact_cells_required"]
        and observed["target_correct_cells"] == gate["target_correct_cells_required"]
        and observed["thinking_bytes"] == gate["thinking_bytes_required"]
        and observed["fault_cells"] == gate["fault_cells_required"]
    )


def observed_semantic(packet: dict, rows: list[dict]) -> dict:
    return {
        "valid_json_cells": sum(row["valid_json"] for row in rows),
        "schema_exact_cells": sum(row["schema_exact"] for row in rows),
        "correct_cells": sum(row["correct"] for row in rows),
        "correct_by_axis": {axis: sum(row["correct"] for row in rows if row["axis"] == axis) for axis in packet["axes"]},
        "correct_by_label": {label: sum(row["correct"] for row in rows if row["expected_label"] == label) for label in packet["labels"]},
        "thinking_bytes": sum(row["thinking_bytes"] for row in rows),
        "fault_cells": sum(row["fault"] is not None for row in rows),
    }


def semantic_passed(plan: dict, observed: dict) -> bool:
    gate = plan["semantic_stage"]["gate"]
    return (
        observed["valid_json_cells"] == gate["valid_json_cells_required"]
        and observed["schema_exact_cells"] == gate["schema_exact_cells_required"]
        and observed["correct_cells"] >= gate["correct_cells_required"]
        and all(value >= gate["correct_per_axis_required"] for value in observed["correct_by_axis"].values())
        and all(value >= gate["correct_per_label_required"] for value in observed["correct_by_label"].values())
        and observed["thinking_bytes"] == gate["thinking_bytes_required"]
        and observed["fault_cells"] == gate["fault_cells_required"]
    )


def validate(plan: dict) -> tuple[dict, dict]:
    packet_path = REPO / plan["semantic_stage"]["packet"]["file"]
    packet = checked(packet_path)
    if packet["content_sha256"] != plan["semantic_stage"]["packet"]["content_sha256"]:
        raise SystemExit("REFUSING: semantic packet drift")
    gate = plan["gpu_gate"]
    gpu_receipt = sampled_gpu_receipt(gate["utilization_samples"], gate["utilization_sample_interval_ms"])
    compute_processes = compute_process_rows()
    if (
        gpu_receipt["minimum_total_free_mib_observed"] < gate["minimum_total_free_mib"]
        or gpu_receipt["maximum_device_utilization_median_percent"] > gate["maximum_median_utilization_percent"]
        or gpu_receipt["maximum_device_utilization_p95_percent"] > gate["maximum_p95_utilization_percent"]
        or (gate["require_no_compute_processes"] and compute_processes)
    ):
        raise SystemExit("REFUSING: GPU gate")
    endpoint = gate["ollama_base_url"].rstrip("/")
    if get(endpoint, "/api/version").get("version") != plan["runtime"]["ollama_version"]:
        raise SystemExit("REFUSING: Ollama version drift")
    if get(endpoint, "/api/ps").get("models"):
        raise SystemExit("REFUSING: resident Ollama model")
    tags = {row["name"]: row["digest"] for row in get(endpoint, "/api/tags").get("models", [])}
    candidate = plan["candidate"]
    if tags.get(candidate["source_model"]) != candidate["source_manifest_sha256"]:
        raise SystemExit("REFUSING: candidate manifest drift")
    shown = post(endpoint, "/api/show", {"model": candidate["source_model"]})
    capabilities = shown.get("capabilities") or []
    if capabilities != candidate["capabilities"]:
        raise SystemExit("REFUSING: candidate capability drift")
    thinking_control = candidate.get("thinking_control")
    if thinking_control is None:
        if "thinking" in capabilities or plan["transport"]["think"]:
            raise SystemExit("REFUSING: unexpected thinking capability or request")
    else:
        if ("thinking" in capabilities) is not thinking_control["capability_expected"]:
            raise SystemExit("REFUSING: candidate thinking capability drift")
        if plan["transport"]["think"] is not thinking_control["request_value"]:
            raise SystemExit("REFUSING: frozen thinking request drift")
        template = shown.get("template") or ""
        if hashlib.sha256(template.encode()).hexdigest() != candidate["template_sha256"]:
            raise SystemExit("REFUSING: candidate template drift")
        if any(marker not in template for marker in thinking_control["required_template_markers"]):
            raise SystemExit("REFUSING: candidate zero-thinking template contract drift")
    return packet, {
        "gpu_sampling": gpu_receipt,
        "compute_processes": compute_processes,
        "resident_before": [],
        "ollama_version": plan["runtime"]["ollama_version"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True)
    args = parser.parse_args()
    plan = checked(ROOT / args.plan)
    result_path = ROOT / plan["result_file"]
    journal_path = ROOT / plan["journal_file"]
    if result_path.exists() or journal_path.exists():
        raise SystemExit("REFUSING: result or journal exists; never rerun burned candidate cells")
    packet, preflight = validate(plan)
    endpoint = plan["gpu_gate"]["ollama_base_url"].rstrip("/")
    format_rows = []
    semantic_rows = []
    ordinal = 0
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with journal_path.open("x", encoding="utf-8") as journal:
        journal_write(journal, {"event": "run_started", "started_at": started, "plan_sha256": plan["content_sha256"]})
        for control in plan["format_stage"]["controls"]:
            ordinal += 1
            journal_write(journal, {"event": "cell_attempted", "stage": "format", "ordinal": ordinal, "control_id": control["id"]})
            response, fault = request_cell(endpoint, plan, "Respond with one JSON object matching the supplied schema. " + control["instruction"] + " Add no other fields.")
            raw = ((response.get("message") or {}).get("content") or "")
            thinking = ((response.get("message") or {}).get("thinking") or "")
            parsed, parse_error, exact = decode(raw)
            row = {
                "stage": "format", "control_id": control["id"], "target": control["target"],
                "raw_output": raw, "raw_output_sha256": hashlib.sha256(raw.encode()).hexdigest(),
                "parsed": parsed, "parse_error": parse_error, "valid_json": parse_error is None,
                "schema_exact": exact, "target_correct": exact and parsed["answer"] == control["target"],
                "thinking_bytes": len(thinking.encode()), "fault": fault,
                "timing": {key: response.get(key) for key in ("total_duration", "load_duration", "prompt_eval_count", "eval_count")},
            }
            format_rows.append(row)
            journal_write(journal, {"event": "cell_recorded", "stage": "format", "ordinal": ordinal, "row": row})
        format_observed = observed_format(format_rows)
        format_ok = format_passed(plan, format_observed)
        journal_write(journal, {"event": "format_completed", "observed": format_observed, "passed": format_ok})
        if format_ok:
            for item in packet["items"]:
                ordinal += 1
                mapping = {CODES[index]: label for index, label in enumerate(item["options"])}
                choices = "\n".join(f"{code}: {label}" for code, label in mapping.items())
                prompt = (
                    plan["semantic_stage"]["prompt_contract"] + "\n\nPremise:\n---\n" + item["premise"] +
                    "\n---\n\nHypothesis: " + item["hypothesis"] + "\nChoices:\n" + choices +
                    "\nRespond with one JSON object whose answer field is exactly the selected choice code."
                )
                journal_write(journal, {"event": "cell_attempted", "stage": "semantic", "ordinal": ordinal, "item_id": item["id"]})
                response, fault = request_cell(endpoint, plan, prompt)
                raw = ((response.get("message") or {}).get("content") or "")
                thinking = ((response.get("message") or {}).get("thinking") or "")
                parsed, parse_error, exact = decode(raw)
                parsed_code = parsed["answer"] if exact else None
                parsed_label = mapping.get(parsed_code)
                expected_code = next(code for code, label in mapping.items() if label == item["answer"])
                row = {
                    "stage": "semantic", "item_id": item["id"], "axis": item["axis"],
                    "expected_label": item["answer"], "expected_code": expected_code,
                    "raw_output": raw, "raw_output_sha256": hashlib.sha256(raw.encode()).hexdigest(),
                    "parsed": parsed, "parse_error": parse_error, "valid_json": parse_error is None,
                    "schema_exact": exact, "parsed_code": parsed_code, "parsed_label": parsed_label,
                    "correct": parsed_label == item["answer"], "thinking_bytes": len(thinking.encode()), "fault": fault,
                    "timing": {key: response.get(key) for key in ("total_duration", "load_duration", "prompt_eval_count", "eval_count")},
                }
                semantic_rows.append(row)
                journal_write(journal, {"event": "cell_recorded", "stage": "semantic", "ordinal": ordinal, "row": row})
        semantic_observed = observed_semantic(packet, semantic_rows) if semantic_rows else None
        development_ok = semantic_passed(plan, semantic_observed) if semantic_observed else False
        journal_write(journal, {"event": "run_completed", "format_passed": format_ok, "semantic_cells": len(semantic_rows), "development_passed": development_ok})
    post(endpoint, "/api/generate", {"model": plan["candidate"]["source_model"], "prompt": "", "stream": False, "keep_alive": 0})
    if get(endpoint, "/api/ps").get("models"):
        raise SystemExit("REFUSING: candidate did not unload")
    result = {
        "kind": plan["result_kind"], "evidentiary_status": plan["evidentiary_status"],
        "plan_sha256": plan["content_sha256"], "candidate": plan["candidate"],
        "started_at": started, "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "preflight": preflight,
        "attempt_journal": {"file": journal_path.name, "sha256": hashlib.sha256(journal_path.read_bytes()).hexdigest()},
        "format": {"observed": format_observed, "passed": format_ok, "rows": format_rows},
        "semantic": {"exposed": format_ok, "observed": semantic_observed, "passed": development_ok, "rows": semantic_rows},
        "v8_holdout_eligible": development_ok,
    }
    result["content_sha256"] = hashlib.sha256(canonical(result)).hexdigest()
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "candidate": plan["candidate"]["lineage"],
        "format": {"observed": format_observed, "passed": format_ok},
        "semantic": {k: v for k, v in result["semantic"].items() if k != "rows"},
        "v8_holdout_eligible": development_ok,
        "sha256": result["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
