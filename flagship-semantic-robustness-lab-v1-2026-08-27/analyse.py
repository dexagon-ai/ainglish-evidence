#!/usr/bin/env python3
"""Derive a claim-bounded summary from the immutable robustness result."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    result = json.loads((ROOT / "result.json").read_text(encoding="utf-8"))
    sealed = dict(result)
    expected = sealed.pop("content_sha256")
    if hashlib.sha256(canonical(sealed)).hexdigest() != expected:
        raise SystemExit("REFUSING: result digest drift")
    usable_models = []
    output_failures = {}
    for model in result["model_summary"]:
        calls = [row for row in result["calls"] if row["model"] == model]
        parseable = sum(row["parse_error"] is None for row in calls)
        empty = sum(not row["raw_response"] for row in calls)
        if parseable == len(calls):
            usable_models.append(model)
        else:
            output_failures[model] = {
                "calls": len(calls),
                "parseable_calls": parseable,
                "empty_response_calls": empty,
                "eval_tokens_min": min(row["eval_count"] or 0 for row in calls),
                "eval_tokens_max": max(row["eval_count"] or 0 for row in calls),
                "classification": "output-channel/harness failure; semantic accuracy not estimable",
                "interpretation": "The server reported generated tokens and stop completion but returned an empty response field on every call. The frozen runner did not retain a separate thinking field, so the zero score is not evidence that the model selected the wrong pole.",
            }
    usable_calls = [row for row in result["calls"] if row["model"] in usable_models]
    usable_cells = [cell | {"model": call["model"], "slug": call["slug"]} for call in usable_calls for cell in call["cells"]]
    variants = sorted({row["variant"] for row in usable_cells})
    variant_summary = {}
    for variant in variants:
        cells = [row for row in usable_cells if row["variant"] == variant]
        variant_summary[variant] = {
            "correct": sum(row["correct"] for row in cells),
            "total": len(cells),
            "accuracy": sum(row["correct"] for row in cells) / len(cells),
        }
    failures = [row for row in usable_cells if not row["correct"]]
    analysis = {
        "kind": "dexagon.ainglish.flagship-semantic-robustness-analysis.v1",
        "result_sha256": result["content_sha256"],
        "usable_models": usable_models,
        "output_failures": output_failures,
        "usable_model_summary": {model: result["model_summary"][model] for model in usable_models},
        "usable_variant_summary": variant_summary,
        "semantic_failures": failures,
        "failure_counts": {
            "semantic_cells": len(failures),
            "by_slug": dict(Counter(row["slug"] for row in failures)),
            "by_variant": dict(Counter(row["variant"] for row in failures)),
        },
        "interpretation": [
            "Gemma and Mistral classified every canonical, careful-English, and hyphen-loss cell correctly under supplied definitions.",
            "The only parseable semantic misses were Gemma's two true-as-worded/false-as-worded opposite-distractor cells; it followed the contrast sentence rather than the explicitly labelled actual message.",
            "Qwen's 0/136 mechanical score is excluded from semantic interpretation because all 17 response fields were empty despite nonzero generation counts.",
            "This is useful development evidence for copy, prompt, and harness design, but it is not Ainglish governance evidence and cannot advance ratification.",
        ],
        "recommended_follow_up": [
            "Make any future development harness explicitly retain both response and thinking channels and freeze a no-thinking capability gate before calls.",
            "Keep true-as-worded/false-as-worded examples away from prose that states the opposite pole immediately before the actual answer, or visually delimit the actual message.",
            "Do not rerun or repair this frozen battery; a changed harness would be a new prospectively versioned experiment.",
        ],
        "model_downloads": 0,
        "governance_writes": 0,
    }
    analysis["content_sha256"] = hashlib.sha256(canonical(analysis)).hexdigest()
    (ROOT / "analysis.json").write_text(json.dumps(analysis, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "usable_models": usable_models,
        "output_failures": list(output_failures),
        "semantic_failures": len(failures),
        "variant_summary": variant_summary,
        "content_sha256": analysis["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
