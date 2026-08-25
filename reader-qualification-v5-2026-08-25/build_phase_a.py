#!/usr/bin/env python3
"""Freeze the Gemma/Llama phase-A holdout before either model sees an item."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import runpy
import urllib.request


ROOT = Path(__file__).resolve().parent
BASE = runpy.run_path(str(ROOT / "build_spec.py"))
MODELS = BASE["MODELS"][:2]
ROWS = BASE["ROWS"]
canonical = BASE["canonical"]
choices = BASE["choices"]


def tags() -> dict[str, str]:
    with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=20) as response:
        return {row["name"]: row["digest"] for row in json.load(response).get("models", [])}


def main() -> None:
    target = ROOT / "phase-a-holdout.json"
    if target.exists():
        raise SystemExit("REFUSING: phase-a-holdout.json already exists")
    known = tags()
    panel = []
    for name, lineage, model, precision in MODELS:
        digest = known.get(model)
        if not digest:
            raise SystemExit(f"REFUSING: model {model} is not installed")
        panel.append({
            "name": name, "lineage": lineage, "provider": "ollama", "model": model,
            "model_digest": f"sha256:{digest}", "precision": precision,
            "max_tokens": 4, "timeout_s": 180, "temperature": 0, "seed": 2026082508,
        })
    items = []
    for axis, rows in ROWS.items():
        for index, (message, question, answer) in enumerate(rows):
            items.append({
                "id": f"v5-hold-{axis}-{index + 1:02d}", "axis": axis,
                "message": message, "question": question,
                "options": choices(answer, index % 3), "answer": answer,
            })
    spec = {
        "kind": "ainglish.panel.reader-qualification-holdout.v5-phase-a",
        "result_kind": "ainglish.panel.reader-qualification-holdout-result.v5-phase-a",
        "phase": {
            "name": "phase-a", "selection": "stability anchor plus first new vendor lineage",
            "reserve_action": "Run the separately declared reserve candidates only if phase A yields fewer than two qualified lineages.",
        },
        "evidentiary_status": "instrument qualification only; never proposal evidence",
        "answer_protocol": "opaque-choice-v1",
        "transport": {"adapter": "ollama-native-chat-v1", "think": False},
        "axes": list(ROWS), "items_per_axis": 8,
        "forbidden_construct_terms": [
            "ainglish", "proxy(", "obs:", "inf:", "rep(", "must-as-", "should-as-",
            "will-as-", "may-not-as-", "all-or-nothing", "keep-successes",
        ],
        "disjoint_from_specs": [
            str(ROOT.parent / "reader-qualification-tournament-2026-08-23/spec.json"),
            str(ROOT.parent / "reader-qualification-v2-2026-08-24/development.json"),
            str(ROOT.parent / "reader-qualification-v2-2026-08-24/holdout.json"),
            str(ROOT.parent / "reader-qualification-v3-2026-08-24/development.json"),
            str(ROOT.parent / "reader-qualification-v3-2026-08-24/holdout.json"),
            str(ROOT.parent / "reader-qualification-v4-2026-08-24/holdout.json"),
        ],
        "gpu_gate": {"ollama_base_url": "http://127.0.0.1:11434", "minimum_total_free_mib": 36000, "maximum_utilization_percent": 35},
        "selection_rule": {
            "exact_code_cells_required": 64, "correct_cells_required": 60,
            "correct_per_axis_required": 7, "minimum_distinct_qualified_lineages": 2,
            "no_roster_action": "Publish every result; if fewer than two lineages qualify, mint no scientific reader campaign and run the reserve phase.",
        },
        "panel": panel, "items": items,
    }
    spec["content_sha256"] = hashlib.sha256(canonical(spec)).hexdigest()
    target.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"items": len(items), "models": len(panel), "reader_calls": 0, "sha256": spec["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
