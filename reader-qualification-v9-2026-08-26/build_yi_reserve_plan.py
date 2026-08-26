#!/usr/bin/env python3
"""Freeze the prospective Yi reserve plan after install and before its first call."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from build_development_plan import canonical, checked, get, post


ROOT = Path(__file__).resolve().parent
SOURCE_MODEL = "yi:34b"


def main() -> None:
    runtime = get("/api/version").get("version")
    if runtime != "0.32.7":
        raise SystemExit(f"REFUSING: Ollama version drift {runtime}")
    tags = {row["name"]: row for row in get("/api/tags").get("models", [])}
    tag = tags.get(SOURCE_MODEL)
    if tag is None:
        raise SystemExit(f"REFUSING: missing installed reserve {SOURCE_MODEL}")
    shown = post("/api/show", {"model": SOURCE_MODEL})
    capabilities = shown.get("capabilities") or []
    if "thinking" in capabilities:
        raise SystemExit(f"REFUSING: thinking capability on {SOURCE_MODEL}")
    details = shown.get("details") or {}
    plan = checked(ROOT / "development-lfm2-plan.json")
    plan.pop("content_sha256")
    plan.update({
        "kind": "ainglish.panel.reader-v9-reserve-development-plan.v1",
        "result_kind": "ainglish.panel.reader-v9-reserve-development-result.v1",
        "phase": "development-yi-reserve",
        "freeze_rule": "LFM2's retained failure activated this preregistered reserve. Commit and push this exact Yi plan before its first call; never tune or retry after observation.",
        "candidate": {
            "lineage": "Yi 1.5 34B",
            "producer": "01.AI",
            "source_model": SOURCE_MODEL,
            "source_manifest_sha256": tag["digest"],
            "capabilities": capabilities,
            "details": {
                "family": details.get("family"),
                "families": details.get("families"),
                "parameter_size": details.get("parameter_size"),
                "quantization_level": details.get("quantization_level"),
                "format": details.get("format"),
            },
            "official_reference": "https://ollama.com/library/yi:34b",
            "independence_caveat": "Distinct 01.AI-trained Yi lineage from Qwen and Liquid LFM2; Ollama labels the underlying architecture llama, and local serving/harness remain shared infrastructure.",
        },
        "result_file": "development-yi-reserve-result.json",
        "journal_file": "development-yi-reserve-attempt-journal.jsonl",
    })
    plan["runtime"]["ollama_version"] = runtime
    plan["transport"]["seed"] = 2026082642
    plan["content_sha256"] = hashlib.sha256(canonical(plan)).hexdigest()
    target = ROOT / "development-yi-reserve-plan.json"
    if target.exists():
        if checked(target) != plan:
            raise SystemExit("REFUSING: frozen Yi reserve plan drift")
    else:
        target.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    failed_result = checked(ROOT / "development-lfm2-result.json")
    index = {
        "kind": "ainglish.panel.reader-v9-reserve-index.v1",
        "activation_receipt": {
            "failed_plan": "development-lfm2-plan.json",
            "failed_result": "development-lfm2-result.json",
            "failed_result_sha256": failed_result["content_sha256"],
            "development_passed": failed_result["semantic"]["passed"],
        },
        "runner": "reader-qualification-v9-2026-08-26/run_candidate_once.py",
        "auditor": "reader-qualification-v9-2026-08-26/audit_candidate.py",
        "plans": [{
            "file": target.name,
            "lineage": plan["candidate"]["lineage"],
            "content_sha256": plan["content_sha256"],
        }],
        "fresh_holdout_authoring_gate": "Yi passes every development gate; later Yi and Qwen holdout plans are both frozen before either call",
        "model_calls": 0,
    }
    if index["activation_receipt"]["development_passed"] is not False:
        raise SystemExit("REFUSING: LFM2 failure did not activate reserve")
    index["content_sha256"] = hashlib.sha256(canonical(index)).hexdigest()
    index_path = ROOT / "reserve-index.json"
    if index_path.exists():
        if checked(index_path) != index:
            raise SystemExit("REFUSING: frozen reserve index drift")
    else:
        index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(index, indent=2))


if __name__ == "__main__":
    main()
