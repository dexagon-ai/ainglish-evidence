#!/usr/bin/env python3
"""Train a development or release QLoRA adapter on the frozen learning corpus."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random

import torch
from torch.utils.data import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    Trainer,
    TrainingArguments,
    set_seed,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training


ROOT = Path(__file__).resolve().parent
MODEL = "Qwen/Qwen2.5-7B-Instruct"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ChatDataset(Dataset):
    def __init__(self, path: Path, tokenizer, max_length: int):
        self.rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        messages = self.rows[index]["messages"]
        prompt = self.tokenizer.apply_chat_template(messages[:-1], tokenize=False, add_generation_prompt=True)
        full = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        prompt_ids = self.tokenizer(prompt, add_special_tokens=False)["input_ids"]
        encoded = self.tokenizer(full, add_special_tokens=False, truncation=True, max_length=self.max_length)
        input_ids = encoded["input_ids"]
        labels = [-100] * min(len(prompt_ids), len(input_ids)) + input_ids[len(prompt_ids):]
        if not any(label != -100 for label in labels):
            raise RuntimeError(
                f"row {self.rows[index]['id']} lost its entire assistant answer at max_length={self.max_length}"
            )
        return {"input_ids": input_ids, "attention_mask": encoded["attention_mask"], "labels": labels}


class Collator:
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def __call__(self, rows):
        width = max(len(row["input_ids"]) for row in rows)
        output = {"input_ids": [], "attention_mask": [], "labels": []}
        for row in rows:
            pad = width - len(row["input_ids"])
            output["input_ids"].append(row["input_ids"] + [self.tokenizer.pad_token_id] * pad)
            output["attention_mask"].append(row["attention_mask"] + [0] * pad)
            output["labels"].append(row["labels"] + [-100] * pad)
        return {key: torch.tensor(value, dtype=torch.long) for key, value in output.items()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("development", "release"), default="development")
    parser.add_argument("--output", required=True)
    parser.add_argument("--epochs", type=float, default=2.0)
    parser.add_argument("--max-length", type=int, default=2048)
    args = parser.parse_args()
    source = ROOT / ("train-dev.jsonl" if args.mode == "development" else "train-release.jsonl")
    manifest = json.loads((ROOT / "manifest.json").read_text())
    expected = manifest["outputs"][source.name]["sha256"]
    if file_sha256(source) != expected:
        raise SystemExit("REFUSING: training split drifted from the frozen manifest")
    output = Path(args.output).resolve()
    if output.exists() and any(output.iterdir()):
        raise SystemExit("REFUSING: output directory is not empty")
    set_seed(2026082515)
    random.seed(2026082515)
    tokenizer = AutoTokenizer.from_pretrained(MODEL, use_fast=True)
    tokenizer.pad_token = tokenizer.eos_token
    dataset = ChatDataset(source, tokenizer, args.max_length)
    # Force every row through tokenization before allocating the quantized base
    # model. A truncation or source-drift error is a zero-cost refusal, not a GPU outcome.
    for index in range(len(dataset)):
        dataset[index]
    refreshed_manifest = json.loads((ROOT / "manifest.json").read_text())
    if refreshed_manifest["outputs"][source.name]["sha256"] != expected or file_sha256(source) != expected:
        raise SystemExit("REFUSING: training source or manifest drifted during preflight")
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        MODEL, quantization_config=quantization, device_map={"": 0}, torch_dtype=torch.bfloat16,
    )
    model = prepare_model_for_kbit_training(model)
    model = get_peft_model(model, LoraConfig(
        r=16, lora_alpha=32, lora_dropout=0.05, bias="none", task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    ))
    trainer = Trainer(
        model=model,
        args=TrainingArguments(
            output_dir=str(output), num_train_epochs=args.epochs,
            per_device_train_batch_size=1, gradient_accumulation_steps=8,
            learning_rate=2e-4, warmup_ratio=0.05, lr_scheduler_type="cosine",
            logging_steps=1, save_strategy="epoch", save_total_limit=2,
            bf16=True, tf32=True, gradient_checkpointing=True,
            report_to="none", remove_unused_columns=False, seed=2026082515,
        ),
        train_dataset=dataset,
        data_collator=Collator(tokenizer),
    )
    model.print_trainable_parameters()
    metrics = trainer.train().metrics
    trainer.save_model(str(output))
    tokenizer.save_pretrained(str(output))
    receipt = {
        "kind": "dexagon.ainglish.qlora-training-receipt.v1",
        "mode": args.mode,
        "base_model": MODEL,
        "source": source.name,
        "source_sha256": expected,
        "seed": 2026082515,
        "epochs": args.epochs,
        "max_length": args.max_length,
        "rows": len(dataset),
        "metrics": metrics,
        "governance_evidence": False,
    }
    (output / "training-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
