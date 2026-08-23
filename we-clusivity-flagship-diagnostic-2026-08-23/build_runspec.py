#!/usr/bin/env python3
"""Build separate preregistration-ready clusivity runspecs for both forms."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SLUG = "we-including-you-we-excluding-you-clusivity-mark-whether-we--4"
FORMS = ("we-including-you", "we-excluding-you")
PROBES = (
    "obligation_routing",
    "permission_routing",
    "commitment_membership",
    "completed_action_membership",
    "notification_membership",
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


def choose_seed(items: list[dict], start: int) -> tuple[int, dict]:
    real = [row for row in items if not row.get("calibration")]
    for seed in range(start, start + 1_000_000):
        report = {}
        acceptable = True
        for reader in READERS:
            marked = [row for row in real if arm_for(seed, reader["name"], row["id"]) == "ainglish"]
            by_probe = Counter(row["probe"] for row in marked)
            if len(marked) != 50 or any(not 8 <= by_probe[probe] <= 12 for probe in PROBES):
                acceptable = False
                break
            report[reader["name"]] = {
                "ainglish": len(marked),
                "english": len(real) - len(marked),
                "ainglish_by_probe": dict(by_probe),
            }
        if acceptable:
            return seed, report
    raise RuntimeError("no balanced assignment seed found")


def build(form: str, freeze_commit: str | None) -> dict:
    items_path = ROOT / f"{form}-items.json"
    items = json.loads(items_path.read_text(encoding="utf-8"))["items"]
    receipt = json.loads((ROOT / "freeze-receipt.json").read_text(encoding="utf-8"))
    entry = next(row for row in receipt["files"] if row["path"] == items_path.name)
    expected = entry["items_sha256"]
    assert canonical_sha(items) == expected
    seed_start = 2026082300 if form == FORMS[0] else 2027082300
    seed, assignment = choose_seed(items, seed_start)
    items_url = (
        f"https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{freeze_commit}/"
        f"we-clusivity-flagship-diagnostic-2026-08-23/{items_path.name}"
        if freeze_commit
        else str(items_path)
    )
    meaning = "included in" if form == FORMS[0] else "excluded from"
    return {
        "construct": f"{form} flagship full-comparator diagnostic",
        "slug": SLUG,
        "metric": "comprehension_accuracy_delta",
        "seed": seed,
        "planted_arm": "ainglish",
        "calibration_min_gap": 0.5,
        "panel_neff": 1,
        "panel": [dict(reader, seed=seed) for reader in READERS],
        "items_url": items_url,
        "items_sha256": expected,
        "attempt": {
            "proposal_revision": SLUG,
            "estimand": (
                f"Post-ratification flagship diagnostic for {form}: the percentage-point difference "
                f"in exact participant-set and routed-consequence recovery between the marker and its "
                f"complete registered careful-English mapping over 100 fresh meaning-matched rows. "
                f"The reader is {meaning} the relevant first-person plural group. Non-inferiority at "
                "-5 percentage points is the standalone primary interpretation for this form. Bare we "
                "and over-read controls are outside this scalar."
            ),
            "admissibility_gates": [
                f"the frozen {form} item array hashes to {expected}; it contains exactly 100 real rows and 16 construct-free calibration rows",
                "every scientific English arm states the complete registered careful-English participant-set meaning; ambiguous bare we is absent from the carrier",
                f"all 100 real rows test {form}; each of five routing probes has 20 rows and every answer position occurs 25 times",
                "the warm-team-tone distractor directly tests semantic bleaching and receives no credit unless exact participant-set consequence is recovered",
                "the deterministic assignment gives each reader exactly 50 marked and 50 careful-English real cells, with 8 to 12 marked cells in every probe",
                "the sibling clusivity form, its runspec, and its execution commitment are frozen before either scientific run; both forms execute regardless of the first form's scientific direction",
                "all three Q4_K_M reader artifacts match their declared Ollama digests; temperature and reader seed are fixed and the 4,096-token task configurations are digest-pinned",
                "immediately before minting, the shared loopback Ollama endpoint at 127.0.0.1:11434 has an empty loaded-model/request queue and at least one RTX 3090 has 20 GiB free VRAM; otherwise wait without minting",
                "the construct-free calibration block executes first in both arms for every reader and must show an explicit-minus-unresolved accuracy gap of at least 0.5",
                "no reader receives repository access, retrieval, conversation history, the human face-validity note, or the register definition beyond the presented cell",
                "all null, adverse, supportive, ceiling-bound, and floor-bound scientific outcomes are retained; only frozen-input, instrument-binding, calibration, cell-yield, transport, manifest-commitment, or declared GPU-contract failures may abort",
            ],
            "planned_sample": {
                "comparison": f"{form} versus its complete registered careful-English mapping",
                "real_items": 100,
                "calibration_items": 16,
                "real_reader_cells": 300,
                "calibration_reader_cells": 96,
                "form": form,
                "probes": {probe: 20 for probe in PROBES},
                "readers": [reader["name"] for reader in READERS],
                "reader_lineages": ["Mistral Small 3.2 24B", "Gemma 3 12B", "Qwen 2.5 7B"],
                "panel_neff": 1,
                "noninferiority_margin_pp": -5,
                "assignment": assignment,
            },
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze-commit", help="40-hex immutable public commit")
    args = parser.parse_args()
    if args.freeze_commit and (len(args.freeze_commit) != 40 or any(ch not in "0123456789abcdef" for ch in args.freeze_commit)):
        raise SystemExit("--freeze-commit must be a lowercase 40-hex commit")
    output = {}
    for form in FORMS:
        spec = build(form, args.freeze_commit)
        path = ROOT / f"runspec-{form}.json"
        path.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        output[form] = {"path": str(path), "seed": spec["seed"], "items_sha256": spec["items_sha256"]}
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
