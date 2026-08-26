#!/usr/bin/env python3
"""Run the frozen format-only structured-output compatibility screen."""

from __future__ import annotations

import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.error
import urllib.request

from build_plan import canonical, checked


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "reader-qualification-v7-2026-08-25"


def get(endpoint: str, path: str) -> dict:
    with urllib.request.urlopen(endpoint + path, timeout=30) as response:
        return json.load(response)


def post(endpoint: str, path: str, payload: dict, timeout: int = 360) -> dict:
    request = urllib.request.Request(
        endpoint + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
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


def validate(plan: dict) -> dict:
    if len(plan["controls"]) != 12 or {row["target"] for row in plan["controls"]} != set("ABC"):
        raise SystemExit("REFUSING: control population drift")
    if any(sum(row["target"] == target for row in plan["controls"]) != 4 for target in "ABC"):
        raise SystemExit("REFUSING: target imbalance")
    for receipt in plan["source_reader_specs"]:
        source = checked(SOURCE / receipt["file"])
        if source["content_sha256"] != receipt["content_sha256"]:
            raise SystemExit(f"REFUSING: source reader spec drift in {receipt['file']}")
    devices = gpu_rows()
    gate = plan["gpu_gate"]
    if sum(row["free_mib"] for row in devices) < gate["minimum_total_free_mib"]:
        raise SystemExit("REFUSING: free-VRAM gate")
    if max(row["utilization"] for row in devices) > gate["maximum_utilization_percent"]:
        raise SystemExit("REFUSING: utilization gate")
    endpoint = gate["ollama_base_url"].rstrip("/")
    runtime = get(endpoint, "/api/version").get("version")
    if runtime != plan["runtime"]["ollama_version"]:
        raise SystemExit(f"REFUSING: Ollama version drift {runtime}")
    if get(endpoint, "/api/ps").get("models"):
        raise SystemExit("REFUSING: resident Ollama model")
    tags = {row["name"]: row["digest"] for row in get(endpoint, "/api/tags").get("models", [])}
    for reader in plan["panel"]:
        if tags.get(reader["source_model"]) != reader["source_manifest_sha256"]:
            raise SystemExit(f"REFUSING: source model drift for {reader['name']}")
        capabilities = post(endpoint, "/api/show", {"model": reader["source_model"]}).get("capabilities")
        if capabilities != reader["source_capabilities"] or "thinking" in capabilities:
            raise SystemExit(f"REFUSING: capability drift for {reader['name']}")
    return {"devices": devices, "resident_before": [], "ollama_version": runtime}


def main() -> None:
    result_path = ROOT / "result.json"
    journal_path = ROOT / "attempt-journal.jsonl"
    if result_path.exists() or journal_path.exists():
        raise SystemExit("REFUSING: result or journal exists; never rerun burned format cells")
    plan = checked(ROOT / "plan.json")
    preflight = validate(plan)
    endpoint = plan["gpu_gate"]["ollama_base_url"].rstrip("/")
    transport = plan["transport"]
    rows = []
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with journal_path.open("x", encoding="utf-8") as journal:
        journal_write(journal, {"event": "run_started", "started_at": started, "plan_sha256": plan["content_sha256"]})
        ordinal = 0
        for reader in plan["panel"]:
            for control in plan["controls"]:
                ordinal += 1
                journal_write(journal, {"event": "cell_attempted", "ordinal": ordinal, "reader": reader["name"], "control_id": control["id"]})
                response = {}
                fault = None
                try:
                    response = post(endpoint, "/api/chat", {
                        "model": reader["source_model"],
                        "messages": [{
                            "role": "user",
                            "content": "Respond with one JSON object matching the supplied schema. " + control["instruction"] + " Add no other fields.",
                        }],
                        "format": transport["format"],
                        "think": False,
                        "stream": False,
                        "keep_alive": -1,
                        "options": {
                            "temperature": transport["temperature"],
                            "seed": transport["seed"],
                            "num_predict": transport["max_tokens"],
                            "num_ctx": transport["num_ctx"],
                        },
                    }, timeout=transport["timeout_s"])
                except Exception as exc:  # retain adverse cells and never retry
                    fault = fault_label(exc)
                raw = ((response.get("message") or {}).get("content") or "")
                thinking = ((response.get("message") or {}).get("thinking") or "")
                parsed = None
                parse_error = None
                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError as exc:
                    parse_error = f"json_decode:{exc.msg}"
                valid_json = parse_error is None
                schema_exact = (
                    isinstance(parsed, dict)
                    and set(parsed) == {"answer"}
                    and isinstance(parsed["answer"], str)
                    and parsed["answer"] in "ABC"
                )
                target_correct = schema_exact and parsed["answer"] == control["target"]
                row = {
                    "reader": reader["name"], "lineage": reader["lineage"],
                    "model": reader["source_model"], "model_digest": "sha256:" + reader["source_manifest_sha256"],
                    "control_id": control["id"], "target": control["target"],
                    "raw_output": raw, "raw_output_sha256": hashlib.sha256(raw.encode()).hexdigest(),
                    "parsed": parsed, "parse_error": parse_error,
                    "thinking_bytes": len(thinking.encode()), "fault": fault,
                    "valid_json": valid_json, "schema_exact": schema_exact, "target_correct": target_correct,
                    "timing": {key: response.get(key) for key in ("total_duration", "load_duration", "prompt_eval_count", "eval_count")},
                }
                rows.append(row)
                journal_write(journal, {"event": "cell_recorded", "ordinal": ordinal, "row": row})
            post(endpoint, "/api/generate", {"model": reader["source_model"], "prompt": "", "stream": False, "keep_alive": 0})
            if get(endpoint, "/api/ps").get("models"):
                raise SystemExit(f"REFUSING: {reader['source_model']} did not unload")
            journal_write(journal, {"event": "reader_completed", "reader": reader["name"]})
            print(f"completed {reader['name']}", flush=True)
        journal_write(journal, {"event": "run_completed", "cells": len(rows)})
    gate = plan["compatibility_gate"]
    summaries = {}
    compatible = []
    for reader in plan["panel"]:
        own = [row for row in rows if row["reader"] == reader["name"]]
        observed = {
            "valid_json_cells": sum(row["valid_json"] for row in own),
            "schema_exact_cells": sum(row["schema_exact"] for row in own),
            "target_correct_cells": sum(row["target_correct"] for row in own),
            "thinking_bytes": sum(row["thinking_bytes"] for row in own),
            "fault_cells": sum(row["fault"] is not None for row in own),
        }
        decision = all(observed[key] == value for key, value in gate.items())
        summaries[reader["name"]] = {"observed": observed, "format_compatible": decision}
        if decision:
            compatible.append({"name": reader["name"], "lineage": reader["lineage"]})
    result = {
        "kind": plan["result_kind"],
        "evidentiary_status": plan["evidentiary_status"],
        "plan_sha256": plan["content_sha256"],
        "started_at": started,
        "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "preflight": preflight,
        "attempt_journal": {"file": journal_path.name, "sha256": hashlib.sha256(journal_path.read_bytes()).hexdigest()},
        "summaries": summaries,
        "compatible_readers": compatible,
        "rows": rows,
    }
    result["content_sha256"] = hashlib.sha256(canonical(result)).hexdigest()
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"summaries": summaries, "compatible_readers": compatible, "sha256": result["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
