#!/usr/bin/env python3
"""Run one frozen v6 tranche exactly once and retain every outcome."""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
PHASES = ("phase-a", "reserve-b", "final-reserve")
SPEC_FILES = {
    "phase-a": "phase-a-holdout.json",
    "reserve-b": "reserve-b-holdout.json",
    "final-reserve": "final-reserve-holdout.json",
}
RESULT_FILES = {
    "phase-a": "phase-a-result.json",
    "reserve-b": "reserve-b-result.json",
    "final-reserve": "final-reserve-result.json",
}
CODES = tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    sealed = dict(value)
    expected = sealed.pop("content_sha256")
    if hashlib.sha256(canonical(sealed)).hexdigest() != expected:
        raise SystemExit(f"REFUSING: digest drift in {path.name}")
    return value


def get(path: str) -> dict:
    with urllib.request.urlopen("http://127.0.0.1:11434" + path, timeout=30) as response:
        return json.load(response)


def post(path: str, payload: dict, timeout: int = 360) -> dict:
    request = urllib.request.Request(
        "http://127.0.0.1:11434" + path,
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


def item_fingerprint(row: dict) -> str:
    return hashlib.sha256(canonical({
        "message": row["message"],
        "question": row["question"],
        "options": sorted(row["options"]),
    })).hexdigest()


def journal_write(handle, value: dict) -> None:
    handle.write(json.dumps(value, sort_keys=True, ensure_ascii=False) + "\n")
    handle.flush()
    os.fsync(handle.fileno())


def validate(spec: dict, plan: dict) -> dict:
    if spec["plan_sha256"] != plan["content_sha256"] or spec["items"] != plan["items"]:
        raise SystemExit("REFUSING: phase does not bind the frozen plan and exact item order")
    if len(spec["items"]) != 64 or len({row["id"] for row in spec["items"]}) != 64:
        raise SystemExit("REFUSING: item count or identity drift")
    counts = {axis: sum(row["axis"] == axis for row in spec["items"]) for axis in spec["axes"]}
    if any(value != 8 for value in counts.values()):
        raise SystemExit(f"REFUSING: axis imbalance {counts}")
    forbidden = [term.casefold() for term in spec["forbidden_construct_terms"]]
    for row in spec["items"]:
        if any(term in json.dumps(row, ensure_ascii=False).casefold() for term in forbidden):
            raise SystemExit(f"REFUSING: construct leak in {row['id']}")
        if row["answer"] not in row["options"] or len(row["options"]) != len(set(row["options"])):
            raise SystemExit(f"REFUSING: invalid choices in {row['id']}")
    prior = set()
    for relative in spec["disjoint_from_specs"]:
        data = json.loads((REPO / relative).read_text(encoding="utf-8"))
        for row in data.get("items", []):
            if all(key in row for key in ("message", "question", "options")):
                prior.add(item_fingerprint(row))
    if prior & {item_fingerprint(row) for row in spec["items"]}:
        raise SystemExit("REFUSING: holdout overlaps a burned qualification item")
    source_results = []
    prior_roster = []
    for receipt in spec["source_results"]:
        result = checked(ROOT / receipt["file"])
        if result["content_sha256"] != receipt["content_sha256"]:
            raise SystemExit(f"REFUSING: source result drift in {receipt['file']}")
        source_results.append(result)
        prior_roster.extend(result.get("fixed_roster", []))
    if prior_roster != spec["prior_qualified_readers"]:
        raise SystemExit("REFUSING: prior qualified-reader projection drift")
    devices = gpu_rows()
    gate = spec["gpu_gate"]
    if sum(row["free_mib"] for row in devices) < gate["minimum_total_free_mib"]:
        raise SystemExit("REFUSING: free-VRAM gate")
    if max(row["utilization"] for row in devices) > gate["maximum_utilization_percent"]:
        raise SystemExit("REFUSING: utilization gate")
    if get("/api/ps").get("models"):
        raise SystemExit("REFUSING: resident Ollama model")
    tags = {row["name"]: row["digest"] for row in get("/api/tags").get("models", [])}
    for reader in spec["panel"]:
        if tags.get(reader["source_model"]) != reader["source_manifest_sha256"]:
            raise SystemExit(f"REFUSING: source model drift for {reader['name']}")
        if tags.get(reader["model"]) != reader["model_digest"].removeprefix("sha256:"):
            raise SystemExit(f"REFUSING: wrapper model drift for {reader['name']}")
    return {"devices": devices, "resident_before": [], "source_result_count": len(source_results)}


def prompt(row: dict) -> tuple[str, dict[str, str]]:
    mapping = {CODES[index]: value for index, value in enumerate(row["options"])}
    choices = "\n".join(f"{code}: {value}" for code, value in mapping.items())
    return (
        "Read this ordinary-English message literally.\n\n---\n" + row["message"] +
        "\n---\n\nQuestion: " + row["question"] + "\nChoices:\n" + choices +
        "\nAnswer with EXACTLY one choice code and nothing else.",
        mapping,
    )


def fault_label(exc: Exception) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        return f"http_{exc.code}"
    if isinstance(exc, urllib.error.URLError):
        return "url_error"
    if isinstance(exc, TimeoutError):
        return "timeout"
    return type(exc).__name__


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", required=True, choices=PHASES)
    args = parser.parse_args()
    result_path = ROOT / RESULT_FILES[args.phase]
    if result_path.exists():
        raise SystemExit("REFUSING: result exists; never rerun")
    journal_path = ROOT / f"{args.phase}-attempt-journal.jsonl"
    if journal_path.exists():
        raise SystemExit("REFUSING: attempt journal exists; never repeat burned cells")
    plan = checked(ROOT / "plan.json")
    spec = checked(ROOT / SPEC_FILES[args.phase])
    preflight = validate(spec, plan)
    rows = []
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with journal_path.open("x", encoding="utf-8") as journal:
        journal_write(journal, {
            "event": "phase_started",
            "phase": args.phase,
            "plan_sha256": plan["content_sha256"],
            "spec_sha256": spec["content_sha256"],
            "started_at": started,
        })
        ordinal = 0
        for reader in spec["panel"]:
            for item in spec["items"]:
                ordinal += 1
                text, mapping = prompt(item)
                journal_write(journal, {
                    "event": "cell_attempted",
                    "ordinal": ordinal,
                    "reader": reader["name"],
                    "item_id": item["id"],
                })
                response = {}
                fault = None
                try:
                    response = post("/api/chat", {
                        "model": reader["model"],
                        "messages": [{"role": "user", "content": text}],
                        "think": False,
                        "stream": False,
                        "keep_alive": -1,
                        "options": {
                            "temperature": reader["temperature"],
                            "seed": reader["seed"],
                            "num_predict": reader["max_tokens"],
                            "num_ctx": reader["num_ctx"],
                        },
                    }, timeout=reader["timeout_s"])
                except Exception as exc:  # retain an adverse cell; never retry a burned reader/item
                    fault = fault_label(exc)
                raw = ((response.get("message") or {}).get("content") or "")
                thinking = ((response.get("message") or {}).get("thinking") or "")
                code = raw.strip().upper()
                exact = len(code) == 1 and code in mapping
                parsed = mapping.get(code) if exact else None
                row = {
                    "reader": reader["name"],
                    "lineage": reader["lineage"],
                    "model": reader["model"],
                    "model_digest": reader["model_digest"],
                    "item_id": item["id"],
                    "axis": item["axis"],
                    "expected": item["answer"],
                    "raw_output": raw,
                    "raw_output_sha256": hashlib.sha256(raw.encode()).hexdigest(),
                    "thinking_bytes": len(thinking.encode()),
                    "fault": fault,
                    "exact_code": exact,
                    "parsed_answer": parsed,
                    "correct": parsed == item["answer"],
                    "timing": {key: response.get(key) for key in ("total_duration", "load_duration", "prompt_eval_count", "eval_count")},
                }
                rows.append(row)
                journal_write(journal, {"event": "cell_recorded", "ordinal": ordinal, "row": row})
            post("/api/generate", {"model": reader["model"], "prompt": "", "stream": False, "keep_alive": 0})
            if get("/api/ps").get("models"):
                raise SystemExit(f"REFUSING: {reader['model']} did not unload")
            journal_write(journal, {"event": "reader_completed", "reader": reader["name"]})
            print(f"completed {reader['name']}", flush=True)
        journal_write(journal, {"event": "phase_completed", "cells": len(rows)})
    journal_sha256 = hashlib.sha256(journal_path.read_bytes()).hexdigest()
    rule = spec["selection_rule"]
    qualification = {}
    current_roster = []
    for reader in spec["panel"]:
        own = [row for row in rows if row["reader"] == reader["name"]]
        by_axis = {axis: sum(row["correct"] for row in own if row["axis"] == axis) for axis in spec["axes"]}
        observed = {
            "exact_code_cells": sum(row["exact_code"] for row in own),
            "correct_cells": sum(row["correct"] for row in own),
            "correct_by_axis": by_axis,
            "thinking_bytes": sum(row["thinking_bytes"] for row in own),
            "fault_cells": sum(row["fault"] is not None for row in own),
        }
        qualified = (
            observed["exact_code_cells"] == rule["exact_code_cells_required"]
            and observed["correct_cells"] >= rule["correct_cells_required"]
            and all(value >= rule["correct_per_axis_required"] for value in by_axis.values())
            and observed["thinking_bytes"] == rule["thinking_bytes_required"]
            and observed["fault_cells"] == 0
        )
        qualification[reader["name"]] = {"observed": observed, "qualified": qualified}
        if qualified:
            current_roster.append(reader)
    accumulated = [*spec["prior_qualified_readers"], *current_roster]
    names = [row["name"] for row in accumulated]
    if len(names) != len(set(names)):
        raise SystemExit("REFUSING: accumulated roster repeats a reader")
    ready = len({row["lineage"] for row in accumulated}) >= rule["minimum_distinct_qualified_lineages"]
    result = {
        "kind": spec["result_kind"],
        "evidentiary_status": spec["evidentiary_status"],
        "plan_sha256": plan["content_sha256"],
        "spec_sha256": spec["content_sha256"],
        "phase": args.phase,
        "started_at": started,
        "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "gpu_preflight": preflight,
        "attempt_journal": {"file": journal_path.name, "sha256": journal_sha256},
        "qualification": qualification,
        "roster_ready": ready,
        "fixed_roster": current_roster,
        "accumulated_fixed_roster": accumulated,
        "rows": rows,
    }
    result["content_sha256"] = hashlib.sha256(canonical(result)).hexdigest()
    with result_path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({
        "phase": args.phase,
        "qualification": qualification,
        "roster_ready": ready,
        "fixed_roster": [row["name"] for row in accumulated],
        "sha256": result["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
