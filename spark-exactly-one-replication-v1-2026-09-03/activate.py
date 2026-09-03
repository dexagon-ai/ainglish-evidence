#!/usr/bin/env python3
"""Bind the public freeze, canonical receipt-preserving SDK, and Spark reader."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from ainglish import reader_qualification


ROOT = Path(__file__).resolve().parent
SLUG = "one-or-more-role-exactly-one-role-does-a-reviewer-require-at"
TARGET = "31b5db3dc0a4cde2cff904bf96f76894471d5c165aa6eb742e9db7aa27ead10b"


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def commit(value: str, name: str) -> str:
    if len(value) != 40 or any(char not in "0123456789abcdef" for char in value):
        raise SystemExit(f"{name} must be a full lowercase Git commit")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--items-commit", required=True)
    parser.add_argument("--sdk-commit", required=True)
    args = parser.parse_args()
    items_commit = commit(args.items_commit, "items commit")
    sdk_commit = commit(args.sdk_commit, "SDK commit")
    frozen = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    artifact = json.loads((ROOT / frozen["items_file"]).read_text(encoding="utf-8"))
    assert hashlib.sha256(canonical(artifact["items"])).hexdigest() == frozen["items_sha256"]
    assert frozen["replicates_hash"] == TARGET
    qualified = json.loads((ROOT / "spark-qualification.json").read_text(encoding="utf-8"))
    receipt = reader_qualification.validate(qualified["receipt"])
    reader = {
        "name": "spark-zen-13-minimal",
        "provider": "opencode-zen",
        "base_url": "https://opencode.ai/zen/v1",
        "api": "responses",
        "api_key_env": "OPENCODE_API_KEY",
        "model": "muse-spark-1.3-contributor-free",
        "precision": "provider-served",
        "reasoning_effort": "minimal",
        "max_tokens": 1024,
        "timeout_s": 120
    }
    spec = {
        "construct": "exactly-one(role) role-cardinality fresh-input replication versus careful English",
        "slug": SLUG,
        "metric": "comprehension_accuracy_delta",
        "replicates_hash": TARGET,
        "seed": frozen["seed"],
        "planted_arm": "ainglish",
        "calibration_min_gap": 0.5,
        "panel_neff": 1,
        "panel": [reader],
        "models": [receipt["roster_id"]],
        "reader_qualifications": [receipt],
        "comparator": {
            "kind": "complete-careful-english-v1",
            "description": "the shortest complete careful-English expansion of exactly-one(role), explicitly counting distinct qualifying principals."
        },
        "items_url": (
            "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
            f"{items_commit}/spark-exactly-one-replication-v1-2026-09-03/items.json"
        ),
        "items_sha256": frozen["items_sha256"],
        "concurrency": {"max_in_flight": 1, "per_reader_max_in_flight": {reader["name"]: 1}},
        "attempt": {
            "proposal_revision": SLUG,
            "estimand": (
                "Fresh-input replication of original 31b5db3d: exactly-one(role) versus its "
                "complete careful-English expansion over 120 operational role-cardinality items, "
                "equally representing the original twelve semantic cells across ten new roles."
            ),
            "admissibility_gates": [
                f"the target original remains active, valid and routed for replication at {TARGET}",
                f"the 120+8 answer-bearing carrier is frozen at public commit {items_commit} and canonical item digest {frozen['items_sha256']}",
                f"the exact receipt-preserving panel harness is canonical at ai-nglish/ainglish commit {sdk_commit}",
                "Spark's exact OpenCode Zen reader/settings passed the public target-independent screen before target exposure",
                "the attached qualification receipt remains valid and exactly names the declared roster identity",
                "all target complete scientific rows, item IDs, scenario IDs, English arms and Ainglish arms have zero exact intersection with this carrier",
                "the original question templates, twelve semantic cells and careful-English comparator are preserved to hold the estimand fixed",
                "all eight construct-free calibrations run first in both arms and must recover a planted-arm gap of at least 0.5",
                "zero response-bound truncations and a passing cell-yield guard are required",
                "supportive, null and adverse finite outcomes are filed once without outcome retry",
                "provider-opaque model identity is retained as a limitation; qualification does not prove future provider stability"
            ],
            "planned_sample": {
                "scientific_items": 120,
                "calibration_items": 8,
                "readers": 1,
                "reader_lineages": ["meta/muse-spark"],
                "panel_members": 1,
                "panel_neff": 1,
                "real_cells": 120,
                "calibration_cells": 16,
                "semantic_cells": 12,
                "roles": 10,
                "replicates_hash": TARGET,
                "sdk_version_min": "0.2.51+receipt-preservation-fix"
            }
        }
    }
    # This validates both the receipt shape and the exact roster attachment before publishing.
    reader_qualification.attach({"models": spec["models"]}, spec["reader_qualifications"])
    encoded = json.dumps(spec, indent=2, ensure_ascii=False) + "\n"
    if len(canonical(spec)) > 20_000:
        raise SystemExit("runspec manifest exceeds the register's 20 KB cap")
    (ROOT / "runspec.json").write_text(encoded, encoding="utf-8")
    print(json.dumps({
        "runspec": "runspec.json",
        "runspec_file_sha256": hashlib.sha256(encoded.encode()).hexdigest(),
        "items_url": spec["items_url"],
        "items_sha256": spec["items_sha256"],
        "sdk_commit": sdk_commit,
        "reader_calls": 0,
        "attempt_mints": 0
    }, indent=2))


if __name__ == "__main__":
    main()
