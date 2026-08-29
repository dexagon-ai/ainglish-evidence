#!/usr/bin/env python3
"""Evaluate one frozen base/adapter condition once with strict per-cell receipts."""

from __future__ import annotations

import argparse
import gc
import json
import os
import time
from pathlib import Path
from typing import Any

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

from integrity import ROOT, jsonl, pretty, require_public_file, validate_artifact, verify_preregistered


RESULTS = ROOT / "results"


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("wb") as handle:
        handle.write(pretty(value))
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def append_many(path: Path, rows: list[dict[str, Any]]) -> None:
    from integrity import canonical

    with path.open("ab") as handle:
        for row in rows:
            handle.write(canonical(row))
        handle.flush()
        os.fsync(handle.fileno())


def parse(raw: str, labels: set[str]) -> tuple[str | None, str | None]:
    try:
        value = json.loads(raw.strip())
        if not isinstance(value, dict) or set(value) != {"answer"} or value["answer"] not in labels:
            raise ValueError("response is not the exact one-key answer object or label is unknown")
        return value["answer"], None
    except (json.JSONDecodeError, ValueError) as exc:
        return None, str(exc)


def artifact_packet() -> tuple[dict[str, Any], str]:
    commit = require_public_file("adapter-receipts.json")
    packet = json.loads((ROOT / "adapter-receipts.json").read_text(encoding="utf-8"))
    if packet.get("schema") != "ainglish.crossover-adapter-receipts.v1" or len(packet.get("adapters", [])) != 2:
        raise RuntimeError("adapter receipt packet malformed")
    for row in packet["adapters"]:
        validate_artifact(Path(row["directory"]), row["manifest"])
    return packet, commit


def load(condition: str, plan: dict[str, Any], adapters: dict[str, dict[str, Any]]):
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    quantization = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
    tokenizer = AutoTokenizer.from_pretrained(plan["base_model"], revision=plan["base_revision"], local_files_only=True, use_fast=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"
    base = AutoModelForCausalLM.from_pretrained(
        plan["base_model"], revision=plan["base_revision"], local_files_only=True,
        quantization_config=quantization, device_map={"": 0}, torch_dtype=torch.bfloat16,
    )
    model = base
    model_id = f"hf/{plan['base_model']}@{plan['base_revision']}/base"
    if condition != "base":
        group = condition[-1]
        row = adapters[group]
        model = PeftModel.from_pretrained(base, row["directory"], local_files_only=True)
        model_id = f"hf/{plan['base_model']}@{plan['base_revision']}/adapter-{group}@{row['manifest']['aggregate_sha256']}"
    model.eval()
    return model, tokenizer, base, model_id


def invalid_rows(inflight: dict[str, Any], reason: str) -> list[dict[str, Any]]:
    return [{
        "condition": inflight["condition"], "reader_id": inflight["reader_id"], "batch": inflight["batch"],
        "id": row["id"], "key": row["key"], "arm": row["condition"], "expected": row["expected"],
        "observed": None, "valid": False, "raw": "", "error": reason,
        "input_tokens": None, "output_tokens": None, "batch_latency_ms": None,
    } for row in inflight["rows"]]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--condition", choices=("base", "adapter-a", "adapter-b"), required=True)
    args = parser.parse_args()
    visible = os.environ.get("CUDA_VISIBLE_DEVICES")
    if visible not in {"0", "1"}:
        raise SystemExit("REFUSING: expose exactly one physical GPU with CUDA_VISIBLE_DEVICES=0 or 1")
    prereg_commit = verify_preregistered()
    packet, adapter_commit = artifact_packet()
    adapters = {row["group"]: row for row in packet["adapters"]}
    plan = json.loads((ROOT / "RUN_PLAN.json").read_text(encoding="utf-8"))
    eval_rows = jsonl(ROOT / "eval.jsonl")
    if len(eval_rows) != plan["evaluation"]["prompts_per_condition"]:
        raise SystemExit("REFUSING: evaluation population drift")
    RESULTS.mkdir(parents=True, exist_ok=True)
    journal = RESULTS / f"{args.condition}.jsonl"
    inflight_path = RESULTS / f"{args.condition}.inflight.json"
    if inflight_path.exists():
        inflight = json.loads(inflight_path.read_text(encoding="utf-8"))
        append_many(journal, invalid_rows(inflight, "interrupted before inference receipt"))
        inflight_path.unlink()
    completed = {row["id"] for row in jsonl(journal)}
    remaining = [row for row in eval_rows if row["id"] not in completed]
    if not remaining:
        print(json.dumps({"condition": args.condition, "status": "already-complete", "rows": len(completed)}))
        return

    import torch
    from transformers import set_seed

    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise SystemExit("REFUSING: evaluation process must see exactly one CUDA device")
    model, tokenizer, base, model_id = load(args.condition, plan, adapters)
    set_seed(plan["evaluation"]["seed"])
    batch_size = plan["evaluation"]["batch_size"]
    for offset in range(0, len(remaining), batch_size):
        batch_rows = remaining[offset:offset + batch_size]
        batch_number = offset // batch_size + 1
        inflight = {
            "condition": args.condition, "reader_id": model_id, "batch": batch_number,
            "rows": [{key: row[key] for key in ("id", "key", "condition", "expected")} for row in batch_rows],
        }
        atomic_write(inflight_path, inflight)
        started = time.monotonic()
        try:
            prompts = [tokenizer.apply_chat_template(row["messages"], tokenize=False, add_generation_prompt=True) for row in batch_rows]
            encoded = tokenizer(prompts, return_tensors="pt", padding=True, add_special_tokens=False).to(model.device)
            width = encoded["input_ids"].shape[1]
            with torch.inference_mode():
                generated = model.generate(
                    **encoded, max_new_tokens=plan["evaluation"]["decoding"]["max_new_tokens"], do_sample=False,
                    pad_token_id=tokenizer.eos_token_id, eos_token_id=tokenizer.eos_token_id,
                )
            elapsed = round((time.monotonic() - started) * 1000, 3)
            result_rows = []
            for index, source in enumerate(batch_rows):
                continuation = generated[index, width:]
                raw = tokenizer.decode(continuation, skip_special_tokens=True)
                labels = {row["label"] for row in source["options"]}
                observed, error = parse(raw, labels)
                result_rows.append({
                    "condition": args.condition, "reader_id": model_id, "physical_cuda_visible_devices": visible,
                    "batch": batch_number, "id": source["id"], "key": source["key"], "arm": source["condition"],
                    "expected": source["expected"], "observed": observed, "valid": error is None,
                    "raw": raw, "error": error,
                    "input_tokens": int(encoded["attention_mask"][index].sum().item()),
                    "output_tokens": len(tokenizer(raw, add_special_tokens=False)["input_ids"]),
                    "batch_latency_ms": elapsed,
                    "public_preregistration_commit": prereg_commit, "public_adapter_receipt_commit": adapter_commit,
                })
        except Exception as exc:
            result_rows = invalid_rows(inflight, f"{type(exc).__name__}: {exc}")
        append_many(journal, result_rows)
        inflight_path.unlink(missing_ok=True)
        completed.update(row["id"] for row in result_rows)
        print(f"{args.condition} batch {batch_number:02d}/{(len(eval_rows) + batch_size - 1) // batch_size}: {sum(row['valid'] for row in result_rows)}/{len(result_rows)} valid", flush=True)
    print(json.dumps({"condition": args.condition, "status": "complete", "rows": len(completed), "reader_id": model_id}, sort_keys=True))
    del model
    del base
    gc.collect()
    torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
