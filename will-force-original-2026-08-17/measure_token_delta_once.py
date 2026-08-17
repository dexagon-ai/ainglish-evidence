#!/usr/bin/env python3
"""Preregister and file the `will-as-*` careful-English token comparison once.

The fixed baselines spell out the complete accountability mapping that each
marked form replaces.  The outcome is never an admissibility gate: positive,
null, and adverse results are all measurements and must be filed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from ainglish.client import manifest_commitment


ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT.parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402


SLUG = "will-as-promise-will-as-plan-will-as-forecast-mark-whether-a"
TOKENIZERS = ["cl100k_base", "o200k_base"]
RECEIPT = ROOT / "token-delta-receipt.json"

# Six fixed examples per form.  Each English arm carries the whole filed
# mapping, rather than a conveniently terse straw competitor.
PAIRS = [
    (
        "will-as-promise",
        "I promise to review your pull request by Friday; this statement creates a commitment to you, and if I do not review it without being released first, I have wronged you.",
        "I will-as-promise review your pull request by Friday.",
    ),
    (
        "will-as-promise",
        "I promise to deliver the signed bundle by noon; this statement creates a commitment to you, and if I do not deliver it without being released first, I have wronged you.",
        "I will-as-promise deliver the signed bundle by noon.",
    ),
    (
        "will-as-promise",
        "We promise to restore the mirror tonight; this statement creates a commitment to you, and if we do not restore it without being released first, we have wronged you.",
        "We will-as-promise restore the mirror tonight.",
    ),
    (
        "will-as-promise",
        "I promise to send the audit receipt after the run; this statement creates a commitment to you, and if I do not send it without being released first, I have wronged you.",
        "I will-as-promise send the audit receipt after the run.",
    ),
    (
        "will-as-promise",
        "I promise to repay the twelve credits tomorrow; this statement creates a commitment to you, and if I do not repay them without being released first, I have wronged you.",
        "I will-as-promise repay the twelve credits tomorrow.",
    ),
    (
        "will-as-promise",
        "We promise to preserve the frozen artifact; this statement creates a commitment to you, and if we do not preserve it without being released first, we have wronged you.",
        "We will-as-promise preserve the frozen artifact.",
    ),
    (
        "will-as-plan",
        "My current plan is to take the migration route; the plan may change, but I owe you notice if it does.",
        "I will-as-plan take the migration route.",
    ),
    (
        "will-as-plan",
        "My current plan is to review the patch this afternoon; the plan may change, but I owe you notice if it does.",
        "I will-as-plan review the patch this afternoon.",
    ),
    (
        "will-as-plan",
        "Our current plan is to deploy through the blue pool; the plan may change, but we owe you notice if it does.",
        "We will-as-plan deploy through the blue pool.",
    ),
    (
        "will-as-plan",
        "My current plan is to use the larger reader model; the plan may change, but I owe you notice if it does.",
        "I will-as-plan use the larger reader model.",
    ),
    (
        "will-as-plan",
        "My current plan is to travel on the morning train; the plan may change, but I owe you notice if it does.",
        "I will-as-plan travel on the morning train.",
    ),
    (
        "will-as-plan",
        "Our current plan is to publish the bundle next week; the plan may change, but we owe you notice if it does.",
        "We will-as-plan publish the bundle next week.",
    ),
    (
        "will-as-forecast",
        "I expect the deployment to finish by 18:00 UTC; this is a prediction about events I do not control, not a commitment to make it happen.",
        "The deployment will-as-forecast finish by 18:00 UTC.",
    ),
    (
        "will-as-forecast",
        "I expect the queue to clear before dawn; this is a prediction about events I do not control, not a commitment to make it happen.",
        "The queue will-as-forecast clear before dawn.",
    ),
    (
        "will-as-forecast",
        "I expect the package to arrive on Tuesday; this is a prediction about events I do not control, not a commitment to make it happen.",
        "The package will-as-forecast arrive on Tuesday.",
    ),
    (
        "will-as-forecast",
        "I expect the price to fall after the auction; this is a prediction about events I do not control, not a commitment to make it happen.",
        "The price will-as-forecast fall after the auction.",
    ),
    (
        "will-as-forecast",
        "I expect the storm to reach the coast tonight; this is a prediction about events I do not control, not a commitment to make it happen.",
        "The storm will-as-forecast reach the coast tonight.",
    ),
    (
        "will-as-forecast",
        "I expect the replication to disagree on one item; this is a prediction about events I do not control, not a commitment to make it happen.",
        "The replication will-as-forecast disagree on one item.",
    ),
]


def manifest() -> dict:
    forms = sorted({form for form, _, _ in PAIRS})
    assert len(PAIRS) == 18 and all(sum(row[0] == form for row in PAIRS) == 6 for form in forms)
    return {
        "metric": "token_delta",
        "construct": "will-as-promise / will-as-plan / will-as-forecast",
        "models": [f"tiktoken/{name}@vocab" for name in TOKENIZERS],
        "tokenizers": TOKENIZERS,
        "design": {
            "items": len(PAIRS),
            "forms": forms,
            "items_per_form": 6,
            "weights": "equal per item and equal per form",
            "selection": "all pairs, weights, tokenizers and analysis fixed before tokenisation",
            "comparison": "marked form minus the proposal's complete careful-English accountability mapping",
        },
        "test_set": [
            {"form": form, "english": english, "ainglish": marked}
            for form, english, marked in PAIRS
        ],
        "pairs": [[english, marked] for _, english, marked in PAIRS],
        "method": (
            "For each tokenizer, compute len(encode(ainglish)) - len(encode(english)) "
            "for every fixed pair. Report the larger, least favourable overall tokenizer "
            "mean. Preserve every tokenizer-by-form mean and every item delta."
        ),
        "analysis_plan": (
            "The filed proposal predicts a negative value against complete careful English. "
            "The result is filed regardless of sign; sign is an outcome, never an admissibility gate."
        ),
        "seed": "none — deterministic tokenisation",
    }


def score(spec: dict) -> tuple[dict, dict]:
    import tiktoken  # deliberately loaded only after the attempt is minted

    cells: dict[str, list[dict]] = {}
    for tokenizer in TOKENIZERS:
        encoding = tiktoken.get_encoding(tokenizer)
        rows = []
        for item in spec["test_set"]:
            delta = len(encoding.encode(item["ainglish"])) - len(encoding.encode(item["english"]))
            rows.append({"form": item["form"], "delta": delta})
        cells[tokenizer] = rows

    means = {
        tokenizer: round(sum(row["delta"] for row in rows) / len(rows), 3)
        for tokenizer, rows in cells.items()
    }
    form_means = {
        tokenizer: {
            form: round(
                sum(row["delta"] for row in rows if row["form"] == form)
                / sum(row["form"] == form for row in rows),
                3,
            )
            for form in spec["design"]["forms"]
        }
        for tokenizer, rows in cells.items()
    }
    observations = [row["delta"] for rows in cells.values() for row in rows]
    value = max(means.values())
    payload = {
        "metric": "token_delta",
        "formula_version": 1,
        "value": value,
        "value_lo": min(observations),
        "value_hi": max(observations),
        "panel_models": [f"tiktoken/{name}@vocab" for name in TOKENIZERS],
        "per_member": [
            {"model": f"tiktoken/{name}", "precision": "vocab", "value": means[name]}
            for name in TOKENIZERS
        ],
        "manifest": spec,
    }
    return payload, {"value": value, "means": means, "form_means": form_means, "cells": cells}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--submit", action="store_true")
    args = parser.parse_args()
    spec = manifest()
    print("manifest_commitment", manifest_commitment(spec))
    if not args.submit:
        print(json.dumps({"status": "frozen-not-run", "manifest": spec}, indent=2))
        return
    if RECEIPT.exists():
        raise SystemExit(f"REFUSING: {RECEIPT.name} already exists; this original is one-shot")

    client = ainglish_client()
    proposal = client.proposal(SLUG)
    if proposal["stage"] != "seconded":
        raise SystemExit(f"REFUSING: proposal stage is {proposal['stage']!r}, not 'seconded'")
    attempt = client.mint_attempt(
        SLUG,
        manifest=spec,
        estimand=(
            "Equal-weight token_delta of the three marked future-force forms against their "
            "complete filed careful-English accountability mappings; six fixed pairs per form, "
            "with the worse of cl100k_base and o200k_base as the headline."
        ),
        admissibility_gates=[
            "both named tokenizer vocabularies load",
            "all 18 frozen pairs contain non-empty and non-identical English and Ainglish arms",
            "all three forms retain exactly six equally weighted pairs",
            "every finite computed outcome is filed regardless of sign",
        ],
        planned_sample={
            "metric": "token_delta",
            "items": 18,
            "forms": spec["design"]["forms"],
            "items_per_form": 6,
            "tokenizers": TOKENIZERS,
            "weights": "equal per item and form",
        },
    )["attempt"]

    payload, computed = score(spec)
    payload["attempt_id"] = attempt["attempt_id"]
    filed = client.measure(SLUG, payload)
    receipt = {
        "kind": "ainglish.token-delta-original.v1",
        "proposal": SLUG,
        "attempt": attempt,
        "computed": computed,
        "measurement": filed,
        "manifest_commitment": manifest_commitment(spec),
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
