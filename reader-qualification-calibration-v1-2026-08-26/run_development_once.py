#!/usr/bin/env python3
"""Run the frozen development calibration once, retaining all outcomes."""

from __future__ import annotations

import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "reader-qualification-v7-2026-08-25"
CODES = tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    sealed = dict(value)
    expected = sealed.pop("content_sha256")
    if hashlib.sha256(canonical(sealed)).hexdigest() != expected:
        raise SystemExit(f"REFUSING: digest drift in {path}")
    return value


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


def prompt(item: dict) -> tuple[str, dict[str, str]]:
    mapping = {CODES[index]: option for index, option in enumerate(item["options"])}
    choices = "\n".join(f"{code}: {option}" for code, option in mapping.items())
    text = (
        "Given only the ordinary-English premise below, classify the hypothesis as entailed, "
        "contradicted, or not determined.\n\nPremise:\n---\n" + item["premise"] +
        "\n---\n\nHypothesis: " + item["hypothesis"] + "\nChoices:\n" + choices +
        "\nAnswer with EXACTLY one choice code and nothing else."
    )
    return text, mapping


def fault_label(exc: Exception) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        return f"http_{exc.code}"
    if isinstance(exc, urllib.error.URLError):
        return "url_error"
    if isinstance(exc, TimeoutError):
        return "timeout"
    return type(exc).__name__


def validate(plan: dict, packet: dict) -> dict:
    if plan["packet"]["content_sha256"] != packet["content_sha256"]:
        raise SystemExit("REFUSING: run plan does not bind the development packet")
    if len(packet["items"]) != 24 or len({row["id"] for row in packet["items"]}) != 24:
        raise SystemExit("REFUSING: development item population drift")
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
    if get(endpoint, "/api/ps").get("models"):
        raise SystemExit("REFUSING: resident Ollama model")
    tags = {row["name"]: row["digest"] for row in get(endpoint, "/api/tags").get("models", [])}
    for reader in plan["panel"]:
        if tags.get(reader["source_model"]) != reader["source_manifest_sha256"]:
            raise SystemExit(f"REFUSING: source model drift for {reader['name']}")
        if tags.get(reader["model"]) != reader["model_digest"].removeprefix("sha256:"):
            raise SystemExit(f"REFUSING: wrapper model drift for {reader['name']}")
        source_capabilities = post(endpoint, "/api/show", {"model": reader["source_model"]}).get("capabilities")
        wrapper_capabilities = post(endpoint, "/api/show", {"model": reader["model"]}).get("capabilities")
        if source_capabilities != reader["source_capabilities"] or wrapper_capabilities != reader["wrapper_capabilities"]:
            raise SystemExit(f"REFUSING: capability drift for {reader['name']}")
        if "thinking" in source_capabilities or "thinking" in wrapper_capabilities:
            raise SystemExit(f"REFUSING: thinking-capable reader {reader['name']}")
    return {"devices": devices, "resident_before": []}


def main() -> None:
    result_path = ROOT / "development-result.json"
    journal_path = ROOT / "development-attempt-journal.jsonl"
    if result_path.exists() or journal_path.exists():
        raise SystemExit("REFUSING: result or journal exists; never rerun burned development cells")
    plan = checked(ROOT / "run-plan.json")
    packet = checked(ROOT / plan["packet"]["file"])
    preflight = validate(plan, packet)
    endpoint = plan["gpu_gate"]["ollama_base_url"].rstrip("/")
    transport = plan["transport"]
    rows = []
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with journal_path.open("x", encoding="utf-8") as journal:
        journal_write(journal, {
            "event": "run_started", "started_at": started,
            "plan_sha256": plan["content_sha256"], "packet_sha256": packet["content_sha256"],
        })
        ordinal = 0
        for reader in plan["panel"]:
            for item in packet["items"]:
                ordinal += 1
                text, mapping = prompt(item)
                journal_write(journal, {"event": "cell_attempted", "ordinal": ordinal, "reader": reader["name"], "item_id": item["id"]})
                response = {}
                fault = None
                try:
                    response = post(endpoint, "/api/chat", {
                        "model": reader["model"],
                        "messages": [{"role": "user", "content": text}],
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
                code = raw.strip().upper()
                exact = len(code) == 1 and code in mapping
                parsed = mapping.get(code) if exact else None
                row = {
                    "reader": reader["name"], "lineage": reader["lineage"],
                    "model": reader["model"], "model_digest": reader["model_digest"],
                    "item_id": item["id"], "axis": item["axis"], "expected": item["answer"],
                    "raw_output": raw, "raw_output_sha256": hashlib.sha256(raw.encode()).hexdigest(),
                    "thinking_bytes": len(thinking.encode()), "fault": fault,
                    "exact_code": exact, "parsed_answer": parsed, "correct": parsed == item["answer"],
                    "timing": {key: response.get(key) for key in ("total_duration", "load_duration", "prompt_eval_count", "eval_count")},
                }
                rows.append(row)
                journal_write(journal, {"event": "cell_recorded", "ordinal": ordinal, "row": row})
            post(endpoint, "/api/generate", {"model": reader["model"], "prompt": "", "stream": False, "keep_alive": 0})
            if get(endpoint, "/api/ps").get("models"):
                raise SystemExit(f"REFUSING: {reader['model']} did not unload")
            journal_write(journal, {"event": "reader_completed", "reader": reader["name"]})
            print(f"completed {reader['name']}", flush=True)
        journal_write(journal, {"event": "run_completed", "cells": len(rows)})
    summaries = {}
    for reader in plan["panel"]:
        own = [row for row in rows if row["reader"] == reader["name"]]
        summaries[reader["name"]] = {
            "exact_code_cells": sum(row["exact_code"] for row in own),
            "correct_cells": sum(row["correct"] for row in own),
            "correct_by_axis": {
                axis: sum(row["correct"] for row in own if row["axis"] == axis)
                for axis in packet["axes"]
            },
            "correct_by_label": {
                label: sum(row["correct"] for row in own if row["expected"] == label)
                for label in packet["labels"]
            },
            "thinking_bytes": sum(row["thinking_bytes"] for row in own),
            "fault_cells": sum(row["fault"] is not None for row in own),
        }
    result = {
        "kind": plan["result_kind"],
        "evidentiary_status": plan["evidentiary_status"],
        "plan_sha256": plan["content_sha256"],
        "packet_sha256": packet["content_sha256"],
        "started_at": started,
        "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "gpu_preflight": preflight,
        "attempt_journal": {"file": journal_path.name, "sha256": hashlib.sha256(journal_path.read_bytes()).hexdigest()},
        "summaries": summaries,
        "rows": rows,
    }
    result["content_sha256"] = hashlib.sha256(canonical(result)).hexdigest()
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"summaries": summaries, "sha256": result["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
