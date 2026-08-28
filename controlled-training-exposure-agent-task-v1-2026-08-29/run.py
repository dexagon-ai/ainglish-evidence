#!/usr/bin/env python3
"""Verify and run the frozen controlled training-exposure study."""

from __future__ import annotations

import argparse
import gc
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
BENCHMARK_ROOT = REPO / "end-to-end-agent-task-benchmark-v0.1-2026-08-28"
LEARNING_ROOT = REPO / "ainglish-learning-program-2026-08-25"
CELLS_PATH = ROOT / "cells.jsonl"
PLAN_PATH = ROOT / "RUN_PLAN.json"
CHECKSUM_PATH = ROOT / "SHA256SUMS.preregistered"
RESULTS_ROOT = ROOT / "results"
RESPONSES_PATH = RESULTS_ROOT / "responses.jsonl"
INFLIGHT_PATH = RESULTS_ROOT / "inflight.json"
BASE_MODEL = "Qwen/Qwen2.5-7B-Instruct"
BASE_REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"
DECODING_SEED = 2026082901
INTERRUPTED = "[INTERRUPTED BEFORE INFERENCE RECEIPT]"
EMPTY = "[EMPTY OUTPUT]"


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def pretty(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("wb") as handle:
        handle.write(pretty(value))
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def append_synced(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as handle:
        handle.write(canonical(value))
        handle.flush()
        os.fsync(handle.fileno())


def jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise RuntimeError(f"{path}:{number}: row is not an object")
            rows.append(value)
    return rows


def load_benchmark():
    path = BENCHMARK_ROOT / "benchmark.py"
    spec = importlib.util.spec_from_file_location("ainglish_agent_task_benchmark", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BENCHMARK = load_benchmark()


def verify_adapter(plan: dict[str, Any]) -> None:
    receipt = json.loads((LEARNING_ROOT / "adapter-artifact-receipt.json").read_text(encoding="utf-8"))
    root = Path(receipt["local_path"])
    if root != Path(plan["adapter_local_path"]) or not root.is_dir():
        raise RuntimeError("frozen adapter directory is missing or moved")
    aggregate = hashlib.sha256()
    actual_paths: set[str] = set()
    for record in receipt["files"]:
        relative = record["path"]
        path = root / relative
        actual_paths.add(relative)
        if path.is_symlink() or not path.is_file():
            raise RuntimeError(f"adapter artifact missing or symlinked: {relative}")
        size = path.stat().st_size
        file_digest = sha256_file(path)
        if size != record["bytes"] or file_digest != record["sha256"]:
            raise RuntimeError(f"adapter artifact drift: {relative}")
        aggregate.update(relative.encode() + b"\0" + str(size).encode() + b"\0" + file_digest.encode() + b"\n")
    current_paths = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
    if current_paths != actual_paths or aggregate.hexdigest() != plan["adapter_directory_sha256"]:
        raise RuntimeError("adapter directory membership or aggregate digest drift")


def verify() -> None:
    if not CHECKSUM_PATH.exists():
        raise RuntimeError("missing preregistered checksum file")
    failures = []
    count = 0
    for line in CHECKSUM_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, relative = line.split("  ", 1)
        path = (ROOT / relative).resolve()
        count += 1
        if not path.exists():
            failures.append(f"missing {relative}")
        elif sha256_file(path) != expected:
            failures.append(f"digest mismatch {relative}")
    if failures:
        raise RuntimeError("preregistered verification failed: " + "; ".join(failures))

    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    if len(jsonl(CELLS_PATH)) != plan["cells_per_condition"]:
        raise RuntimeError("cell count drift")
    verify_adapter(plan)

    status = subprocess.run(
        ["git", "status", "--porcelain", "--", str(ROOT.relative_to(REPO))],
        cwd=REPO, check=True, capture_output=True, text=True,
    ).stdout
    if status.strip():
        raise RuntimeError("study files must be committed before inference")
    commit = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", str(ROOT.relative_to(REPO))],
        cwd=REPO, check=True, capture_output=True, text=True,
    ).stdout.strip()
    if not commit:
        raise RuntimeError("study has no Git commit")
    subprocess.run(["git", "fetch", "origin", "main", "--quiet"], cwd=REPO, check=True)
    public = subprocess.run(["git", "merge-base", "--is-ancestor", commit, "origin/main"], cwd=REPO)
    if public.returncode != 0:
        raise RuntimeError(f"preregistering commit {commit} is not public on origin/main")
    print(json.dumps({"ok": True, "files": count, "cells": plan["cells_per_condition"], "public_commit": commit, "adapter_verified": True}, sort_keys=True))


def strict_decision(raw: str, action_ids: set[str], usage: dict[str, float]) -> tuple[dict[str, Any], str | None]:
    preserved = raw if raw else EMPTY
    try:
        value = json.loads(raw.strip())
        if not isinstance(value, dict):
            raise ValueError("response is not a JSON object")
        if value.get("decision") == "act":
            if set(value) != {"decision", "actions"}:
                raise ValueError("act response has non-exact keys")
            actions = value["actions"]
            if not isinstance(actions, list) or not actions or not all(isinstance(v, str) for v in actions):
                raise ValueError("act response needs a non-empty string list")
            if len(actions) != len(set(actions)) or not set(actions) <= action_ids:
                raise ValueError("act response has duplicate or unknown action")
            return {"decision": "act", "actions": actions, **usage}, None
        if value.get("decision") == "clarify":
            if set(value) != {"decision", "question"} or not isinstance(value["question"], str) or not value["question"].strip():
                raise ValueError("clarify response has invalid schema")
            return {"decision": "clarify", "question": value["question"], **usage}, None
        raise ValueError("decision is neither act nor clarify")
    except (json.JSONDecodeError, ValueError) as exc:
        return {"decision": "invalid", "raw": preserved, **usage}, str(exc)


def load_model(condition: str, device_index: int):
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(
        BASE_MODEL, revision=BASE_REVISION, local_files_only=True, use_fast=True,
    )
    base = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        revision=BASE_REVISION,
        local_files_only=True,
        quantization_config=quantization,
        device_map={"": device_index},
        torch_dtype=torch.bfloat16,
    )
    model = base
    if condition == "adapter":
        adapter = json.loads((LEARNING_ROOT / "adapter-artifact-receipt.json").read_text(encoding="utf-8"))["local_path"]
        model = PeftModel.from_pretrained(base, adapter, local_files_only=True)
    model.eval()
    return model, tokenizer, base


def generate(model, tokenizer, messages: list[dict[str, str]]) -> tuple[str, dict[str, float]]:
    import torch
    from transformers import set_seed

    set_seed(DECODING_SEED)
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    encoded = tokenizer(prompt, return_tensors="pt", add_special_tokens=False).to(model.device)
    started = time.monotonic()
    with torch.inference_mode():
        output = model.generate(
            **encoded,
            max_new_tokens=96,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    elapsed = (time.monotonic() - started) * 1000
    continuation = output[0, encoded["input_ids"].shape[1]:]
    raw = tokenizer.decode(continuation, skip_special_tokens=True)
    return raw, {
        "input_tokens": int(encoded["input_ids"].numel()),
        "output_tokens": int(continuation.numel()),
        "latency_ms": round(elapsed, 3),
    }


def interrupted_record(inflight: dict[str, Any]) -> dict[str, Any]:
    base = {key: inflight[key] for key in (
        "condition", "reader_id", "cell_id", "order", "item_id", "construct", "source_slug",
        "exposure_class", "arm", "track", "prompt_sha256", "clarification_sha256",
    )}
    if inflight["stage"] == "repair":
        return {**base, "first": inflight["first"], "repair": None, "repair_error": INTERRUPTED}
    return {**base, "first": {"decision": "invalid", "raw": INTERRUPTED}, "repair": None, "first_error": INTERRUPTED}


def run(device_index: int, requested: str) -> None:
    verify()
    if INFLIGHT_PATH.exists():
        inflight = json.loads(INFLIGHT_PATH.read_text(encoding="utf-8"))
        append_synced(RESPONSES_PATH, interrupted_record(inflight))
        INFLIGHT_PATH.unlink()
        print(f"materialized interrupted {inflight['condition']} {inflight['cell_id']}", flush=True)

    packet = BENCHMARK.load_tasks()
    items = {item["id"]: item for item in packet["items"]}
    cells = jsonl(CELLS_PATH)
    completed = {(row["condition"], row["cell_id"]) for row in jsonl(RESPONSES_PATH)}
    conditions = ("base", "adapter") if requested == "all" else (requested,)

    for condition in conditions:
        remaining = [cell for cell in cells if (condition, cell["cell_id"]) not in completed]
        if not remaining:
            print(f"condition {condition}: already complete", flush=True)
            continue
        print(f"loading {condition} on cuda:{device_index}; remaining={len(remaining)}", flush=True)
        model, tokenizer, base_model = load_model(condition, device_index)
        reader_id = (
            f"hf/{BASE_MODEL}@{BASE_REVISION}/base" if condition == "base" else
            f"hf/{BASE_MODEL}@{BASE_REVISION}/adapter@{json.loads(PLAN_PATH.read_text())['adapter_directory_sha256']}"
        )
        for index, cell in enumerate(remaining, 1):
            item = items[cell["item_id"]]
            action_ids = {action["id"] for action in item["actions"]}
            common = {key: cell[key] for key in (
                "cell_id", "order", "item_id", "construct", "source_slug", "exposure_class", "arm", "track",
                "prompt_sha256", "clarification_sha256",
            )}
            common.update({"condition": condition, "reader_id": reader_id})
            messages = [{"role": "user", "content": cell["prompt"]}]
            atomic_write(INFLIGHT_PATH, {**common, "stage": "first"})
            try:
                raw, usage = generate(model, tokenizer, messages)
                first, first_error = strict_decision(raw, action_ids, usage)
            except Exception as exc:  # an inference failure is an observed invalid response, never retried
                raw = f"[INFERENCE ERROR {type(exc).__name__}: {exc}]"
                first, first_error = {"decision": "invalid", "raw": raw}, raw
            record: dict[str, Any] = {**common, "first": first, "repair": None}
            if first_error:
                record["first_error"] = first_error
            if first["decision"] == "clarify":
                repair_text = "Clarification from sender: " + cell["clarification"] + "\n\nRespond under the original JSON-only contract."
                repair_messages = [*messages, {"role": "assistant", "content": raw}, {"role": "user", "content": repair_text}]
                atomic_write(INFLIGHT_PATH, {**common, "stage": "repair", "first": first})
                try:
                    repair_raw, repair_usage = generate(model, tokenizer, repair_messages)
                    repair, repair_error = strict_decision(repair_raw, action_ids, repair_usage)
                    if repair["decision"] != "act":
                        repair_error = repair_error or "repair response is not an action"
                        repair = {"decision": "invalid", "raw": repair_raw or EMPTY, **repair_usage}
                    record["repair"] = repair
                    if repair_error:
                        record["repair_error"] = repair_error
                except Exception as exc:
                    record["repair_error"] = f"[INFERENCE ERROR {type(exc).__name__}: {exc}]"
            append_synced(RESPONSES_PATH, record)
            INFLIGHT_PATH.unlink(missing_ok=True)
            completed.add((condition, cell["cell_id"]))
            print(f"{condition} {index:03d}/{len(remaining):03d} {cell['cell_id']} {cell['track']}/{cell['arm']}: {record['first']['decision']}", flush=True)
        del model, base_model, tokenizer
        gc.collect()
        import torch
        torch.cuda.empty_cache()

    actual = jsonl(RESPONSES_PATH)
    print(json.dumps({"status": "complete" if len(actual) == 264 else "partial", "observations": len(actual), "planned": 264}, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("verify")
    execute = sub.add_parser("run")
    execute.add_argument("--device-index", type=int, default=1)
    execute.add_argument("--condition", choices=("base", "adapter", "all"), default="all")
    args = parser.parse_args()
    try:
        if args.command == "verify":
            verify()
        else:
            run(args.device_index, args.condition)
    except Exception as exc:
        print(f"REFUSING: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
