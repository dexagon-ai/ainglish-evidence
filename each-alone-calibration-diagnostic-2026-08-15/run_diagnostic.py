#!/usr/bin/env python3
"""Capture raw answers for the failed construct-free calibration, on GPU only.

This deliberately does not invoke run_panel and does not load any scientific item. It recreates
the released ask() prompt and exact parser around chat() so the otherwise-discarded raw response
can be audited. It is a harness diagnostic, never proposal evidence.
"""

from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request

from ainglish import __version__ as sdk_version
from ainglish import panel


ROOT = Path(__file__).resolve().parent
SPEC_PATH = ROOT / "diagnostic-spec.json"
RESULT_PATH = ROOT / "diagnostic-results.json"


def canonical_sha(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def api_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.load(response)


def gpu_rows() -> list[dict]:
    command = [
        "nvidia-smi",
        "--query-gpu=index,pci.bus_id,name,memory.used,memory.free,utilization.gpu",
        "--format=csv,noheader,nounits",
    ]
    lines = subprocess.run(command, check=True, capture_output=True, text=True).stdout.splitlines()
    rows = []
    for line in lines:
        index, pci, name, used, free, utilization = [part.strip() for part in line.split(",", 5)]
        rows.append({
            "index": int(index),
            "pci_bus_id": pci,
            "name": name,
            "memory_used_mib": int(used),
            "memory_free_mib": int(free),
            "utilization_percent": int(utilization),
        })
    return rows


def prompt_for(text: str, question: str, options: list[str]) -> str:
    return (
        f"Read this message written by one agent to another:\n\n---\n{text}\n---\n\n"
        f"Question: {question}\nAnswer with EXACTLY one of these options and nothing else: "
        + " | ".join(options)
    )


def parse(raw: str, truncated: bool, options: list[str]) -> tuple[str | None, str]:
    if truncated:
        return None, "truncated"
    normalized = raw.strip().casefold()
    if not normalized:
        return None, "empty_stop"
    exact = {str(option).strip().casefold(): option for option in options}
    if normalized in exact:
        return str(exact[normalized]), "exact_option"
    return normalized[:40], "off_option"


def summarize(rows: list[dict]) -> dict:
    summary = {}
    for row in rows:
        key = f"{row['reader']}|{row['arm']}"
        bucket = summary.setdefault(key, {
            "reader": row["reader"],
            "arm": row["arm"],
            "cells": 0,
            "correct": 0,
            "exact_option": 0,
            "off_option": 0,
            "empty_or_truncated": 0,
        })
        bucket["cells"] += 1
        bucket["correct"] += int(row["correct"])
        if row["parse_state"] == "exact_option":
            bucket["exact_option"] += 1
        elif row["parse_state"] == "off_option":
            bucket["off_option"] += 1
        else:
            bucket["empty_or_truncated"] += 1
    for bucket in summary.values():
        bucket["accuracy"] = bucket["correct"] / bucket["cells"]
    return {key: summary[key] for key in sorted(summary)}


def main() -> None:
    if RESULT_PATH.exists():
        raise SystemExit(f"REFUSING: {RESULT_PATH.name} already exists; this diagnostic is not rerun in place")

    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    if sdk_version != spec["source_sdk_version"]:
        raise SystemExit(f"REFUSING: SDK {sdk_version} does not match frozen {spec['source_sdk_version']}")
    if len(spec["items"]) != 6 or any(not item["id"].startswith("dexagon-count-calibration-")
                                      for item in spec["items"]):
        raise SystemExit("REFUSING: diagnostic must contain exactly the six generic controls")
    forbidden = ("each-alone", "as-one", "rosetta-amount")
    if any(token in json.dumps(spec["items"], ensure_ascii=False) for token in forbidden):
        raise SystemExit("REFUSING: scientific construct or source item leaked into diagnostic")

    gate = spec["gpu_gate"]
    devices = gpu_rows()
    device = next((row for row in devices if row["index"] == gate["index"]), None)
    if device is None or device["memory_free_mib"] < gate["minimum_free_mib"]:
        raise SystemExit(f"REFUSING: GPU {gate['index']} does not meet the frozen free-VRAM gate")
    shared = api_json(gate["shared_ollama_ps"])
    dedicated = api_json(gate["dedicated_ollama_ps"])
    if shared.get("models") or dedicated.get("models"):
        raise SystemExit("REFUSING: an Ollama service already has a resident model")

    rows = []
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    for reader in spec["panel"]:
        for item in spec["items"]:
            for arm in ("english", "ainglish"):
                prompt = prompt_for(item[arm], item["question"], item["options"])
                raw, truncated = panel.chat(reader, prompt)
                parsed, state = parse(raw, truncated, item["options"])
                rows.append({
                    "reader": reader["name"],
                    "model": reader["model"],
                    "item_id": item["id"],
                    "arm": arm,
                    "expected": item["answer"],
                    "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                    "raw_output": raw,
                    "raw_output_sha256": hashlib.sha256(raw.encode()).hexdigest(),
                    "truncated": truncated,
                    "parsed_answer": parsed,
                    "parse_state": state,
                    "correct": parsed is not None and parsed.casefold() == item["answer"].casefold(),
                })

    document = {
        "kind": "ainglish.panel.calibration-diagnostic-result.v1",
        "evidentiary_status": "construct-free post-abort harness diagnostic; not proposal evidence",
        "spec_sha256": canonical_sha(spec),
        "sdk_version": sdk_version,
        "started_at": started,
        "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "gpu_preflight": {"selected": device, "all_devices": devices},
        "rows": rows,
        "summary": summarize(rows),
    }
    RESULT_PATH.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(document["summary"], indent=2))
    print(f"RESULT: {RESULT_PATH} canonical sha256 {canonical_sha(document)}")


if __name__ == "__main__":
    main()
