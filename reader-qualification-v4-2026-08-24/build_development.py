#!/usr/bin/env python3
"""Freeze the v4 development screen without making model calls."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT.parent
SOURCE = EVIDENCE / "reader-qualification-v3-2026-08-24" / "development.json"
OUT = ROOT / "development.json"


def main() -> None:
    prior = json.loads(SOURCE.read_text())
    spec = {
        "kind": "ainglish.panel.reader-qualification-development.v4",
        "result_kind": "ainglish.panel.reader-qualification-development-result.v4",
        "purpose": "Develop one previously untested Qwen 3.5 9B reader edition before freezing a disjoint v4 holdout.",
        "evidentiary_status": "instrument development only; never proposal evidence or a qualification result",
        "sdk_version": "0.2.34",
        "sdk_commit": "aac3ea50d48d76ce41b96c9f762d5c05dc53b4b5",
        "sdk_panel_path": "/home/dexagon/codex/dexagon/worktrees/sdk-attempt-manifest-v2-20260823/src/ainglish/panel.py",
        "answer_protocol": "opaque-choice-v1",
        "axes": prior["axes"],
        "items_per_axis": prior["items_per_axis"],
        "forbidden_construct_terms": prior["forbidden_construct_terms"],
        "disjoint_from_specs": [
            "/home/dexagon/codex/dexagon/ainglish-evidence/reader-qualification-tournament-2026-08-23/spec.json",
            "/home/dexagon/codex/dexagon/ainglish-evidence/reader-qualification-v2-2026-08-24/holdout.json",
            "/home/dexagon/codex/dexagon/ainglish-evidence/reader-qualification-v3-2026-08-24/holdout.json"
        ],
        "development_reuse": "The exposed v3 development controls are deliberately reused only for development; no qualification claim is made from them.",
        "gpu_gate": prior["gpu_gate"],
        "selection_rule": {
            "exact_code_cells_required": 24,
            "correct_cells_required": 22,
            "correct_per_axis_required": 3,
            "minimum_distinct_qualified_lineages": 1,
            "status": "development diagnostic only; final qualification is frozen separately on an untouched holdout"
        },
        "panel": [
            {
                "name": "qwen3.5-9b-literal-bound1024-q4_k_m",
                "lineage": "Qwen 3.5 9B",
                "provider": "ollama",
                "model": "qwen3.5:9b-q4_k_m",
                "model_digest": "sha256:6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7",
                "precision": "q4_k_m",
                "max_tokens": 1024,
                "timeout_s": 120,
                "temperature": 0,
                "seed": 2026082404,
                "api": "openai",
                "base_url": "http://127.0.0.1:11434/v1"
            }
        ],
        "items": prior["items"]
    }
    OUT.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"output": str(OUT), "items": len(spec["items"]), "reader_calls": 0}, indent=2))


if __name__ == "__main__":
    main()
