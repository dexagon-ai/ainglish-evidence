#!/usr/bin/env python3
"""Run the frozen exposure benchmark on a local base and its frozen adapter."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
from pathlib import Path
import re
import time
import unicodedata

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, set_seed
from peft import PeftModel


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
BASE = "Qwen/Qwen2.5-7B-Instruct"
BASE_REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"
ADAPTER = REPO.parent / "artifacts" / "ainglish-qwen2.5-7b-dev-20260825"
SYSTEM = "Return only the exact registered Ainglish form requested. Add no prose, quotation marks, or code fence."


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    sealed = dict(value)
    expected = sealed.pop("content_sha256")
    if hashlib.sha256(canonical(sealed)).hexdigest() != expected:
        raise SystemExit("REFUSING: item digest drift")
    return value


def normalized(value: str) -> str:
    value = unicodedata.normalize("NFKC", value.strip())
    value = re.sub(r"^```[^\n]*\n?|\n?```$", "", value).strip().strip("`\"'")
    return " ".join(value.split())


def generate(model, tokenizer, messages: list[dict]) -> tuple[str, int, int, float]:
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    encoded = tokenizer(prompt, return_tensors="pt", add_special_tokens=False).to(model.device)
    started = time.monotonic()
    with torch.inference_mode():
        output = model.generate(
            **encoded, max_new_tokens=48, do_sample=False,
            pad_token_id=tokenizer.eos_token_id, eos_token_id=tokenizer.eos_token_id,
        )
    latency = time.monotonic() - started
    continuation = output[0, encoded["input_ids"].shape[1] :]
    return tokenizer.decode(continuation, skip_special_tokens=True).strip(), encoded["input_ids"].numel(), continuation.numel(), latency


def load_base():
    quantization = BitsAndBytesConfig(
        load_in_4bit=True, bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True,
    )
    return AutoModelForCausalLM.from_pretrained(
        BASE, revision=BASE_REVISION, local_files_only=True,
        quantization_config=quantization, device_map={"": 0}, torch_dtype=torch.bfloat16,
    )


def run_condition(name: str, items: list[dict], tokenizer) -> list[dict]:
    set_seed(2026082831)
    base = load_base()
    model = base if name == "base" else PeftModel.from_pretrained(base, str(ADAPTER), local_files_only=True)
    model.eval()
    rows = []
    for item in items:
        user = "Which exact registered Ainglish form expresses this meaning?\n\n" + item["gloss"]
        messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]
        first, first_in, first_out, first_latency = generate(model, tokenizer, messages)
        first_ok = normalized(first) == normalized(item["answer"])
        turns = [{"round": 1, "output": first, "input_tokens": first_in, "output_tokens": first_out, "success": first_ok, "latency_s": round(first_latency, 6)}]
        if not first_ok:
            repair = (
                "Authoritative register repair receipt:\n"
                f"Exact form: {item['answer']}\n"
                f"Definition: {item['repair_definition']}\n\n"
                "Return only the exact form from this receipt."
            )
            repaired_messages = [*messages, {"role": "assistant", "content": first}, {"role": "user", "content": repair}]
            second, second_in, second_out, second_latency = generate(model, tokenizer, repaired_messages)
            second_ok = normalized(second) == normalized(item["answer"])
            turns.append({"round": 2, "output": second, "input_tokens": second_in, "output_tokens": second_out, "success": second_ok, "latency_s": round(second_latency, 6)})
        rows.append({
            "id": item["id"], "slug": item["slug"], "exposure_class": item["exposure_class"],
            "answer": item["answer"], "turns": turns,
            "first_pass_success": first_ok,
            "eventual_success": turns[-1]["success"],
            "interaction_tokens": sum(turn["input_tokens"] + turn["output_tokens"] for turn in turns),
            "repair_required": not first_ok,
        })
    del model, base
    gc.collect()
    torch.cuda.empty_cache()
    return rows


def summarize(rows: list[dict]) -> dict:
    output = {}
    for stratum in ("all", "trained_surface", "withheld_surface"):
        subset = rows if stratum == "all" else [row for row in rows if row["exposure_class"] == stratum]
        output[stratum] = {
            "items": len(subset),
            "first_pass_successes": sum(row["first_pass_success"] for row in subset),
            "eventual_successes": sum(row["eventual_success"] for row in subset),
            "repairs": sum(row["repair_required"] for row in subset),
            "interaction_tokens": sum(row["interaction_tokens"] for row in subset),
            "mean_interaction_tokens": round(sum(row["interaction_tokens"] for row in subset) / len(subset), 6),
        }
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="result.json")
    args = parser.parse_args()
    target = ROOT / args.output
    if target.exists():
        raise SystemExit("REFUSING: result exists")
    packet = checked(ROOT / "items.json")
    tokenizer = AutoTokenizer.from_pretrained(BASE, revision=BASE_REVISION, local_files_only=True, use_fast=True)
    base_rows = run_condition("base", packet["items"], tokenizer)
    adapter_rows = run_condition("adapter", packet["items"], tokenizer)
    summaries = {"base": summarize(base_rows), "adapter": summarize(adapter_rows)}
    report = {
        "kind": "dexagon.ainglish.fixed-tokenizer-exposure-result.v1",
        "items_sha256": packet["content_sha256"],
        "base_model": BASE,
        "base_revision": BASE_REVISION,
        "adapter": str(ADAPTER),
        "tokenizer": {"source": BASE, "revision": BASE_REVISION, "class": type(tokenizer).__name__, "vocab_size": len(tokenizer)},
        "decoding": {"do_sample": False, "max_new_tokens": 48, "seed": 2026082831},
        "summaries": summaries,
        "paired_effects": {
            stratum: {
                "first_pass_success_delta": summaries["adapter"][stratum]["first_pass_successes"] - summaries["base"][stratum]["first_pass_successes"],
                "repair_delta": summaries["adapter"][stratum]["repairs"] - summaries["base"][stratum]["repairs"],
                "interaction_token_delta": summaries["adapter"][stratum]["interaction_tokens"] - summaries["base"][stratum]["interaction_tokens"],
            }
            for stratum in summaries["base"]
        },
        "rows": {"base": base_rows, "adapter": adapter_rows},
        "governance_evidence": False,
        "interpretation": "Same base revision, quantization, tokenizer, prompts and deterministic decoding. The only condition change is the frozen LoRA adapter. Trained-surface results measure exposure uptake, not independent generalization; withheld surfaces are a four-item exploratory transfer stratum.",
    }
    report["content_sha256"] = hashlib.sha256(canonical(report)).hexdigest()
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "summaries": summaries, "paired_effects": report["paired_effects"], "content_sha256": report["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
