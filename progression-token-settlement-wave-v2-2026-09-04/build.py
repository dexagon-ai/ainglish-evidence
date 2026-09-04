#!/usr/bin/env python3
"""Freeze three 32-pair token replications without importing a tokenizer."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MODELS = ["cl100k_base", "o200k_base", "p50k_base"]


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def multiply_pairs() -> list[dict]:
    subjects = [
        "audit latency", "batch throughput", "cache capacity", "decoder speed",
        "export volume", "fetch duration", "gateway traffic", "heap usage",
    ]
    rows = []
    for index, subject in enumerate(subjects, 1):
        n = (2, 3, 4, 5)[(index - 1) % 4]
        rows.append({
            "id": f"increase-as-{index:02d}",
            "english": f"In trial M{index:02d}, {subject} was {n} times higher than the baseline.",
            "ainglish": f"In trial M{index:02d}, {subject} was {n} times as high as the baseline.",
        })
        rows.append({
            "id": f"increase-the-{index:02d}",
            "english": f"In trial N{index:02d}, the new system used {n} times more {subject} than the old system.",
            "ainglish": f"In trial N{index:02d}, the new system used {n} times the {subject} of the old system.",
        })
        rows.append({
            "id": f"increase-symbol-{index:02d}",
            "english": f"In trial P{index:02d}, {subject} reached {n}-fold higher than the reference level.",
            "ainglish": f"In trial P{index:02d}, {subject} reached {n}× the reference level.",
        })
        rows.append({
            "id": f"decrease-fraction-{index:02d}",
            "english": f"In trial Q{index:02d}, {subject} was {n} times lower than the reference level.",
            "ainglish": f"In trial Q{index:02d}, {subject} was one-{n}th the reference level.",
        })
    return rows


def availability_pairs() -> list[dict]:
    resources = [
        ("GPU 14", "research-pool"), ("meeting room Cedar", "Friday-09:00"),
        ("archive mirror Delta", "restore-team"), ("cargo bay 6", "night-shift"),
        ("test handset K", "mobile-lab"), ("render node 23", "animation-pool"),
        ("translation booth B", "conference-slot"), ("spectrometer 4", "chemistry-pool"),
        ("backup circuit North", "maintenance-window"), ("field vehicle 8", "survey-team"),
        ("training seat 19", "September-cohort"), ("storage tier Bronze", "project-iris"),
        ("lab bench 5", "assay-window"), ("support channel J", "incident-team"),
        ("database replica 7", "analytics-pool"), ("inspection drone 3", "coastal-mission"),
    ]
    rows = []
    for index, (resource, scope) in enumerate(resources, 1):
        rows.append({
            "id": f"no-charge-{index:02d}",
            "english": f"Using {resource} incurs no monetary charge within {scope}; this says nothing about current allocation.",
            "ainglish": f"{resource} is no-charge({scope}).",
        })
        rows.append({
            "id": f"available-now-{index:02d}",
            "english": f"A qualifying requester can allocate {resource} now within {scope}; this says nothing about price.",
            "ainglish": f"{resource} is available-now({scope}).",
        })
    return rows


def replacement_pairs() -> list[dict]:
    things = [
        "signing-key", "parser", "coolant-pump", "routing-rule", "reviewer", "source-document",
        "patient-instruction", "database-row", "sensor", "dependency", "service-account", "policy",
        "adapter", "certificate", "worker", "schema", "mirror", "queue", "dataset", "gateway",
        "controller", "index", "dashboard", "translator", "record", "connector", "filter", "schedule",
        "validator", "template", "checkpoint", "replica",
    ]
    rows = []
    for index, thing in enumerate(things, 1):
        old = f"{thing}-old-{index:02d}"
        new = f"{thing}-new-{index:02d}"
        slot = f"slot-R{index:02d}"
        rows.append({
            "id": f"replace-{index:02d}",
            "english": f"Remove {old} from {slot} and put {new} in that slot instead.",
            "ainglish": f"In {slot}, replace(old={old}, new={new}).",
        })
    return rows


def write(name: str, public_id: str, slug: str, construct: str, target: str, pairs: list[dict]) -> dict:
    assert len(pairs) == 32
    assert len({(row["english"], row["ainglish"]) for row in pairs}) == 32
    manifest = {
        "metric": "token_delta",
        "construct": construct,
        "models": MODELS,
        "replicates_hash": target,
        "test_set": pairs,
        "seed": "deterministic-no-randomness-20260904-v2",
        "method": "tiktoken encode count difference between Ainglish and English for every complete pair; equal pair mean per tokenizer; headline is the maximum tokenizer mean",
        "environment": {"library": "tiktoken", "version": "0.14.0"},
        "training_asymmetry": "Current tokenizers were trained around ordinary English and are not assumed to have seen Ainglish. This is present-day cost evidence, not a ceiling on post-training or future-tokenizer efficiency.",
    }
    path = ROOT / f"{name}.manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "name": name,
        "public_id": public_id,
        "slug": slug,
        "construct": construct,
        "replicates_hash": target,
        "file": path.name,
        "pair_count": len(pairs),
        "manifest_sha256": sha256(canonical(manifest)).hexdigest(),
        "pairs_sha256": sha256(canonical(pairs)).hexdigest(),
    }


def main() -> None:
    campaigns = [
        write(
            "multiply-quantity", "a-cjgt374hndvt1jqa",
            "multiply-the-quantity-a-multiplier-attaches-to-the-2", "multiply-the-quantity",
            "6660caff9f84bb5f1fac081bd4b1e7801776c2659f5b72fc14eb019929c3975f", multiply_pairs(),
        ),
        write(
            "price-availability", "a-yc4193gwc2e87zkn",
            "offer-is-no-charge-billing-scope-resource-is-available-now", "no-charge / available-now",
            "12f28a15fa7ab6af314f380945cd2cf9ca041a29b25b9fdf3573d29d7aaf5e4b", availability_pairs(),
        ),
        write(
            "replacement-roles", "a-f34mb0zf8xp2pkwm", "replace-old-departing-ref-new-incoming-ref",
            "replace(old, new)", "c447483fa585e6e151ad5259be0f1310bb0941aded707433623b4fe854dd1c02",
            replacement_pairs(),
        ),
    ]
    all_pairs = []
    for row in campaigns:
        all_pairs.extend(json.loads((ROOT / row["file"]).read_text(encoding="utf-8"))["test_set"])
    assert len({(row["english"], row["ainglish"]) for row in all_pairs}) == 96
    output = {
        "kind": "dexagon.ainglish.progression-token-settlement-wave.v2",
        "model_calls": 0,
        "tokenizer_calls": 0,
        "tiktoken_version": "0.14.0",
        "campaigns": {row["name"]: row for row in campaigns},
    }
    output["content_sha256"] = sha256(canonical(output)).hexdigest()
    (ROOT / "index.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
