#!/usr/bin/env python3
"""Run a v8 holdout plan, permitting thinking capability only when explicitly disabled."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
GENERIC = ROOT.parent / "reader-fresh-lineage-v1-2026-08-26"
sys.path.insert(0, str(GENERIC))
spec = importlib.util.spec_from_file_location("generic_holdout_runner", GENERIC / "run_candidate_once.py")
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def validate(plan: dict) -> tuple[dict, dict]:
    packet = module.checked(ROOT.parent / plan["semantic_stage"]["packet"]["file"])
    if packet["content_sha256"] != plan["semantic_stage"]["packet"]["content_sha256"]:
        raise SystemExit("REFUSING: holdout drift")
    devices = module.gpu_rows()
    gate = plan["gpu_gate"]
    if sum(row["free_mib"] for row in devices) < gate["minimum_total_free_mib"] or max(row["utilization"] for row in devices) > gate["maximum_utilization_percent"]:
        raise SystemExit("REFUSING: GPU gate")
    endpoint = gate["ollama_base_url"].rstrip("/")
    if module.get(endpoint, "/api/version").get("version") != plan["runtime"]["ollama_version"]:
        raise SystemExit("REFUSING: Ollama version drift")
    if module.get(endpoint, "/api/ps").get("models"):
        raise SystemExit("REFUSING: resident Ollama model")
    tags = {row["name"]: row["digest"] for row in module.get(endpoint, "/api/tags").get("models", [])}
    candidate = plan["candidate"]
    if tags.get(candidate["source_model"]) != candidate["source_manifest_sha256"]:
        raise SystemExit("REFUSING: candidate manifest drift")
    capabilities = module.post(endpoint, "/api/show", {"model": candidate["source_model"]}).get("capabilities") or []
    if capabilities != candidate["capabilities"]:
        raise SystemExit("REFUSING: candidate capability drift")
    if "thinking" in capabilities and "advertised_thinking_policy" not in candidate:
        raise SystemExit("REFUSING: undeclared thinking capability")
    if plan["transport"].get("think") is not False or plan["semantic_stage"]["gate"]["thinking_bytes_required"] != 0:
        raise SystemExit("REFUSING: thinking gate drift")
    return packet, {"devices": devices, "resident_before": [], "ollama_version": plan["runtime"]["ollama_version"]}


module.ROOT = ROOT
module.REPO = ROOT.parent
module.validate = validate
module.main()

