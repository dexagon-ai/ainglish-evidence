#!/usr/bin/env python3
"""One-shot, GPU-only reader screen on already exposed generic controls."""

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
SPEC_PATH = ROOT / "screen-spec.json"
RESULT_PATH = ROOT / "screen-results.json"


def canonical_sha(value: object) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(data).hexdigest()


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.load(response)


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
    exact = {str(option).strip().casefold(): str(option) for option in options}
    return (exact[normalized], "exact_option") if normalized in exact else (normalized[:40], "off_option")


def gpu_preflight(gate: dict) -> dict:
    command = [
        "nvidia-smi",
        "--query-gpu=index,pci.bus_id,name,memory.used,memory.free,utilization.gpu",
        "--format=csv,noheader,nounits",
    ]
    lines = subprocess.run(command, check=True, capture_output=True, text=True).stdout.splitlines()
    rows = []
    for line in lines:
        index, pci, name, used, free, utilization = [part.strip() for part in line.split(",", 5)]
        rows.append({"index": int(index), "pci_bus_id": pci, "name": name,
                     "memory_used_mib": int(used), "memory_free_mib": int(free),
                     "utilization_percent": int(utilization)})
    selected = next((row for row in rows if row["index"] == gate["index"]), None)
    if selected is None or selected["memory_free_mib"] < gate["minimum_free_mib"]:
        raise SystemExit("REFUSING: GPU 0 does not meet the frozen free-VRAM gate")
    if get_json(gate["shared_ollama_ps"]).get("models") or get_json(gate["dedicated_ollama_ps"]).get("models"):
        raise SystemExit("REFUSING: an Ollama endpoint already has a resident model")
    return {"selected": selected, "all_devices": rows}


def main() -> None:
    if RESULT_PATH.exists():
        raise SystemExit("REFUSING: screen-results.json exists; do not rerun the screen in place")
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    if sdk_version != spec["sdk_version"]:
        raise SystemExit(f"REFUSING: SDK {sdk_version} != frozen {spec['sdk_version']}")
    source_path = (ROOT / spec["items_source"]).resolve()
    source = json.loads(source_path.read_text(encoding="utf-8"))
    items = source["items"]
    if len(items) != 6 or any(not item["id"].startswith("dexagon-count-calibration-") for item in items):
        raise SystemExit("REFUSING: development source is not the six exposed generic controls")
    if any(token in json.dumps(items, ensure_ascii=False) for token in ("each-alone", "as-one", "rosetta-amount")):
        raise SystemExit("REFUSING: scientific content leaked into the reader screen")

    device = gpu_preflight(spec["gpu_gate"])
    rows = []
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    for reader in spec["panel"]:
        for item in items:
            for arm in ("english", "ainglish"):
                prompt = prompt_for(item[arm], item["question"], item["options"])
                raw, truncated = panel.chat(reader, prompt)
                answer, state = parse(raw, truncated, item["options"])
                rows.append({
                    "reader": reader["name"], "model": reader["model"], "item_id": item["id"],
                    "arm": arm, "expected": item["answer"], "raw_output": raw,
                    "raw_output_sha256": hashlib.sha256(raw.encode()).hexdigest(),
                    "truncated": truncated, "parsed_answer": answer, "parse_state": state,
                    "correct": answer is not None and answer.casefold() == item["answer"].casefold(),
                })

    qualification = {}
    for reader in spec["panel"]:
        name = reader["name"]
        own = [row for row in rows if row["reader"] == name]
        explicit = [row for row in own if row["arm"] == "ainglish"]
        one = [row for row in explicit if row["expected"] == "one"]
        three = [row for row in explicit if row["expected"] == "three"]
        observed = {
            "live_exact_cells": sum(row["parse_state"] == "exact_option" for row in own),
            "explicit_arm_correct": sum(row["correct"] for row in explicit),
            "explicit_one_correct": sum(row["correct"] for row in one),
            "explicit_three_correct": sum(row["correct"] for row in three),
        }
        qualification[name] = {
            "observed": observed,
            "qualified": all(observed[key] == spec["qualification"][key] for key in observed),
        }

    document = {
        "kind": "ainglish.panel.reader-development-screen-result.v1",
        "evidentiary_status": "development-only; not proposal evidence",
        "spec_sha256": canonical_sha(spec), "sdk_version": sdk_version,
        "started_at": started,
        "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "gpu_preflight": device, "rows": rows, "qualification": qualification,
    }
    RESULT_PATH.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(qualification, indent=2))
    print(f"RESULT: {RESULT_PATH} canonical sha256 {canonical_sha(document)}")


if __name__ == "__main__":
    main()
