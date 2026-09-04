#!/usr/bin/env python3
"""Derive a local, independently qualified two-reader runspec from frozen items."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
QUAL_ROOT = ROOT.parent / "reader-qualification-local-v1-2026-09-04"
OUTPUT = ROOT / "runspec-local-qualified.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    spec = load(ROOT / "runspec.json")
    screens = [load(QUAL_ROOT / name) for name in ("mistral-screen.json", "gemma-screen.json")]
    receipts = [
        load(QUAL_ROOT / name)["receipt"]
        for name in ("mistral-qualification.json", "gemma-qualification.json")
    ]
    spec["kind"] = "dexagon.ainglish.snapshot-live-qualified-local-runspec.v1"
    spec["seed"] = 2026090406
    spec["panel_neff"] = 2
    spec["panel"] = [screen["reader"] for screen in screens]
    spec["models"] = [receipt["roster_id"] for receipt in receipts]
    spec["reader_qualifications"] = receipts
    spec["comparison_identity"] = {
        "comparator_genre": "complete-careful-English-v1",
        "pair_rendering": "held-out joint implementation-and-consequence choice",
        "reader_roster": spec["models"],
        "form_strata": ["send-snapshot", "grant-live-view"],
    }
    spec["concurrency"] = {
        "max_in_flight": 2,
        "per_reader_max_in_flight": {
            screens[0]["reader"]["name"]: 1,
            screens[1]["reader"]["name"]: 1,
        },
    }
    spec["training_asymmetry"] = (
        "These present local readers were trained primarily on ordinary English and are not "
        "assumed to have seen Ainglish. This measures current zero-shot comprehension, not "
        "expected efficiency after future Ainglish-aware training."
    )
    attempt = spec["attempt"]
    attempt["admissibility_gates"] = [
        "authenticated suggestions still request this exact original comprehension_accuracy_delta immediately before mint",
        "the proposal remains current at measured stage and the executing principal is not its proposer",
        "the public 144+8 carrier hashes to the already-published digest and preserves all declared balances",
        "every scenario exposes two separately recoverable questions and a complete four-way Cartesian answer set",
        "both exact local reader configurations retain passing target-independent qualification receipts at mint time",
        "the reader artifacts still match their declared Ollama sha256 digests",
        "construct-free calibration executes first and each reader must show an explicit-minus-unresolved gap of at least 0.5",
        "zero transport faults, response-bound truncations, or missing scientific cells are required",
        "absolute arms, replayable interval, all settlement strata, report cells, and normalized answers are retained",
        "every finite supportive, null, adverse, floor-bound, ceiling-bound, or inconclusive outcome is filed exactly once",
        "bare share is never used as an accuracy comparator against a hidden intended topology",
    ]
    planned = attempt["planned_sample"]
    planned.update(
        {
            "readers": 2,
            "reader_lineages": [receipt["lineage"]["key"] for receipt in receipts],
            "panel_members": 2,
            "panel_neff": 2,
            "real_cells": 288,
            "calibration_cells": 32,
            "sdk_commit": "9bb31166b7b99b5d0a399f0b8001c8fceba7f885",
            "qualification_commit": "00226c0",
        }
    )
    encoded = json.dumps(spec, indent=2, ensure_ascii=False).encode() + b"\n"
    OUTPUT.write_bytes(encoded)
    print(json.dumps({"output": OUTPUT.name, "sha256": hashlib.sha256(encoded).hexdigest()}))


if __name__ == "__main__":
    main()
