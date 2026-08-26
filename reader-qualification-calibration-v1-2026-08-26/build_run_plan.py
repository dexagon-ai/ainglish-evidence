#!/usr/bin/env python3
"""Freeze the development calibration run over the six already-pinned v7 readers."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "reader-qualification-v7-2026-08-25"
SOURCE_SPECS = ("phase-a-holdout.json", "reserve-b-holdout.json", "final-reserve-holdout.json")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    sealed = dict(value)
    expected = sealed.pop("content_sha256")
    if hashlib.sha256(canonical(sealed)).hexdigest() != expected:
        raise SystemExit(f"REFUSING: digest drift in {path}")
    return value


def build() -> dict:
    packet = checked(ROOT / "development-packet.json")
    panels = []
    receipts = []
    for name in SOURCE_SPECS:
        spec = checked(SOURCE / name)
        receipts.append({"file": name, "content_sha256": spec["content_sha256"]})
        panels.extend(spec["panel"])
    if len(panels) != 6 or len({row["name"] for row in panels}) != 6 or len({row["lineage"] for row in panels}) != 6:
        raise SystemExit("REFUSING: expected six distinct v7 readers and lineages")
    projection_keys = (
        "name", "lineage", "producer", "source_model", "source_manifest_sha256",
        "model", "model_digest", "source_capabilities", "wrapper_capabilities",
        "max_tokens", "timeout_s", "temperature", "num_ctx",
    )
    panel = [{key: row[key] for key in projection_keys} for row in panels]
    document = {
        "kind": "ainglish.panel.reader-qualification-development-run-plan.v1",
        "result_kind": "ainglish.panel.reader-qualification-development-result.v1",
        "evidentiary_status": "development-only exposed controls; never qualification or proposal evidence",
        "freeze_rule": "Commit and push this plan and its bound packet before the first model call. Attempt every reader-item cell at most once and retain every outcome.",
        "packet": {"file": "development-packet.json", "content_sha256": packet["content_sha256"]},
        "source_directory": SOURCE.name,
        "source_reader_specs": receipts,
        "transport": {
            "adapter": "ollama-native-chat-v1",
            "think": False,
            "temperature": 0,
            "seed": 2026082617,
            "num_ctx": 4096,
            "max_tokens": 4,
            "timeout_s": 300,
        },
        "gpu_gate": {
            "ollama_base_url": "http://127.0.0.1:11434",
            "minimum_total_free_mib": 36000,
            "maximum_utilization_percent": 35,
        },
        "panel": panel,
        "reporting_rule": "Report exact-code, label accuracy, per-axis accuracy, thinking bytes, and fault cells descriptively. This run cannot qualify a reader.",
    }
    document["content_sha256"] = hashlib.sha256(canonical(document)).hexdigest()
    return document


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    document = build()
    target = ROOT / "run-plan.json"
    if args.write:
        if target.exists():
            raise SystemExit("REFUSING: run-plan.json already exists")
        target.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"readers": len(document["panel"]), "sha256": document["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
