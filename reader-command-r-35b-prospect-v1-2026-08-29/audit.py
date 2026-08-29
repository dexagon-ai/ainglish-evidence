#!/usr/bin/env python3
"""Statically audit both Command R plans before any reader call."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    unsigned = dict(value)
    expected = unsigned.pop("content_sha256", None)
    if hashlib.sha256(canonical(unsigned)).hexdigest() != expected:
        raise SystemExit(f"REFUSING: digest drift at {path}")
    return value


def main() -> None:
    development = checked(ROOT / "development-command-r-plan.json")
    holdout = checked(ROOT / "holdout-command-r-plan.json")
    index = checked(ROOT / "index.json")
    if development["candidate"] != holdout["candidate"]:
        raise SystemExit("REFUSING: candidate drift between stages")
    candidate = development["candidate"]
    if (
        candidate["source_manifest_sha256"]
        != "376304b5a50577f311bfc4fb75cc1217e71b77906b48bb07b652647af760a7bd"
        or candidate["capabilities"] != ["completion", "tools"]
        or candidate["template_sha256"]
        != "922095537bc1278418b3aeff5c9bdde0c61a5c6adb7573498b09791a95044068"
    ):
        raise SystemExit("REFUSING: non-answer-bearing candidate binding drift")
    adverse = development["prior_evidence"]["construct_specific_adverse_calibration"]
    if (
        adverse != holdout["prior_evidence"]["construct_specific_adverse_calibration"]
        or adverse["commit"] != "6c32a4a75c30c1e1feb41baba79f884857104974"
        or adverse["raw_sha256"] != "574e90833f4e0a25ed88a35ad0aa8b0e01be4ba79fb6ef327225270f5d57b1b5"
        or adverse["command_r_gap"] != 0
        or adverse["real_cells_attempted"] != 0
    ):
        raise SystemExit("REFUSING: disclosed adverse prior drift")
    format_source = checked(REPO / development["format_stage"]["source_plan"]["file"])
    development_packet = checked(REPO / development["semantic_stage"]["packet"]["file"])
    holdout_packet = checked(REPO / holdout["semantic_stage"]["packet"]["file"])
    if (
        development["format_stage"]["source_plan"]["content_sha256"] != format_source["content_sha256"]
        or development["format_stage"]["controls"] != format_source["controls"]
        or holdout["format_stage"] != development["format_stage"]
        or development["semantic_stage"]["packet"]["content_sha256"] != development_packet["content_sha256"]
        or holdout["semantic_stage"]["packet"]["content_sha256"] != holdout_packet["content_sha256"]
    ):
        raise SystemExit("REFUSING: frozen instrument binding drift")
    if (
        development["semantic_stage"]["gate"]["correct_cells_required"] != 22
        or holdout["semantic_stage"]["gate"]["correct_cells_required"] != 60
        or development["transport"]["max_tokens"] != 16
        or holdout["transport"]["max_tokens"] != 16
        or development["transport"]["think"] is not False
        or holdout["transport"]["think"] is not False
    ):
        raise SystemExit("REFUSING: gate or transport drift")
    if holdout["development_gate"] != {
        "plan_file": "development-command-r-plan.json",
        "plan_sha256": development["content_sha256"],
        "result_file": "development-command-r-result.json",
        "required": "sealed result binds the exact candidate and plan, with v8_holdout_eligible=true",
    }:
        raise SystemExit("REFUSING: conditional holdout activation drift")
    if index["plans"] != [
        {"file": "development-command-r-plan.json", "content_sha256": development["content_sha256"], "activation": "next"},
        {"file": "holdout-command-r-plan.json", "content_sha256": holdout["content_sha256"], "activation": "only after exact development pass"},
    ]:
        raise SystemExit("REFUSING: index/plan drift")
    report = {
        "kind": "ainglish.panel.reader-command-r-prospect-audit.v1",
        "status": "passed-static",
        "development_plan_sha256": development["content_sha256"],
        "holdout_plan_sha256": holdout["content_sha256"],
        "adverse_prior_disclosed": True,
        "holdout_conditioned_on_development_pass": True,
        "development_items": len(development_packet["items"]),
        "holdout_items": len(holdout_packet["items"]),
        "model_calls": 0,
        "model_downloads": 0,
        "network_calls": 0,
    }
    report["content_sha256"] = hashlib.sha256(canonical(report)).hexdigest()
    (ROOT / "audit.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
