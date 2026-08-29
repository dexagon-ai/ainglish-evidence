#!/usr/bin/env python3
"""Run one frozen Command R stage once, with exact host and development gates."""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
GENERIC = REPO / "reader-fresh-lineage-v1-2026-08-26"
sys.path.insert(0, str(GENERIC))
spec = importlib.util.spec_from_file_location("generic_command_r_runner", GENERIC / "run_candidate_once.py")
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def validate(plan: dict) -> tuple[dict, dict]:
    packet = module.checked(REPO / plan["semantic_stage"]["packet"]["file"])
    if packet["content_sha256"] != plan["semantic_stage"]["packet"]["content_sha256"]:
        raise SystemExit("REFUSING: semantic packet drift")
    development_receipt = None
    if plan["phase"] == "holdout-command-r":
        gate = plan["development_gate"]
        development_plan = module.checked(ROOT / gate["plan_file"])
        if development_plan["content_sha256"] != gate["plan_sha256"]:
            raise SystemExit("REFUSING: development-plan binding drift")
        development = module.checked(ROOT / gate["result_file"])
        if (
            development.get("plan_sha256") != development_plan["content_sha256"]
            or development.get("candidate") != plan["candidate"]
            or development.get("v8_holdout_eligible") is not True
            or (development.get("semantic") or {}).get("passed") is not True
        ):
            raise SystemExit("REFUSING: exact Command R development gate did not pass")
        development_receipt = development["content_sha256"]
    elif plan["phase"] != "development-command-r-35b":
        raise SystemExit("REFUSING: unknown Command R stage")

    devices = module.gpu_rows()
    gpu_gate = plan["gpu_gate"]
    if (
        sum(row["free_mib"] for row in devices) < gpu_gate["minimum_total_free_mib"]
        or max(row["utilization"] for row in devices) > gpu_gate["maximum_utilization_percent"]
    ):
        raise SystemExit("REFUSING: GPU gate")
    endpoint = gpu_gate["ollama_base_url"].rstrip("/")
    version = module.get(endpoint, "/api/version").get("version")
    if version != plan["runtime"]["ollama_version"]:
        raise SystemExit("REFUSING: Ollama version drift")
    if module.get(endpoint, "/api/ps").get("models"):
        raise SystemExit("REFUSING: resident Ollama model")
    tags = {row["name"]: row["digest"] for row in module.get(endpoint, "/api/tags").get("models", [])}
    candidate = plan["candidate"]
    if tags.get(candidate["source_model"]) != candidate["source_manifest_sha256"]:
        raise SystemExit("REFUSING: candidate manifest drift")
    shown = module.post(endpoint, "/api/show", {"model": candidate["source_model"]})
    capabilities = shown.get("capabilities") or []
    if capabilities != candidate["capabilities"] or "thinking" in capabilities:
        raise SystemExit("REFUSING: candidate capability drift")
    details = shown.get("details") or {}
    observed_details = {
        "family": details.get("family"),
        "families": details.get("families"),
        "parameter_size": details.get("parameter_size"),
        "quantization_level": details.get("quantization_level"),
        "format": details.get("format"),
        "parent_model": details.get("parent_model"),
    }
    if observed_details != candidate["details"]:
        raise SystemExit("REFUSING: candidate details drift")
    template = shown.get("template") or ""
    if (
        len(template) != candidate["template_length_chars"]
        or hashlib.sha256(template.encode()).hexdigest() != candidate["template_sha256"]
    ):
        raise SystemExit("REFUSING: candidate template drift")
    if plan["transport"].get("think") is not False:
        raise SystemExit("REFUSING: think:false transport drift")
    return packet, {
        "devices": devices,
        "resident_before": [],
        "ollama_version": version,
        "template_sha256": candidate["template_sha256"],
        "development_result_sha256": development_receipt,
    }


module.ROOT = ROOT
module.REPO = REPO
module.validate = validate


if __name__ == "__main__":
    module.main()
