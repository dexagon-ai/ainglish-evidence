#!/usr/bin/env python3
"""Evaluate the base model or a frozen adapter on seen and transfer splits."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, set_seed
from peft import PeftModel


ROOT = Path(__file__).resolve().parent
MODEL = "Qwen/Qwen2.5-7B-Instruct"


def normalize(value: str) -> list[str]:
    return re.findall(r"[^\W_]+", value.casefold(), flags=re.UNICODE)


def token_f1(prediction: str, reference: str) -> float:
    left, right = Counter(normalize(prediction)), Counter(normalize(reference))
    overlap = sum((left & right).values())
    if not left or not right:
        return float(left == right)
    precision = overlap / sum(left.values())
    recall = overlap / sum(right.values())
    return 2 * precision * recall / (precision + recall) if overlap else 0.0


def canonical_form_hit(prediction: str, reference: str) -> bool:
    return " ".join(normalize(reference)) in " ".join(normalize(prediction))


def load_split(name: str) -> tuple[list[dict], str]:
    manifest = json.loads((ROOT / "manifest.json").read_text())
    path = ROOT / name
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != manifest["outputs"][name]["sha256"]:
        raise SystemExit(f"REFUSING: {name} drifted from the frozen manifest")
    return [json.loads(line) for line in path.read_text().splitlines() if line], digest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter")
    parser.add_argument("--output", required=True)
    parser.add_argument("--splits", nargs="+", default=["validation-seen.jsonl", "transfer-holdout.jsonl"])
    parser.add_argument("--max-new-tokens", type=int, default=256)
    args = parser.parse_args()
    output = Path(args.output).resolve()
    if output.exists():
        raise SystemExit(f"REFUSING: {output} already exists")
    set_seed(2026082516)
    tokenizer = AutoTokenizer.from_pretrained(MODEL, use_fast=True)
    tokenizer.pad_token = tokenizer.eos_token
    quantization = BitsAndBytesConfig(
        load_in_4bit=True, bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        MODEL, quantization_config=quantization, device_map={"": 0}, torch_dtype=torch.bfloat16,
    )
    if args.adapter:
        model = PeftModel.from_pretrained(model, args.adapter)
    model.eval()
    predictions = []
    split_digests = {}
    for split in args.splits:
        rows, split_digests[split] = load_split(split)
        for position, row in enumerate(rows, 1):
            prompt = tokenizer.apply_chat_template(row["messages"][:-1], tokenize=False, add_generation_prompt=True)
            encoded = tokenizer(prompt, return_tensors="pt").to("cuda:0")
            with torch.inference_mode():
                generated = model.generate(
                    **encoded, max_new_tokens=args.max_new_tokens, do_sample=False,
                    pad_token_id=tokenizer.eos_token_id,
                )
            prediction = tokenizer.decode(generated[0, encoded["input_ids"].shape[1]:], skip_special_tokens=True).strip()
            reference = row["messages"][-1]["content"]
            result = {
                "id": row["id"], "split": split, "source_slug": row["source_slug"], "task": row["task"],
                "prediction": prediction, "reference": reference,
                "token_f1": round(token_f1(prediction, reference), 6),
                "canonical_form_hit": canonical_form_hit(prediction, reference) if row["task"] == "form-retrieval" else None,
            }
            predictions.append(result)
            print(f"{split} {position}/{len(rows)} {row['id']} f1={result['token_f1']:.3f}", flush=True)
    groups = defaultdict(list)
    for row in predictions:
        groups[(row["split"], row["task"])].append(row)
    metrics = []
    for (split, task), rows in sorted(groups.items()):
        metric = {
            "split": split, "task": task, "rows": len(rows),
            "mean_token_f1": round(sum(row["token_f1"] for row in rows) / len(rows), 6),
        }
        hits = [row["canonical_form_hit"] for row in rows if row["canonical_form_hit"] is not None]
        if hits:
            metric["canonical_form_accuracy"] = round(sum(hits) / len(hits), 6)
        metrics.append(metric)
    payload = {
        "kind": "dexagon.ainglish.adapter-evaluation.v1",
        "base_model": MODEL,
        "adapter": str(Path(args.adapter).resolve()) if args.adapter else None,
        "seed": 2026082516,
        "max_new_tokens": args.max_new_tokens,
        "split_digests": split_digests,
        "metrics": metrics,
        "predictions": predictions,
        "governance_evidence": False,
    }
    payload["content_sha256"] = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"metrics": metrics, "content_sha256": payload["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
