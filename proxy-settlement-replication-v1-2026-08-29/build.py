#!/usr/bin/env python3
"""Build the immutable proxy item artifact, then its unactivated manifest template."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
SOURCE = REPO / "proxy-comprehension-carrier-2026-08-25" / "careful-items.json"
HEX40 = re.compile(r"[0-9a-f]{40}")


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


def source_packet() -> tuple[dict, list[dict]]:
    packet = json.loads(SOURCE.read_text(encoding="utf-8"))
    if digest(packet["items"]) != packet["sha256"]:
        raise SystemExit("REFUSING: source packet digest drift")
    return packet, packet["items"]


def build_items(snapshot: dict) -> dict:
    source, rows = source_packet()
    copied = []
    for row in rows:
        item = json.loads(json.dumps(row))
        if not item.get("calibration"):
            item["settlement_stratum"] = "original-published-scalar"
        copied.append(item)
    scientific = sum(not row.get("calibration") for row in copied)
    artifact = {
        "kind": "dexagon.ainglish.proxy-settlement-replication-items.v1",
        "slug": snapshot["proposal"]["slug"],
        "replicates_hash": snapshot["target"]["manifest_hash"],
        "source": {
            "path": str(SOURCE.relative_to(REPO)),
            "first_public_commit": snapshot["prospective_source"]["first_public_commit"],
            "items_sha256": source["sha256"],
            "public_before_original": True,
            "fresh_unspent_population": True,
        },
        "input_disjointness": snapshot["input_disjointness"],
        "scientific_items": scientific,
        "calibration_items": len(copied) - scientific,
        "items": copied,
    }
    artifact["items_sha256"] = digest(copied)
    artifact["content_sha256"] = digest(artifact)
    (ROOT / "proxy.items.json").write_text(
        json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return artifact


def build_template(snapshot: dict, artifact: dict, item_commit: str) -> dict:
    if not HEX40.fullmatch(item_commit):
        raise SystemExit("REFUSING: --item-commit must be one full lowercase Git commit")
    target = snapshot["target"]
    template = {
        "kind": "dexagon.ainglish.proxy-settlement-replication-template.v1",
        "proposal_revision": snapshot["proposal"]["slug"],
        "slug": snapshot["proposal"]["slug"],
        "construct": target["construct"],
        "metric": "comprehension_accuracy_delta",
        "replicates_hash": target["manifest_hash"],
        "seed": 2026082961,
        "comparator": target["comparator"],
        "settlement_strata": [{"id": "original-published-scalar", "weight": 1}],
        "settlement_design": (
            "one pooled scalar matching the target original's public careful-English estimand; "
            "domain, question frame, wave, and per-reader values remain report-only diagnostics"
        ),
        "report_only_diagnostics": ["domain", "question_frame", "wave", "per_reader"],
        "items": artifact["items"],
        "scientific_items": artifact["scientific_items"],
        "calibration_items": artifact["calibration_items"],
        "panel": [],
        "panel_neff": 2,
        "reader_independence": {
            "minimum_distinct_lineages": 2,
            "forbidden_lineage_fragments": target["original_panel_family_fragments"],
            "basis": (
                "the prospective item population is byte-frozen and message-disjoint from the "
                "original; the confirmation panel must also exclude its Qwen, Gemma, and Ornith families"
            ),
        },
        "source_unspent_freeze": artifact["source"],
        "original_input_independence": artifact["input_disjointness"],
        "items_artifact": {
            "file": "proxy.items.json",
            "items_sha256": artifact["items_sha256"],
            "published_url": (
                "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
                f"{item_commit}/proxy-settlement-replication-v1-2026-08-29/proxy.items.json"
            ),
        },
        "activation": (
            "blocked until one common unseen holdout qualifies two lineages outside "
            "Qwen, Gemma, and Ornith; no current model call is authorized"
        ),
        "model_calls": 0,
        "attempts_minted": 0,
        "governance_writes": 0,
    }
    template["content_sha256"] = digest(template)
    (ROOT / "proxy.template.json").write_text(
        json.dumps(template, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    index = {
        "kind": "dexagon.ainglish.proxy-settlement-replication-index.v1",
        "snapshot_sha256": snapshot["content_sha256"],
        "item_commit": item_commit,
        "items": {
            "file": "proxy.items.json",
            "items_sha256": artifact["items_sha256"],
            "content_sha256": artifact["content_sha256"],
        },
        "template": {
            "file": "proxy.template.json",
            "content_sha256": template["content_sha256"],
            "replicates_hash": template["replicates_hash"],
        },
        "blocker": "two independently qualified non-Qwen/Gemma/Ornith reader lineages",
        "model_calls": 0,
        "attempts_minted": 0,
        "governance_writes": 0,
    }
    index["content_sha256"] = digest(index)
    (ROOT / "index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return template


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--item-commit")
    args = parser.parse_args()
    snapshot = sealed(ROOT / "snapshot.json")
    artifact = build_items(snapshot)
    if not args.item_commit:
        print(json.dumps({
            "phase": "items",
            "scientific_items": artifact["scientific_items"],
            "calibration_items": artifact["calibration_items"],
            "items_sha256": artifact["items_sha256"],
        }, indent=2))
        return
    template = build_template(snapshot, artifact, args.item_commit)
    print(json.dumps({
        "phase": "template",
        "replicates_hash": template["replicates_hash"],
        "content_sha256": template["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
