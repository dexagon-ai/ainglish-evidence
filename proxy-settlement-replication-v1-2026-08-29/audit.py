#!/usr/bin/env python3
"""Audit source preservation, disjointness receipts, and optional public bindings."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import build


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def sealed(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    unsigned = dict(value)
    expected = unsigned.pop("content_sha256", None)
    if digest(unsigned) != expected:
        raise SystemExit(f"REFUSING: content digest drift at {path}")
    return value


def strip_added(row: dict) -> dict:
    value = dict(row)
    value.pop("settlement_stratum", None)
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-template", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    snapshot = sealed(ROOT / "snapshot.json")
    artifact = sealed(ROOT / "proxy.items.json")
    source, source_rows = build.source_packet()
    if [strip_added(row) for row in artifact["items"]] != source_rows:
        raise SystemExit("REFUSING: answer-bearing prospective source drift")
    scientific = [row for row in artifact["items"] if not row.get("calibration")]
    calibration = [row for row in artifact["items"] if row.get("calibration")]
    if any(row.get("settlement_stratum") != "original-published-scalar" for row in scientific):
        raise SystemExit("REFUSING: scientific settlement label drift")
    if any("settlement_stratum" in row for row in calibration):
        raise SystemExit("REFUSING: calibration entered the scientific estimand")
    if len({row["id"] for row in artifact["items"]}) != len(artifact["items"]):
        raise SystemExit("REFUSING: duplicate item ids")
    if digest(artifact["items"]) != artifact["items_sha256"]:
        raise SystemExit("REFUSING: item digest drift")
    if artifact["source"] != {
        "path": str(build.SOURCE.relative_to(REPO)),
        "first_public_commit": snapshot["prospective_source"]["first_public_commit"],
        "items_sha256": source["sha256"],
        "public_before_original": True,
        "fresh_unspent_population": True,
    }:
        raise SystemExit("REFUSING: prospective source binding drift")
    if artifact["replicates_hash"] != snapshot["target"]["manifest_hash"]:
        raise SystemExit("REFUSING: replication target drift")
    if any(row["overlap"] != 0 for row in snapshot["input_disjointness"].values()):
        raise SystemExit("REFUSING: original input overlap is not zero")
    if artifact["input_disjointness"] != snapshot["input_disjointness"]:
        raise SystemExit("REFUSING: input-disjointness receipt drift")

    report = {
        "kind": "dexagon.ainglish.proxy-settlement-replication-audit.v1",
        "status": "passed",
        "snapshot_sha256": snapshot["content_sha256"],
        "replicates_hash": artifact["replicates_hash"],
        "scientific_items": len(scientific),
        "calibration_items": len(calibration),
        "source_answers_preserved_exactly": True,
        "source_public_before_original": True,
        "overlap_counts": {
            label: row["overlap"] for label, row in snapshot["input_disjointness"].items()
        },
        "template_verified": False,
        "item_commit": None,
        "published_item_bytes_verified": False,
        "pooled_original_estimand_only": True,
        "original_reader_families_excluded": ["qwen", "gemma", "ornith"],
        "activation_blocked": True,
        "model_calls": 0,
        "attempts_minted": 0,
        "governance_writes": 0,
    }
    if (ROOT / "index.json").exists() and (ROOT / "proxy.template.json").exists():
        index = sealed(ROOT / "index.json")
        template = sealed(ROOT / "proxy.template.json")
        item_commit = index["item_commit"]
        subprocess.run(["git", "cat-file", "-e", f"{item_commit}^{{commit}}"], cwd=REPO, check=True)
        expected_url = (
            "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
            f"{item_commit}/proxy-settlement-replication-v1-2026-08-29/proxy.items.json"
        )
        if (
            template["items"] != artifact["items"]
            or template["replicates_hash"] != snapshot["target"]["manifest_hash"]
            or template["settlement_strata"] != [{"id": "original-published-scalar", "weight": 1}]
            or template["items_artifact"]["items_sha256"] != artifact["items_sha256"]
            or template["items_artifact"]["published_url"] != expected_url
            or template["reader_independence"]["forbidden_lineage_fragments"] != ["qwen", "gemma", "ornith"]
        ):
            raise SystemExit("REFUSING: template binding drift")
        public = subprocess.run(
            ["git", "show", f"{item_commit}:proxy-settlement-replication-v1-2026-08-29/proxy.items.json"],
            cwd=REPO, check=True, capture_output=True,
        ).stdout
        if public != (ROOT / "proxy.items.json").read_bytes():
            raise SystemExit("REFUSING: item artifact differs from its first public commit")
        report.update({
            "template_verified": True,
            "item_commit": item_commit,
            "published_item_bytes_verified": True,
        })
    elif args.require_template:
        raise SystemExit("REFUSING: template phase has not been frozen")
    report["content_sha256"] = digest(report)
    if args.write:
        (ROOT / "audit.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
