#!/usr/bin/env python3
"""One-shot construct-blind qualification runner over Ollama native chat."""

from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request


ANSWER_CODES = tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ")


def canonical_sha(value: object) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode()).hexdigest()


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.load(response)


def post_json(url: str, value: dict, timeout: int = 120) -> dict:
    request = urllib.request.Request(
        url, data=json.dumps(value).encode(), headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def gpu_snapshot() -> list[dict]:
    command = [
        "nvidia-smi",
        "--query-gpu=index,pci.bus_id,name,memory.used,memory.free,utilization.gpu",
        "--format=csv,noheader,nounits",
    ]
    rows = []
    output = subprocess.run(command, check=True, capture_output=True, text=True).stdout
    for line in output.splitlines():
        index, pci, name, used, free, utilization = [part.strip() for part in line.split(",", 5)]
        rows.append({
            "index": int(index), "pci_bus_id": pci, "name": name,
            "memory_used_mib": int(used), "memory_free_mib": int(free),
            "utilization_percent": int(utilization),
        })
    return rows


def prompt_for(item: dict) -> tuple[str, dict[str, str]]:
    choice_map = {ANSWER_CODES[index]: option for index, option in enumerate(item["options"])}
    choices = "\n".join(f"{code}: {option}" for code, option in choice_map.items())
    prompt = (
        "Read this message written by one agent to another:\n\n---\n"
        f"{item['message']}\n---\n\nQuestion: {item['question']}\nChoices:\n{choices}\n"
        "Answer with EXACTLY one choice code and nothing else."
    )
    return prompt, choice_map


def validate(spec: dict) -> dict:
    if spec.get("answer_protocol") != "opaque-choice-v1":
        raise SystemExit("REFUSING: answer protocol is not opaque-choice-v1")
    if spec.get("transport") != {"adapter": "ollama-native-chat-v1", "think": False}:
        raise SystemExit("REFUSING: native transport declaration drifted")
    items = spec["items"]
    axes = sorted({item["axis"] for item in items})
    if axes != sorted(spec["axes"]):
        raise SystemExit("REFUSING: axes drifted")
    counts = {axis: sum(item["axis"] == axis for item in items) for axis in axes}
    if any(value != spec["items_per_axis"] for value in counts.values()):
        raise SystemExit(f"REFUSING: unbalanced axes {counts}")
    if len({item["id"] for item in items}) != len(items):
        raise SystemExit("REFUSING: duplicate item ids")
    forbidden = tuple(term.casefold() for term in spec["forbidden_construct_terms"])
    for item in items:
        if any(term in json.dumps(item, ensure_ascii=False).casefold() for term in forbidden):
            raise SystemExit(f"REFUSING: construct term leaked into {item['id']}")
        if item["answer"] not in item["options"] or len(set(item["options"])) != len(item["options"]):
            raise SystemExit(f"REFUSING: invalid choices in {item['id']}")
    old_specs = [json.loads(Path(path).read_text()) for path in spec["disjoint_from_specs"]]
    old_rows = {
        canonical_sha({key: item[key] for key in ("message", "question", "options")})
        for old in old_specs for item in old["items"]
    }
    new_rows = {
        canonical_sha({key: item[key] for key in ("message", "question", "options")})
        for item in items
    }
    if old_rows & new_rows:
        raise SystemExit("REFUSING: an item duplicates a burned or development control")
    devices = gpu_snapshot()
    gate = spec["gpu_gate"]
    if sum(row["memory_free_mib"] for row in devices) < gate["minimum_total_free_mib"]:
        raise SystemExit("REFUSING: total free-VRAM gate is not met")
    if max(row["utilization_percent"] for row in devices) > gate["maximum_utilization_percent"]:
        raise SystemExit("REFUSING: GPU utilization gate is not met")
    endpoint = gate["ollama_base_url"].rstrip("/")
    if get_json(endpoint + "/api/ps").get("models"):
        raise SystemExit("REFUSING: Ollama already has a resident model")
    tags = get_json(endpoint + "/api/tags").get("models", [])
    digests = {entry.get("name"): entry.get("digest") for entry in tags}
    for reader in spec["panel"]:
        observed = digests.get(reader["model"])
        if observed != reader["model_digest"].removeprefix("sha256:"):
            raise SystemExit(f"REFUSING: model digest mismatch for {reader['name']}")
    return {"devices": devices, "resident_before": []}


def run(spec_path: Path, result_path: Path) -> None:
    if result_path.exists():
        raise SystemExit(f"REFUSING: {result_path.name} exists; never rerun this screen")
    spec = json.loads(spec_path.read_text())
    preflight = validate(spec)
    endpoint = spec["gpu_gate"]["ollama_base_url"].rstrip("/")
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    rows = []
    unloads = []
    for reader in spec["panel"]:
        for item in spec["items"]:
            prompt, choice_map = prompt_for(item)
            response = post_json(endpoint + "/api/chat", {
                "model": reader["model"],
                "messages": [{"role": "user", "content": prompt}],
                "think": False,
                "stream": False,
                "options": {
                    "temperature": reader["temperature"],
                    "seed": reader["seed"],
                    "num_predict": reader["max_tokens"],
                    "num_ctx": 4096,
                },
                "keep_alive": -1,
            }, timeout=reader["timeout_s"])
            raw = (response.get("message") or {}).get("content") or ""
            thinking = (response.get("message") or {}).get("thinking") or ""
            code = raw.strip().upper()
            exact = code in choice_map and len(code) == 1
            parsed = choice_map.get(code) if exact else None
            expected_code = next(key for key, value in choice_map.items() if value == item["answer"])
            rows.append({
                "reader": reader["name"], "lineage": reader["lineage"],
                "model": reader["model"], "model_digest": reader["model_digest"],
                "item_id": item["id"], "axis": item["axis"],
                "expected": item["answer"], "expected_code": expected_code,
                "raw_output": raw, "raw_output_sha256": hashlib.sha256(raw.encode()).hexdigest(),
                "thinking_bytes": len(thinking.encode()),
                "done_reason": response.get("done_reason"),
                "exact_code": exact, "parsed_answer": parsed,
                "correct": parsed == item["answer"],
            })
        post_json(endpoint + "/api/generate", {
            "model": reader["model"], "prompt": "", "keep_alive": 0, "stream": False,
        })
        resident = get_json(endpoint + "/api/ps").get("models", [])
        if resident:
            raise SystemExit(f"REFUSING: reader {reader['model']} did not unload")
        unloads.append({"reader": reader["name"], "resident_after": resident})
    qualification = {}
    roster = []
    rule = spec["selection_rule"]
    for reader in spec["panel"]:
        own = [row for row in rows if row["reader"] == reader["name"]]
        by_axis = {
            axis: sum(row["correct"] for row in own if row["axis"] == axis)
            for axis in spec["axes"]
        }
        observed = {
            "exact_code_cells": sum(row["exact_code"] for row in own),
            "correct_cells": sum(row["correct"] for row in own),
            "correct_by_axis": by_axis,
            "thinking_bytes": sum(row["thinking_bytes"] for row in own),
        }
        qualified = (
            observed["exact_code_cells"] == rule["exact_code_cells_required"]
            and observed["correct_cells"] >= rule["correct_cells_required"]
            and all(value >= rule["correct_per_axis_required"] for value in by_axis.values())
            and observed["thinking_bytes"] == 0
        )
        qualification[reader["name"]] = {"observed": observed, "qualified": qualified}
        if qualified:
            roster.append(reader)
    roster_ready = len({reader["lineage"] for reader in roster}) >= rule[
        "minimum_distinct_qualified_lineages"
    ]
    document = {
        "kind": spec["result_kind"],
        "evidentiary_status": spec["evidentiary_status"],
        "spec_sha256": canonical_sha(spec),
        "answer_protocol": spec["answer_protocol"],
        "transport": spec["transport"],
        "started_at": started,
        "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "gpu_preflight": preflight,
        "unloads": unloads,
        "qualification": qualification,
        "roster_ready": roster_ready,
        "fixed_roster": roster,
        "rows": rows,
    }
    result_path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({
        "qualification": qualification,
        "roster_ready": roster_ready,
        "fixed_roster": [reader["name"] for reader in roster],
        "spec_sha256": document["spec_sha256"],
        "result_sha256": canonical_sha(document),
    }, indent=2))
