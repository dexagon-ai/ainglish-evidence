#!/usr/bin/env python3
"""Build balanced local or immutable runspecs for each standing-property form."""

from __future__ import annotations

from collections import Counter
import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SLUG = "by-construction-by-rule-in-practice-mark-whether-a-standing-"
FORMS = ("by-construction", "by-rule", "in-practice")
DOMAINS = ("infrastructure", "data", "security", "workflow", "physical", "governance")
READERS = [
    {
        "name": "mistral-small3.2-24b-event-task-q4_k_m",
        "provider": "ollama",
        "model": "dexagon-mistral-small3.2-24b-event-task:ctx4k",
        "model_digest": "sha256:d863e7d02e85c64e98388581a1dc0ae6d1493adac28f7167a688e28b15765745",
        "precision": "q4_k_m",
        "api": "openai",
        "base_url": "http://127.0.0.1:11434/v1",
        "max_tokens": 256,
        "timeout_s": 120,
        "temperature": 0,
    },
    {
        "name": "gemma3-12b-event-task-q4_k_m",
        "provider": "ollama",
        "model": "dexagon-gemma3-12b-event-task:ctx4k",
        "model_digest": "sha256:2586761c96ff8c74c0c1c1b6b4d8a5d6f5718fe049237341deb0e50141be942c",
        "precision": "q4_k_m",
        "api": "openai",
        "base_url": "http://127.0.0.1:11434/v1",
        "max_tokens": 256,
        "timeout_s": 120,
        "temperature": 0,
    },
    {
        "name": "qwen2.5-7b-event-task-q4_k_m",
        "provider": "ollama",
        "model": "dexagon-qwen2.5-7b-event-task:ctx4k",
        "model_digest": "sha256:f43ddd2e3d09fd829a4e5b839419243dc2b2dc767bf288a9b80ba56c329db107",
        "precision": "q4_k_m",
        "api": "openai",
        "base_url": "http://127.0.0.1:11434/v1",
        "max_tokens": 256,
        "timeout_s": 120,
        "temperature": 0,
    },
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def arm_for(seed: int, reader: str, item_id: str) -> str:
    return "ainglish" if hashlib.sha256(f"{seed}|{reader}|{item_id}".encode()).digest()[0] % 2 else "english"


def choose_seed(items: list[dict], start: int) -> tuple[int, dict]:
    real = [row for row in items if not row.get("calibration")]
    for seed in range(start, start + 1_000_000):
        report = {}
        for reader in READERS:
            marked = [row for row in real if arm_for(seed, reader["name"], row["id"]) == "ainglish"]
            counts = Counter(row["strata"]["domain"] for row in marked)
            if len(marked) != 24 or any(not 3 <= counts[domain] <= 5 for domain in DOMAINS):
                break
            report[reader["name"]] = {"ainglish": 24, "english": 24, "ainglish_by_domain": dict(counts)}
        else:
            return seed, report
    raise RuntimeError("no balanced seed found")


def build(form: str, freeze_commit: str | None) -> dict:
    document = json.loads((ROOT / f"{form}-items.json").read_text(encoding="utf-8"))
    receipt = json.loads((ROOT / "freeze-receipt.json").read_text(encoding="utf-8"))
    frozen = next(row for row in receipt["files"] if row["form"] == form)
    if canonical(document["items"]) is None or hashlib.sha256(canonical(document["items"])).hexdigest() != frozen["items_sha256"]:
        raise SystemExit(f"REFUSING: {form} digest drift")
    seed, assignment = choose_seed(document["items"], document["seed_base"])
    source = (
        f"https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{freeze_commit}/"
        f"by-standing-property-comprehension-original-2026-08-23/{form}-items.json"
        if freeze_commit else str(ROOT / f"{form}-items.json")
    )
    answer = next(row["answer"] for row in document["items"] if not row.get("calibration"))
    return {
        "construct": f"{form} complete-careful-English comprehension carrier",
        "slug": SLUG,
        "metric": "comprehension_accuracy_delta",
        "seed": seed,
        "planted_arm": "ainglish",
        "calibration_min_gap": 0.5,
        "panel_neff": 1,
        "panel": [dict(reader, seed=seed) for reader in READERS],
        "items_url": source,
        "items_sha256": frozen["items_sha256"],
        "attempt": {
            "proposal_revision": SLUG,
            "estimand": (
                f"Percentage-point exact two-consequence-profile accuracy difference for {form}, "
                "marked form minus its complete registered careful-English mapping, over 48 frozen "
                "scenarios and three Q4_K_M reader families. The standalone -5 percentage-point "
                "non-inferiority interpretation applies only to this form; forms are never pooled."
            ),
            "admissibility_gates": [
                f"the {form} packet remains {frozen['items_sha256']} with 48 real and 8 construct-free calibration rows",
                f"every real row tests only {form} against its complete careful-English mapping and has keyed profile {answer}",
                "all six domains contribute exactly eight rows and answer positions differ by at most one",
                "the intent, ceremony, removal-test, named-owner, and vacuous-success cases remain labelled for descriptive audit and never change the scalar after results",
                "each reader receives exactly 24 marked and 24 careful-English real cells, with three to five marked cells in every domain",
                "all three reader artifacts match their declared live Ollama digests; response binding is opaque-choice-v1 and max_tokens is 256",
                "the construct-free calibration block runs first in both arms for every reader and pooled explicit-minus-opaque accuracy is at least 0.5",
                "any digest, live-stage, resource, calibration, yield, transport, truncation, manifest, or reconciliation failure becomes a typed abort without retry",
                "all finite supportive, null, adverse, ceiling-bound and floor-bound results file; all three sibling forms execute regardless of earlier scientific directions",
            ],
            "planned_sample": {
                "form": form,
                "comparison": "complete registered careful-English mapping",
                "real_items": 48,
                "calibration_items": 8,
                "real_reader_cells": 144,
                "calibration_reader_cells": 48,
                "domains": {domain: 8 for domain in DOMAINS},
                "readers": [reader["name"] for reader in READERS],
                "reader_lineages": ["Mistral Small 3.2 24B", "Gemma 3 12B", "Qwen 2.5 7B"],
                "panel_neff": 1,
                "noninferiority_margin_pp": -5,
                "assignment": assignment,
                "seed": seed,
            },
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze-commit")
    args = parser.parse_args()
    if args.freeze_commit and (len(args.freeze_commit) != 40 or any(c not in "0123456789abcdef" for c in args.freeze_commit)):
        raise SystemExit("--freeze-commit must be lowercase 40-hex")
    report = {}
    for form in FORMS:
        spec = build(form, args.freeze_commit)
        path = ROOT / f"runspec-{form}.json"
        path.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        report[form] = {"seed": spec["seed"], "items_sha256": spec["items_sha256"], "path": path.name}
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
