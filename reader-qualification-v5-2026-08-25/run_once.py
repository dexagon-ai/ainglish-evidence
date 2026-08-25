#!/usr/bin/env python3
"""Run the frozen v5 holdout exactly once and retain all outcomes."""

from __future__ import annotations

import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request


ROOT = Path(__file__).resolve().parent
CODES = tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def get(path: str) -> dict:
    with urllib.request.urlopen("http://127.0.0.1:11434" + path, timeout=30) as response:
        return json.load(response)


def post(path: str, payload: dict, timeout: int = 240) -> dict:
    req = urllib.request.Request(
        "http://127.0.0.1:11434" + path, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)


def gpu_rows() -> list[dict]:
    out = subprocess.run([
        "nvidia-smi", "--query-gpu=index,name,memory.free,utilization.gpu",
        "--format=csv,noheader,nounits",
    ], check=True, capture_output=True, text=True).stdout
    rows = []
    for line in out.splitlines():
        index, name, free, utilization = [part.strip() for part in line.split(",", 3)]
        rows.append({"index": int(index), "name": name, "free_mib": int(free), "utilization": int(utilization)})
    return rows


def validate(spec: dict) -> dict:
    sealed = dict(spec)
    expected = sealed.pop("content_sha256")
    if hashlib.sha256(canonical(sealed)).hexdigest() != expected:
        raise SystemExit("REFUSING: holdout digest drift")
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
            raise SystemExit(f"REFUSING: invalid answers in {row['id']}")
    old = set()
    for path in spec["disjoint_from_specs"]:
        prior = json.loads(Path(path).read_text(encoding="utf-8"))
        for row in prior.get("items", []):
            old.add(hashlib.sha256(canonical({key: row[key] for key in ("message", "question", "options")})).hexdigest())
    new = {
        hashlib.sha256(canonical({key: row[key] for key in ("message", "question", "options")})).hexdigest()
        for row in spec["items"]
    }
    if old & new:
        raise SystemExit("REFUSING: holdout overlaps a burned item")
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
        if tags.get(reader["model"]) != reader["model_digest"].removeprefix("sha256:"):
            raise SystemExit(f"REFUSING: model drift for {reader['name']}")
    return {"devices": devices, "resident_before": []}


def prompt(row: dict) -> tuple[str, dict[str, str]]:
    mapping = {CODES[index]: value for index, value in enumerate(row["options"])}
    choices = "\n".join(f"{code}: {value}" for code, value in mapping.items())
    return (
        "Read this ordinary-English message literally.\n\n---\n" + row["message"] +
        "\n---\n\nQuestion: " + row["question"] + "\nChoices:\n" + choices +
        "\nAnswer with EXACTLY one choice code and nothing else.", mapping,
    )


def main() -> None:
    result_path = ROOT / "result.json"
    if result_path.exists():
        raise SystemExit("REFUSING: result exists; never rerun")
    spec = json.loads((ROOT / "holdout.json").read_text(encoding="utf-8"))
    preflight = validate(spec)
    rows = []
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    for reader in spec["panel"]:
        for item in spec["items"]:
            text, mapping = prompt(item)
            response = post("/api/chat", {
                "model": reader["model"], "messages": [{"role": "user", "content": text}],
                "think": False, "stream": False, "keep_alive": -1,
                "options": {"temperature": 0, "seed": reader["seed"], "num_predict": reader["max_tokens"], "num_ctx": 4096},
            }, timeout=reader["timeout_s"])
            raw = ((response.get("message") or {}).get("content") or "")
            thinking = ((response.get("message") or {}).get("thinking") or "")
            code = raw.strip().upper()
            exact = len(code) == 1 and code in mapping
            parsed = mapping.get(code) if exact else None
            rows.append({
                "reader": reader["name"], "lineage": reader["lineage"], "model": reader["model"],
                "model_digest": reader["model_digest"], "item_id": item["id"], "axis": item["axis"],
                "expected": item["answer"], "raw_output": raw,
                "raw_output_sha256": hashlib.sha256(raw.encode()).hexdigest(),
                "thinking_bytes": len(thinking.encode()), "exact_code": exact,
                "parsed_answer": parsed, "correct": parsed == item["answer"],
            })
        post("/api/generate", {"model": reader["model"], "prompt": "", "stream": False, "keep_alive": 0})
        if get("/api/ps").get("models"):
            raise SystemExit(f"REFUSING: {reader['model']} did not unload")
        print(f"completed {reader['name']}", flush=True)
    rule = spec["selection_rule"]
    qualification = {}
    roster = []
    for reader in spec["panel"]:
        own = [row for row in rows if row["reader"] == reader["name"]]
        by_axis = {axis: sum(row["correct"] for row in own if row["axis"] == axis) for axis in spec["axes"]}
        observed = {
            "exact_code_cells": sum(row["exact_code"] for row in own),
            "correct_cells": sum(row["correct"] for row in own), "correct_by_axis": by_axis,
            "thinking_bytes": sum(row["thinking_bytes"] for row in own),
        }
        qualified = (
            observed["exact_code_cells"] == rule["exact_code_cells_required"] and
            observed["correct_cells"] >= rule["correct_cells_required"] and
            all(value >= rule["correct_per_axis_required"] for value in by_axis.values()) and
            observed["thinking_bytes"] == 0
        )
        qualification[reader["name"]] = {"observed": observed, "qualified": qualified}
        if qualified:
            roster.append(reader)
    ready = len({row["lineage"] for row in roster}) >= rule["minimum_distinct_qualified_lineages"]
    result = {
        "kind": spec["result_kind"], "evidentiary_status": spec["evidentiary_status"],
        "spec_sha256": spec["content_sha256"], "started_at": started,
        "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "gpu_preflight": preflight, "qualification": qualification, "roster_ready": ready,
        "fixed_roster": roster, "rows": rows,
    }
    result["content_sha256"] = hashlib.sha256(canonical(result)).hexdigest()
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"qualification": qualification, "roster_ready": ready, "fixed_roster": [r["name"] for r in roster], "sha256": result["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()

