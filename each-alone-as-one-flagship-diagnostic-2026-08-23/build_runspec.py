#!/usr/bin/env python3
"""Build the preregistration-ready flagship diagnostic run specification."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SLUG = "each-alone-as-one-distributive-vs-collective-does-the-plural"
ITEMS_PATH = ROOT / "careful-items.json"
PUBLIC_ITEMS_URL = (
    "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
    "bdb9cf226b28a8cdb519dbf9cb911472af5d89b8/"
    "each-alone-as-one-flagship-diagnostic-2026-08-23/careful-items.json"
)
READERS = [
    {
        "name": "mistral-small3.2-24b-event-task-q4_k_m",
        "provider": "ollama",
        "model": "dexagon-mistral-small3.2-24b-event-task:ctx4k",
        "model_digest": "sha256:d863e7d02e85c64e98388581a1dc0ae6d1493adac28f7167a688e28b15765745",
        "precision": "q4_k_m",
        "api": "openai",
        "base_url": "http://127.0.0.1:11434/v1",
        "max_tokens": 1024,
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
        "max_tokens": 1024,
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
        "max_tokens": 1024,
        "timeout_s": 120,
        "temperature": 0,
    },
]


def canonical_sha(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def arm_for(seed: int, panelist: str, item_id: str) -> str:
    digest = hashlib.sha256(f"{seed}|{panelist}|{item_id}".encode()).digest()
    return "ainglish" if digest[0] % 2 else "english"


def choose_seed(items: list[dict]) -> tuple[int, dict]:
    real = [row for row in items if not row.get("calibration")]
    for seed in range(2026082300, 2027082300):
        report = {}
        acceptable = True
        for reader in READERS:
            marked = [row for row in real if arm_for(seed, reader["name"], row["id"]) == "ainglish"]
            by_probe = Counter(row["probe"] for row in marked)
            by_form = Counter(row["form"] for row in marked)
            if len(marked) != 50:
                acceptable = False
                break
            if not (22 <= by_form["each-alone"] <= 28 and 22 <= by_form["as-one"] <= 28):
                acceptable = False
                break
            bounds = {
                "action_count": (21, 29),
                "timing_overread": (7, 13),
                "amount_transfer": (7, 13),
                "participation_overread": (3, 7),
            }
            if any(not (lo <= by_probe[key] <= hi) for key, (lo, hi) in bounds.items()):
                acceptable = False
                break
            report[reader["name"]] = {
                "ainglish": len(marked),
                "english": len(real) - len(marked),
                "ainglish_by_form": dict(by_form),
                "ainglish_by_probe": dict(by_probe),
            }
        if acceptable:
            return seed, report
    raise RuntimeError("no balanced seed found")


def main() -> None:
    payload = json.loads(ITEMS_PATH.read_text(encoding="utf-8"))
    items = payload["items"]
    receipt = json.loads((ROOT / "freeze-receipt.json").read_text(encoding="utf-8"))
    expected = receipt["files"][0]["items_sha256"]
    assert canonical_sha(items) == expected
    seed, assignment = choose_seed(items)
    items_location = PUBLIC_ITEMS_URL or str(ITEMS_PATH)
    spec = {
        "construct": "each-alone / as-one flagship full-comparator diagnostic",
        "slug": SLUG,
        "metric": "comprehension_accuracy_delta",
        "seed": seed,
        "planted_arm": "ainglish",
        "calibration_min_gap": 0.5,
        "panel_neff": 1,
        "panel": [dict(reader, seed=seed) for reader in READERS],
        "items_url": items_location,
        "items_sha256": expected,
        "attempt": {
            "proposal_revision": SLUG,
            "estimand": (
                "Post-ratification flagship diagnostic: the percentage-point difference in exact "
                "recovery between each-alone/as-one and their complete registered careful-English "
                "mappings over 100 fresh meaning-matched rows. The primary interpretation is "
                "non-inferiority at -5 percentage points. Probe strata separately retain action "
                "count, timing over-read, amount transfer, and member-participation over-read. "
                "Bare plurals are outside this claim carrier and remain descriptive only."
            ),
            "admissibility_gates": [
                f"the frozen complete item array hashes to {expected}; it contains exactly 100 real rows and 16 calibration rows",
                "all scientific English arms state the complete registered careful-English meaning; no ambiguous bare plural enters the claim carrier",
                "the 100 real rows contain exactly 50 each-alone and 50 as-one rows; probe counts are action 50, timing 20, amount 20, participation 10; every answer position occurs 25 times",
                "the deterministic assignment gives each reader exactly 50 marked and 50 careful-English real cells, with both forms and all four probe types represented inside each arm",
                "all three Q4_K_M reader artifacts match their declared Ollama digests; temperature and reader seed are fixed and the 4,096-token task configurations are digest-pinned",
                "immediately before minting, the shared loopback Ollama endpoint at 127.0.0.1:11434 has an empty loaded-model/request queue and at least one RTX 3090 has 20 GiB free VRAM; otherwise wait without minting",
                "the construct-free calibration block executes first in both arms for every reader and must show an explicit-minus-unresolved accuracy gap of at least 0.5",
                "no reader receives repository access, retrieval, conversation history, or the register definition beyond the presented cell",
                "all null, adverse, supportive, ceiling-bound, and floor-bound scientific outcomes are retained; only frozen-input, instrument-binding, calibration, cell-yield, transport, manifest-commitment, or declared GPU-contract failures may abort",
            ],
            "planned_sample": {
                "comparison": "registered marker versus complete careful-English mapping",
                "real_items": 100,
                "calibration_items": 16,
                "real_reader_cells": 300,
                "calibration_reader_cells": 96,
                "forms": {"each-alone": 50, "as-one": 50},
                "probes": {
                    "action_count": 50,
                    "timing_overread": 20,
                    "amount_transfer": 20,
                    "participation_overread": 10,
                },
                "readers": [reader["name"] for reader in READERS],
                "reader_lineages": ["Mistral Small 3.2 24B", "Gemma 3 12B", "Qwen 2.5 7B"],
                "panel_neff": 1,
                "noninferiority_margin_pp": -5,
                "assignment": assignment,
            },
        },
    }
    path = ROOT / "runspec.json"
    path.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"path": str(path), "seed": seed, "assignment": assignment}, indent=2))


if __name__ == "__main__":
    main()
