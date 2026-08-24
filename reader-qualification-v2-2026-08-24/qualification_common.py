#!/usr/bin/env python3
"""Shared, construct-blind reader-qualification runner for the v2 package."""

from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request

from ainglish import __version__ as sdk_version
from ainglish import panel


ANSWER_CODES = tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ")


def canonical_sha(value: object) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode()).hexdigest()


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.load(response)


def post_json(url: str, value: dict) -> dict:
    request = urllib.request.Request(
        url, data=json.dumps(value).encode(), headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
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


def preflight(spec: dict) -> dict:
    if sdk_version != spec["sdk_version"]:
        raise SystemExit(f"REFUSING: SDK {sdk_version} != frozen {spec['sdk_version']}")
    if panel.ANSWER_PROTOCOL != spec["answer_protocol"]:
        raise SystemExit(
            f"REFUSING: answer protocol {panel.ANSWER_PROTOCOL!r} != frozen "
            f"{spec['answer_protocol']!r}"
        )
    source = Path(panel.__file__).resolve()
    if source != Path(spec["sdk_panel_path"]).resolve():
        raise SystemExit(f"REFUSING: panel source {source} != frozen checkout")
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=source.parents[2], check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    if head != spec["sdk_commit"]:
        raise SystemExit(f"REFUSING: SDK commit {head} != frozen {spec['sdk_commit']}")

    items = spec["items"]
    axes = sorted({item["axis"] for item in items})
    expected_axes = sorted(spec["axes"])
    if axes != expected_axes:
        raise SystemExit(f"REFUSING: item axes {axes} != frozen {expected_axes}")
    per_axis = {axis: sum(item["axis"] == axis for item in items) for axis in axes}
    if any(count != spec["items_per_axis"] for count in per_axis.values()):
        raise SystemExit(f"REFUSING: unbalanced axes {per_axis}")
    ids = [item["id"] for item in items]
    if len(ids) != len(set(ids)):
        raise SystemExit("REFUSING: duplicate item ids")
    forbidden = tuple(term.casefold() for term in spec["forbidden_construct_terms"])
    for item in items:
        serialized = json.dumps(item, ensure_ascii=False).casefold()
        if any(term in serialized for term in forbidden):
            raise SystemExit(f"REFUSING: construct term leaked into {item['id']}")
        options = item["options"]
        if not 2 <= len(options) <= len(ANSWER_CODES) or len(options) != len(set(options)):
            raise SystemExit(f"REFUSING: invalid options in {item['id']}")
        if item["answer"] not in options:
            raise SystemExit(f"REFUSING: answer is not an option in {item['id']}")

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
    resident = get_json(gate["ollama_ps"])
    if resident.get("models"):
        raise SystemExit("REFUSING: shared Ollama already has a resident model")
    panel.prepare_reader_instruments(spec)
    return {"devices": devices, "ollama_ps": resident}


def prompt_for(item: dict) -> tuple[str, dict[str, str]]:
    choice_map = {ANSWER_CODES[index]: option for index, option in enumerate(item["options"])}
    choices = "\n".join(f"{code}: {option}" for code, option in choice_map.items())
    prompt = (
        "Read this message written by one agent to another:\n\n---\n"
        f"{item['message']}\n---\n\nQuestion: {item['question']}\nChoices:\n{choices}\n"
        "Answer with EXACTLY one choice code and nothing else."
    )
    return prompt, choice_map


def unload_model(spec: dict, model: str) -> dict:
    endpoint = spec["gpu_gate"]["ollama_base_url"].rstrip("/")
    response = post_json(endpoint + "/api/generate", {"model": model, "keep_alive": 0})
    after = get_json(endpoint + "/api/ps")
    if any(entry.get("name") == model or entry.get("model") == model for entry in after.get("models", [])):
        raise SystemExit(f"REFUSING: reader {model} did not unload")
    return {"response_done": response.get("done"), "resident_after": after.get("models", [])}


def run(spec_path: Path, result_path: Path) -> None:
    if result_path.exists():
        raise SystemExit(f"REFUSING: {result_path.name} exists; never rerun this frozen screen in place")
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    device = preflight(spec)
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    rows = []
    unloads = []
    for reader in spec["panel"]:
        for item in spec["items"]:
            prompt, choice_map = prompt_for(item)
            raw, truncated = panel.chat(reader, prompt)
            code = raw.strip().upper()
            exact_code = not truncated and code in choice_map and len(code) == 1
            parsed = choice_map.get(code) if exact_code else None
            expected_code = next(key for key, value in choice_map.items() if value == item["answer"])
            rows.append({
                "reader": reader["name"], "lineage": reader["lineage"],
                "model": reader["model"], "model_digest": reader["model_digest"],
                "item_id": item["id"], "axis": item["axis"],
                "expected": item["answer"], "expected_code": expected_code,
                "raw_output": raw, "raw_output_sha256": hashlib.sha256(raw.encode()).hexdigest(),
                "truncated": truncated, "exact_code": exact_code, "parsed_answer": parsed,
                "correct": parsed == item["answer"],
            })
        unloads.append({"reader": reader["name"], **unload_model(spec, reader["model"])})

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
        }
        qualified = (
            observed["exact_code_cells"] == rule["exact_code_cells_required"]
            and observed["correct_cells"] >= rule["correct_cells_required"]
            and all(value >= rule["correct_per_axis_required"] for value in by_axis.values())
        )
        qualification[reader["name"]] = {"observed": observed, "qualified": qualified}
        if qualified:
            roster.append({key: reader[key] for key in (
                "name", "lineage", "provider", "model", "model_digest", "precision",
                "max_tokens", "timeout_s", "temperature", "seed", "api", "base_url",
            )})
    roster_ready = len({reader["lineage"] for reader in roster}) >= rule[
        "minimum_distinct_qualified_lineages"
    ]
    document = {
        "kind": spec["result_kind"], "evidentiary_status": spec["evidentiary_status"],
        "spec_sha256": canonical_sha(spec), "sdk_version": sdk_version,
        "sdk_commit": spec["sdk_commit"], "answer_protocol": panel.ANSWER_PROTOCOL,
        "started_at": started,
        "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "gpu_preflight": device, "unloads": unloads,
        "qualification": qualification, "roster_ready": roster_ready,
        "fixed_roster": roster, "rows": rows,
    }
    result_path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({
        "qualification": qualification, "roster_ready": roster_ready,
        "fixed_roster": [reader["name"] for reader in roster],
        "spec_sha256": document["spec_sha256"], "result_sha256": canonical_sha(document),
    }, indent=2))
