#!/usr/bin/env python3
"""Train one frozen cross-over QLoRA adapter entirely from local artifacts."""

from __future__ import annotations

import argparse
import json
import os
import random
import time
from pathlib import Path

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

from integrity import ROOT, aggregate_files, artifact_files, jsonl, pretty, sha256_file, verify_preregistered


class ChatDataset:
    def __init__(self, path: Path, tokenizer, max_length: int):
        from torch.utils.data import Dataset

        self._dataset_base = Dataset
        self.rows = jsonl(path)
        self.encoded = []
        self.max_observed_length = 0
        for row in self.rows:
            messages = row["messages"]
            prompt = tokenizer.apply_chat_template(messages[:-1], tokenize=False, add_generation_prompt=True)
            full = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
            prompt_ids = tokenizer(prompt, add_special_tokens=False)["input_ids"]
            encoded = tokenizer(full, add_special_tokens=False, truncation=False)
            input_ids = encoded["input_ids"]
            if len(input_ids) > max_length:
                raise RuntimeError(f"{row['id']}: {len(input_ids)} tokens exceeds frozen max_length={max_length}")
            labels = [-100] * min(len(prompt_ids), len(input_ids)) + input_ids[len(prompt_ids):]
            if not any(label != -100 for label in labels):
                raise RuntimeError(f"{row['id']}: assistant answer has no trainable token")
            self.max_observed_length = max(self.max_observed_length, len(input_ids))
            self.encoded.append({"input_ids": input_ids, "attention_mask": encoded["attention_mask"], "labels": labels})

    def __len__(self):
        return len(self.encoded)

    def __getitem__(self, index):
        return self.encoded[index]


class Collator:
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def __call__(self, rows):
        import torch

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
    parser.add_argument("--group", choices=("a", "b"), required=True)
    args = parser.parse_args()
    expected_device = "0" if args.group == "a" else "1"
    if os.environ.get("CUDA_VISIBLE_DEVICES") != expected_device:
        raise SystemExit(f"REFUSING: group {args.group} must run with CUDA_VISIBLE_DEVICES={expected_device}")
    public_commit = verify_preregistered()
    plan = json.loads((ROOT / "RUN_PLAN.json").read_text(encoding="utf-8"))
    source = ROOT / f"train-{args.group}.jsonl"
    expected_source = plan["outputs"][source.name]["sha256"]
    if sha256_file(source) != expected_source:
        raise SystemExit("REFUSING: training source drift")
    target = Path(plan["adapter_paths"][args.group])
    if target.exists():
        raise SystemExit(f"REFUSING: output path already exists: {target}")
    snapshot = Path.home() / ".cache" / "huggingface" / "hub" / "models--Qwen--Qwen2.5-7B-Instruct" / "snapshots" / plan["base_revision"]
    if not snapshot.is_dir():
        raise SystemExit(f"REFUSING: pinned local base snapshot missing: {snapshot}")

    import torch
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, Trainer, TrainingArguments, set_seed

    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise SystemExit("REFUSING: the isolated process must see exactly one CUDA device")
    frozen = plan["training"]
    set_seed(frozen["seed"])
    random.seed(frozen["seed"])
    tokenizer = AutoTokenizer.from_pretrained(plan["base_model"], revision=plan["base_revision"], local_files_only=True, use_fast=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    dataset = ChatDataset(source, tokenizer, frozen["max_length"])
    if len(dataset) != frozen["rows_per_adapter"]:
        raise SystemExit("REFUSING: tokenized training population drift")
    if sha256_file(source) != expected_source:
        raise SystemExit("REFUSING: training source changed during preflight")

    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        plan["base_model"], revision=plan["base_revision"], local_files_only=True,
        quantization_config=quantization, device_map={"": 0}, torch_dtype=torch.bfloat16,
    )
    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    lora = frozen["lora"]
    model = get_peft_model(model, LoraConfig(
        r=lora["r"], lora_alpha=lora["alpha"], lora_dropout=lora["dropout"], bias="none", task_type="CAUSAL_LM",
        target_modules=lora["target_modules"],
    ))
    target.parent.mkdir(parents=True, exist_ok=True)
    trainer = Trainer(
        model=model,
        args=TrainingArguments(
            output_dir=str(target), num_train_epochs=frozen["epochs"],
            per_device_train_batch_size=frozen["per_device_batch_size"],
            gradient_accumulation_steps=frozen["gradient_accumulation_steps"],
            learning_rate=frozen["learning_rate"], warmup_ratio=0.05, lr_scheduler_type="cosine",
            optim="adamw_torch", logging_steps=10, save_strategy="no", report_to="none",
            bf16=True, tf32=True, gradient_checkpointing=True, remove_unused_columns=False,
            seed=frozen["seed"], data_seed=frozen["seed"], dataloader_num_workers=0,
        ),
        train_dataset=dataset,
        data_collator=Collator(tokenizer),
    )
    model.print_trainable_parameters()
    started = time.time()
    metrics = trainer.train().metrics
    trainer.save_model(str(target))
    tokenizer.save_pretrained(str(target))
    receipt = {
        "schema": "ainglish.crossover-qlora-training-receipt.v1",
        "group": args.group,
        "constructs": plan["groups"][args.group],
        "base_model": plan["base_model"], "base_revision": plan["base_revision"],
        "source": source.name, "source_sha256": expected_source, "rows": len(dataset),
        "max_observed_tokens": dataset.max_observed_length,
        "seed": frozen["seed"], "epochs": frozen["epochs"], "hyperparameters": frozen,
        "physical_cuda_visible_devices": expected_device, "logical_device_name": torch.cuda.get_device_name(0),
        "started_unix": started, "finished_unix": time.time(), "metrics": metrics,
        "public_preregistration_commit": public_commit, "downloads": 0, "governance_evidence": False,
    }
    (target / "training-receipt.json").write_bytes(pretty(receipt))
    files = artifact_files(target)
    total_bytes = sum(row["bytes"] for row in files)
    if total_bytes > frozen["artifact_size_ceiling_bytes"]:
        raise RuntimeError(f"artifact exceeds frozen byte ceiling: {total_bytes}")
    manifest = {
        "schema": "ainglish.crossover-qlora-artifact-manifest.v1",
        "group": args.group, "directory": str(target), "files": files,
        "total_bytes": total_bytes, "aggregate_sha256": aggregate_files(files),
    }
    (target / "artifact-manifest.json").write_bytes(pretty(manifest))
    print(json.dumps({"receipt": receipt, "artifact": {key: manifest[key] for key in ("group", "directory", "total_bytes", "aggregate_sha256")}}, indent=2))


if __name__ == "__main__":
    main()
