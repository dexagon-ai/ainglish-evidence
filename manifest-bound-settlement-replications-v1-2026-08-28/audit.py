#!/usr/bin/env python3
"""Audit source preservation, seals, and optional activated-template bindings."""

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


def sealed(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    unsigned = dict(value)
    expected = unsigned.pop("content_sha256", None)
    if hashlib.sha256(canonical(unsigned)).hexdigest() != expected:
        raise SystemExit(f"REFUSING: content digest drift at {path}")
    return value


def strip_added(row: dict) -> dict:
    clean = dict(row)
    clean.pop("settlement_stratum", None)
    return clean


def audit_items(snapshot: dict) -> dict:
    campaigns = {}
    for name, source_path in build.SOURCES.items():
        source, source_rows, source_digest = build.source_rows(source_path)
        artifact = sealed(ROOT / f"{name}.items.json")
        rows = artifact["items"]
        if artifact["source"] != {
            "path": str(source_path.relative_to(REPO)),
            "items_sha256": source_digest,
            "fresh_unspent_population": True,
        }:
            raise SystemExit(f"REFUSING: source binding drift for {name}")
        if [strip_added(row) for row in rows] != source_rows:
            raise SystemExit(f"REFUSING: answer-bearing source drift for {name}")
        scientific = [row for row in rows if not row.get("calibration")]
        calibration = [row for row in rows if row.get("calibration")]
        if any(row.get("settlement_stratum") != "original-published-scalar" for row in scientific):
            raise SystemExit(f"REFUSING: scientific settlement label drift for {name}")
        if any("settlement_stratum" in row for row in calibration):
            raise SystemExit(f"REFUSING: calibration was assigned to the scientific estimand for {name}")
        if len({row["id"] for row in rows}) != len(rows):
            raise SystemExit(f"REFUSING: duplicate item id for {name}")
        if hashlib.sha256(canonical(rows)).hexdigest() != artifact["items_sha256"]:
            raise SystemExit(f"REFUSING: item digest drift for {name}")
        target = snapshot["targets"][name]
        if artifact["slug"] != target["slug"] or artifact["replicates_hash"] != target["manifest_hash"]:
            raise SystemExit(f"REFUSING: live target binding drift for {name}")
        campaigns[name] = {
            "scientific": len(scientific),
            "calibration": len(calibration),
            "source_answers_preserved_exactly": True,
            "items_sha256": artifact["items_sha256"],
        }
    return campaigns


def audit_templates(snapshot: dict, campaigns: dict) -> tuple[str, dict]:
    index = sealed(ROOT / "index.json")
    item_commit = index["item_commit"]
    subprocess.run(["git", "cat-file", "-e", f"{item_commit}^{{commit}}"], cwd=REPO, check=True)
    templates = {}
    for name in build.SOURCES:
        artifact = sealed(ROOT / f"{name}.items.json")
        template = sealed(ROOT / f"{name}.template.json")
        expected_url = (
            "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
            f"{item_commit}/manifest-bound-settlement-replications-v1-2026-08-28/{name}.items.json"
        )
        if (
            template["items"] != artifact["items"]
            or template["items_artifact"]["items_sha256"] != artifact["items_sha256"]
            or template["items_artifact"]["published_url"] != expected_url
            or template["replicates_hash"] != snapshot["targets"][name]["manifest_hash"]
            or template["settlement_strata"] != [{"id": "original-published-scalar", "weight": 1}]
            or template["reader_independence"]["forbidden_lineage_fragments"]
            != snapshot["targets"][name]["original_panel_family_fragments"]
        ):
            raise SystemExit(f"REFUSING: manifest template binding drift for {name}")
        public = subprocess.run(
            ["git", "show", f"{item_commit}:manifest-bound-settlement-replications-v1-2026-08-28/{name}.items.json"],
            cwd=REPO, check=True, capture_output=True,
        ).stdout
        if public != (ROOT / f"{name}.items.json").read_bytes():
            raise SystemExit(f"REFUSING: item artifact differs from first public commit for {name}")
        templates[name] = {
            "template_sha256": template["content_sha256"],
            "published_item_bytes_verified": True,
            "pooled_original_estimand_only": True,
            "forbidden_original_families": template["reader_independence"]["forbidden_lineage_fragments"],
        }
    if set(index["outputs"]) != set(campaigns) or set(index["templates"]) != set(templates):
        raise SystemExit("REFUSING: index population drift")
    return item_commit, templates


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-templates", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    snapshot = sealed(ROOT / "snapshot.json")
    campaigns = audit_items(snapshot)
    report = {
        "kind": "dexagon.ainglish.manifest-bound-settlement-replication-audit.v1",
        "snapshot_sha256": snapshot["content_sha256"],
        "campaigns": campaigns,
        "templates_verified": False,
        "item_commit": None,
        "templates": {},
        "model_calls": 0,
        "governance_writes": 0,
    }
    if (ROOT / "index.json").exists():
        report["item_commit"], report["templates"] = audit_templates(snapshot, campaigns)
        report["templates_verified"] = True
    elif args.require_templates:
        raise SystemExit("REFUSING: template phase has not been frozen")
    report["content_sha256"] = hashlib.sha256(canonical(report)).hexdigest()
    if args.write:
        (ROOT / "audit.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
