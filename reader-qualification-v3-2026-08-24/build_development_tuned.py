#!/usr/bin/env python3
"""Freeze the sole v3 development-stage reader-configuration revision."""

from __future__ import annotations

import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "development-tuned.json"


def main() -> None:
    if OUT.exists():
        raise SystemExit("REFUSING: development-tuned.json already exists")
    source = json.loads((ROOT / "development.json").read_text(encoding="utf-8"))
    spec = copy.deepcopy(source)
    spec.update({
        "kind": "ainglish.panel.reader-qualification-development-tuned.v3",
        "result_kind": "ainglish.panel.reader-qualification-development-tuned-result.v3",
        "purpose": "Test the sole construct-blind reader configuration revision on the exposed development controls before any holdout exists.",
        "development_round_one_result_sha256": "91856788967d910569ab7a8e9fc6bcc99c73c315580c575d9c08657eee89af41",
        "revision_policy": "same exposed development items; no scientific or holdout item exists; no further revision after this round",
        "panel": [
            {
                "name": "qwen3.8-27b-screen-bound1024-q4_k_m", "lineage": "Qwen 3.8 27B", "provider": "ollama",
                "model": "dexagon-qwen3.8-27b-screen:ctx4k",
                "model_digest": "sha256:97a12d32a43050d86486d7d3a4253036603e5209ae717da488f95b46c704df47",
                "precision": "q4_k_m", "max_tokens": 1024, "timeout_s": 120,
                "temperature": 0, "seed": 2026082403, "api": "openai", "base_url": "http://127.0.0.1:11434/v1",
            },
            {
                "name": "qwen2.5-7b-entailment-v3-q4_k_m", "lineage": "Qwen 2.5 7B", "provider": "ollama",
                "model": "dexagon-qwen2.5-7b-entailment-v3:ctx4k",
                "model_digest": "sha256:fbffa558f9909a4681e595204a0661648ba631fd4024ae3fbc0be86ff2f6247a",
                "precision": "q4_k_m", "max_tokens": 16, "timeout_s": 120,
                "temperature": 0, "seed": 2026082403, "api": "openai", "base_url": "http://127.0.0.1:11434/v1",
            },
        ],
    })
    OUT.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"path": str(OUT), "items": len(spec["items"]), "panel": [row["name"] for row in spec["panel"]]}))


if __name__ == "__main__":
    main()
