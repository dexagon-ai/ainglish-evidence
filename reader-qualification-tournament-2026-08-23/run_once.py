#!/usr/bin/env python3
"""Run the frozen construct-blind reader qualification tournament once."""

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
SPEC_PATH = ROOT / "spec.json"
RESULT_PATH = ROOT / "result.json"


def canonical_sha(value: object) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode()).hexdigest()


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.load(response)


def gpu_preflight(gate: dict) -> dict:
    rows = []
    command = [
        "nvidia-smi",
        "--query-gpu=index,pci.bus_id,name,memory.used,memory.free,utilization.gpu",
        "--format=csv,noheader,nounits",
    ]
    for line in subprocess.run(command, check=True, capture_output=True, text=True).stdout.splitlines():
        index, pci, name, used, free, utilization = [part.strip() for part in line.split(",", 5)]
        rows.append({
            "index": int(index), "pci_bus_id": pci, "name": name,
            "memory_used_mib": int(used), "memory_free_mib": int(free),
            "utilization_percent": int(utilization),
        })
    selected = next((row for row in rows if row["index"] == gate["index"]), None)
    if selected is None or selected["memory_free_mib"] < gate["minimum_free_mib"]:
        raise SystemExit("REFUSING: the frozen GPU free-VRAM gate is not met")
    shared = get_json(gate["shared_ollama_ps"])
    dedicated = get_json(gate["dedicated_ollama_ps"])
    if shared.get("models") or dedicated.get("models"):
        raise SystemExit("REFUSING: an Ollama endpoint already has a resident model")
    return {"selected": selected, "all_devices": rows}


def prompt_for(item: dict) -> str:
    return (
        "Read this message written by one agent to another:\n\n---\n"
        f"{item['message']}\n---\n\nQuestion: {item['question']}\n"
        "Answer with EXACTLY one of these options and nothing else: "
        + " | ".join(item["options"])
    )


def parse(raw: str, truncated: bool, options: list[str]) -> tuple[str | None, str]:
    if truncated:
        return None, "truncated"
    normalized = raw.strip().casefold()
    if not normalized:
        return None, "empty_stop"
    exact = {option.strip().casefold(): option for option in options}
    if normalized in exact:
        return exact[normalized], "exact_option"
    return normalized[:40], "off_option"


def main() -> None:
    if RESULT_PATH.exists():
        raise SystemExit("REFUSING: result.json exists; never rerun this frozen screen in place")
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    if sdk_version != spec["sdk_version"]:
        raise SystemExit(f"REFUSING: SDK {sdk_version} != frozen {spec['sdk_version']}")
    items = spec["items"]
    if len(items) != 32 or sorted({item["axis"] for item in items}) != [
        "disjunction", "fact_or_choice", "participant_set", "proposal_or_decision",
    ]:
        raise SystemExit("REFUSING: expected four declared eight-item axes")
    if any("we-including-you" in json.dumps(item).casefold() for item in items):
        raise SystemExit("REFUSING: Ainglish construct leaked into the qualification suite")

    device = gpu_preflight(spec["gpu_gate"])
    panel.prepare_reader_instruments(spec)
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    rows = []
    for reader in spec["panel"]:
        for item in items:
            raw, truncated = panel.chat(reader, prompt_for(item))
            answer, state = parse(raw, truncated, item["options"])
            rows.append({
                "reader": reader["name"], "lineage": reader["lineage"],
                "model": reader["model"], "model_digest": reader["model_digest"],
                "item_id": item["id"], "axis": item["axis"],
                "expected": item["answer"], "raw_output": raw,
                "raw_output_sha256": hashlib.sha256(raw.encode()).hexdigest(),
                "truncated": truncated, "parsed_answer": answer, "parse_state": state,
                "correct": answer is not None and answer.casefold() == item["answer"].casefold(),
            })

    rule = spec["selection_rule"]
    qualification = {}
    roster = []
    for reader in spec["panel"]:
        own = [row for row in rows if row["reader"] == reader["name"]]
        by_axis = {
            axis: sum(row["correct"] for row in own if row["axis"] == axis)
            for axis in sorted({row["axis"] for row in own})
        }
        observed = {
            "exact_option_cells": sum(row["parse_state"] == "exact_option" for row in own),
            "correct_cells": sum(row["correct"] for row in own),
            "correct_by_axis": by_axis,
        }
        qualified = (
            observed["exact_option_cells"] == rule["exact_option_cells_required"]
            and observed["correct_cells"] >= rule["correct_cells_required"]
            and all(value >= rule["correct_per_axis_required"] for value in by_axis.values())
        )
        qualification[reader["name"]] = {"observed": observed, "qualified": qualified}
        if qualified:
            roster.append({
                key: reader[key] for key in (
                    "name", "lineage", "provider", "model", "model_digest", "precision",
                    "max_tokens", "timeout_s", "temperature", "seed", "api", "base_url",
                )
            })

    roster_ready = len({reader["lineage"] for reader in roster}) >= rule[
        "minimum_distinct_qualified_lineages"
    ]
    document = {
        "kind": "ainglish.panel.reader-qualification-tournament-result.v1",
        "evidentiary_status": spec["evidentiary_status"],
        "spec_sha256": canonical_sha(spec), "sdk_version": sdk_version,
        "started_at": started,
        "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "gpu_preflight": device, "qualification": qualification,
        "roster_ready": roster_ready, "fixed_roster": roster, "rows": rows,
    }
    RESULT_PATH.write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8",
    )
    print(json.dumps({
        "qualification": qualification, "roster_ready": roster_ready,
        "fixed_roster": [reader["name"] for reader in roster],
        "spec_sha256": document["spec_sha256"], "result_sha256": canonical_sha(document),
    }, indent=2))


if __name__ == "__main__":
    main()
