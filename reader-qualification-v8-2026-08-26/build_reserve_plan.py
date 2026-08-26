#!/usr/bin/env python3
"""Freeze the one high-capacity thinking-optional reserve without tuning the gate."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import urllib.request

from build_development_plans import ENDPOINT, canonical, checked, get, post


ROOT = Path(__file__).resolve().parent
SOURCE_MODEL = "qwen3.6:35b"


def main() -> None:
    base = checked(ROOT / "development-phi-plan.json")
    tags = {row["name"]: row for row in get("/api/tags").get("models", [])}
    tag = tags.get(SOURCE_MODEL)
    if tag is None:
        raise SystemExit("REFUSING: qwen reserve is not installed")
    shown = post("/api/show", {"model": SOURCE_MODEL})
    capabilities = shown.get("capabilities") or []
    if "thinking" not in capabilities:
        raise SystemExit("REFUSING: reserve capability assumptions changed")
    details = shown.get("details") or {}
    document = copy.deepcopy(base)
    document.pop("content_sha256")
    document["kind"] = "ainglish.panel.reader-v8-thinking-optional-reserve-plan.v1"
    document["phase"] = "development-qwen35-reserve"
    document["freeze_rule"] = "Commit and push this reserve plan before its first call; use the unchanged primary prompt and gates, transmit think:false, and fail on any returned thinking byte."
    document["candidate"] = {
        "lineage": "Qwen 3.6 35B",
        "producer": "Alibaba Cloud",
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
        "official_reference": "local digest-pinned Ollama qwen3.6:35b artifact",
        "independence_caveat": "Distinct from the sole passing Phi family; related Qwen editions appeared in older development screens but never this prospective transport and holdout branch.",
        "advertised_thinking_policy": "capability allowed only with transmitted think:false and zero returned thinking bytes",
    }
    document["result_file"] = "development-qwen35-reserve-result.json"
    document["journal_file"] = "development-qwen35-reserve-attempt-journal.jsonl"
    document["content_sha256"] = hashlib.sha256(canonical(document)).hexdigest()
    target = ROOT / "development-qwen35-reserve-plan.json"
    if target.exists():
        if checked(target) != document:
            raise SystemExit("REFUSING: frozen reserve plan drift")
    else:
        target.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    index = {
        "kind": "ainglish.panel.reader-v8-reserve-index.v1",
        "trigger": "exactly one of four primary development candidates passed the unchanged gate",
        "plan": {"file": target.name, "content_sha256": document["content_sha256"]},
        "selection_basis": "strongest already-installed distinct family; avoids a new download",
        "threshold_changes": 0,
        "model_calls": 0,
    }
    index["content_sha256"] = hashlib.sha256(canonical(index)).hexdigest()
    index_path = ROOT / "reserve-index.json"
    if index_path.exists():
        if checked(index_path) != index:
            raise SystemExit("REFUSING: reserve index drift")
    else:
        index_path.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(index, indent=2))


if __name__ == "__main__":
    main()

