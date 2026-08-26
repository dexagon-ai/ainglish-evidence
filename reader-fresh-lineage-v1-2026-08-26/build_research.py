#!/usr/bin/env python3
"""Publish the candidate novelty and feasibility research frozen before acquisition completes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
HISTORY_COMMIT = "b8b0223c81eedd1909e4e2ac96012ac60e0c4f1e"
PRIOR_LINEAGES = (
    "Command R7B", "DeepSeek V2 Lite 16B", "EXAONE 3.5 32B", "Falcon 3 10B",
    "GLM-4 9B", "Gemma 3 12B", "Granite 3.3 8B", "InternLM 2 20B",
    "Llama 3.1 8B", "Mistral Small 3.2 24B", "OLMo 2 13B", "OpenAI GPT-OSS 20B",
    "Phi-4 14B", "Qwen 2.5 7B", "Qwen 3.5 27B", "Qwen 3.5 9B",
    "Qwen 3.8 27B", "Qwen 3.6 27B",
)
PRIOR_SOURCE_MODELS = (
    "deepseek-v2:16b", "exaone3.5:32b", "falcon3:10b", "gemma3:12b", "glm4:9b",
    "gpt-oss:20b", "internlm2:20b", "mistral-small3.2:24b-instruct-2506-q4_K_M",
    "olmo2:13b", "qwen2.5:7b", "qwen3.5:27b", "qwen3.8-27b-q4:latest",
)


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def build() -> dict:
    candidates = [
        {
            "rank": 1,
            "lineage": "Llama 3.3 70B",
            "producer": "Meta",
            "source_model": "llama3.3:70b-instruct-q4_K_M",
            "published_size_gb": 43,
            "official_reference": "https://ollama.com/library/llama3.3/tags",
            "strength_basis": "Official Ollama card describes Llama 3.3 70B as offering performance similar to Llama 3.1 405B.",
            "novelty": "Exact model and 70B scale are untested in the qualification repository.",
            "independence_caveat": "Correlated with the previously tested Llama 3.1 8B family; do not count both as independent panel lineages.",
            "selected": True,
        },
        {
            "rank": 2,
            "lineage": "Solar Pro 22B",
            "producer": "Upstage",
            "source_model": "solar-pro:22b",
            "published_size_gb": 13,
            "official_reference": "https://ollama.com/library/solar-pro",
            "strength_basis": "Official Ollama card reports strong MMLU-Pro and IFEval performance and comparison with Llama 3.1 70B.",
            "novelty": "Previously untested producer, architecture, source model, and lineage.",
            "independence_caveat": "Solar Pro scales a Phi-3-medium base; disclose correlation if a Phi-family reader later joins the same scientific panel.",
            "selected": True,
        },
        {
            "rank": 3,
            "lineage": "Command R 35B",
            "producer": "Cohere",
            "source_model": "command-r:35b",
            "published_size_gb": 19,
            "official_reference": "https://ollama.com/library/command-r/tags",
            "strength_basis": "Larger 35B Command R edition optimized for conversational interaction and long-context accuracy.",
            "novelty": "Exact 35B edition is untested.",
            "independence_caveat": "Same Command family as the tested Command R7B; reserve rather than primary independence seat.",
            "selected": False,
        },
        {
            "rank": 4,
            "lineage": "Aya Expanse 32B",
            "producer": "Cohere For AI",
            "source_model": "aya-expanse:32b",
            "published_size_gb": 20,
            "official_reference": "https://ollama.com/library/aya-expanse:32b",
            "strength_basis": "32B multilingual instruction model with explicit English support.",
            "novelty": "Exact edition and Aya tuning are untested.",
            "independence_caveat": "Built on the Command family and therefore correlated with Command R.",
            "selected": False,
        },
        {
            "rank": 5,
            "lineage": "Yi 34B",
            "producer": "01.AI",
            "source_model": "yi:34b-chat",
            "published_size_gb": 19,
            "official_reference": "https://ollama.com/library/yi:34b-chat",
            "strength_basis": "Large bilingual chat model from a previously untested producer.",
            "novelty": "Previously untested producer, source model, and lineage.",
            "independence_caveat": "Older four-thousand-token model with weaker current instruction-following evidence than the selected pair.",
            "selected": False,
        },
        {
            "rank": 6,
            "lineage": "Llama 3.1 Nemotron 70B",
            "producer": "NVIDIA",
            "source_model": "nemotron:70b",
            "published_size_gb": 43,
            "official_reference": "https://ollama.com/library/nemotron:70b",
            "strength_basis": "70B NVIDIA helpfulness-tuned model.",
            "novelty": "Exact tuning is untested.",
            "independence_caveat": "Derived from Llama 3.1 70B; costly and strongly correlated with the Llama branch.",
            "selected": False,
        },
    ]
    selected = [row for row in candidates if row["selected"]]
    if len(selected) != 2 or any(row["source_model"] in PRIOR_SOURCE_MODELS for row in selected):
        raise SystemExit("REFUSING: selected candidate novelty drift")
    document = {
        "kind": "ainglish.panel.reader-fresh-lineage-research.v1",
        "evidentiary_status": "reader-development research; never qualification or proposal evidence",
        "researched_at": "2026-08-26",
        "history": {
            "repository_commit": HISTORY_COMMIT,
            "substantive_lineages_seen": list(PRIOR_LINEAGES),
            "source_models_seen": list(PRIOR_SOURCE_MODELS),
        },
        "resource_envelope": {
            "gpus": ["NVIDIA GeForce RTX 3090", "NVIDIA GeForce RTX 3090"],
            "usable_total_vram_gib_approx": 47,
            "disk_free_gib_before_acquisition": 575,
            "maximum_selected_published_model_size_gb": 43,
        },
        "ranking_rule": "Prefer expected ordinary-English reasoning strength, exact source novelty, producer/base-family diversity, no-thinking compatibility potential, and sequential fit within two 24 GiB GPUs.",
        "candidates": candidates,
        "selected_order": [row["source_model"] for row in selected],
        "execution_rule": "Acquire first, inspect pinned manifests and capabilities, then freeze a staged format gate before exposing any semantic development item.",
        "model_calls": 0,
    }
    document["content_sha256"] = hashlib.sha256(canonical(document)).hexdigest()
    return document


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    document = build()
    target = ROOT / "research.json"
    if args.write:
        if target.exists():
            raise SystemExit("REFUSING: research.json already exists")
        target.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"selected_order": document["selected_order"], "sha256": document["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
