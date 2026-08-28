#!/usr/bin/env python3
"""Build immutable fresh-input settlement artifacts, then their manifest templates."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
HEX40 = re.compile(r"[0-9a-f]{40}")
SOURCES = {
    "moved_later": REPO / "moved-direction-comprehension-carrier-2026-08-26/items-moved-later-vs-careful.json",
    "moved_earlier": REPO / "moved-direction-comprehension-carrier-2026-08-26/items-moved-earlier-vs-careful.json",
    "may": REPO / "may-modal-settlement-replication-2026-08-26/items.json",
    "preference": REPO / "flagship-dispute-replication-carriers-2026-08-26/items-preference.json",
    "persistence": REPO / "flagship-dispute-replication-carriers-2026-08-26/items-persistence.json",
}
DIAGNOSTICS = {
    "moved_later": ["domain", "probe_group"],
    "moved_earlier": ["domain", "probe_group"],
    "may": ["form", "voice", "domain", "question_kind", "cross_cell"],
    "preference": ["form", "power_stratum", "outcome", "probe"],
    "persistence": ["form", "stratum", "attachment"],
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"REFUSING: {path} is not an object")
    return value


def source_rows(path: Path) -> tuple[dict, list[dict], str]:
    packet = checked(path)
    rows = packet["items"]
    digest = hashlib.sha256(canonical(rows)).hexdigest()
    declared = packet.get("items_sha256") or packet.get("sha256")
    if digest != declared:
        raise SystemExit(f"REFUSING: source item digest drift at {path}")
    return packet, rows, digest


def build_items(snapshot: dict) -> dict:
    outputs = {}
    for name, path in SOURCES.items():
        source, rows, source_digest = source_rows(path)
        copied = []
        for row in rows:
            item = json.loads(json.dumps(row))
            if not item.get("calibration"):
                item["settlement_stratum"] = "original-published-scalar"
            copied.append(item)
        scientific = sum(not row.get("calibration") for row in copied)
        calibration = len(copied) - scientific
        target = snapshot["targets"][name]
        artifact = {
            "kind": "dexagon.ainglish.manifest-bound-settlement-replication-items.v1",
            "campaign": name,
            "slug": target["slug"],
            "replicates_hash": target["manifest_hash"],
            "source": {
                "path": str(path.relative_to(REPO)),
                "items_sha256": source_digest,
                "fresh_unspent_population": True,
            },
            "scientific_items": scientific,
            "calibration_items": calibration,
            "items": copied,
        }
        artifact["items_sha256"] = hashlib.sha256(canonical(copied)).hexdigest()
        artifact["content_sha256"] = hashlib.sha256(canonical(artifact)).hexdigest()
        output = ROOT / f"{name}.items.json"
        output.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        outputs[name] = {
            "file": output.name,
            "scientific_items": scientific,
            "calibration_items": calibration,
            "items_sha256": artifact["items_sha256"],
            "content_sha256": artifact["content_sha256"],
        }
    return outputs


def build_templates(snapshot: dict, item_commit: str, outputs: dict) -> dict:
    if not HEX40.fullmatch(item_commit):
        raise SystemExit("REFUSING: --item-commit must be one full lowercase Git commit")
    templates = {}
    for ordinal, name in enumerate(SOURCES, 1):
        target = snapshot["targets"][name]
        artifact = checked(ROOT / outputs[name]["file"])
        template = {
            "kind": "dexagon.ainglish.manifest-bound-settlement-replication-template.v1",
            "proposal_revision": target["slug"],
            "slug": target["slug"],
            "construct": target["construct"],
            "metric": "comprehension_accuracy_delta",
            "replicates_hash": target["manifest_hash"],
            "seed": 2026082860 + ordinal,
            "comparator": target["comparator"],
            "settlement_strata": [{"id": "original-published-scalar", "weight": 1}],
            "settlement_design": (
                "one pooled scalar matching the target original's public estimand; form, domain, "
                "probe, power, voice, and cross-cell annotations remain report-only diagnostics "
                "and cannot be promoted into post-hoc settlement gates"
            ),
            "report_only_diagnostics": DIAGNOSTICS[name],
            "items": artifact["items"],
            "scientific_items": artifact["scientific_items"],
            "calibration_items": artifact["calibration_items"],
            "panel": [],
            "panel_neff": 2,
            "reader_independence": {
                "minimum_distinct_lineages": 2,
                "forbidden_lineage_fragments": target["original_panel_family_fragments"],
                "basis": "fresh item population plus two qualified base-model families absent from the original Qwen/Gemma/Ornith panel",
            },
            "source_unspent_freeze": artifact["source"],
            "items_artifact": {
                "file": outputs[name]["file"],
                "items_sha256": artifact["items_sha256"],
                "published_url": (
                    "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
                    f"{item_commit}/manifest-bound-settlement-replications-v1-2026-08-28/"
                    f"{outputs[name]['file']}"
                ),
            },
            "activation": "blocked until one common frozen holdout qualifies two lineages disjoint from Qwen, Gemma, and Ornith",
            "model_calls": 0,
            "governance_writes": 0,
        }
        template["content_sha256"] = hashlib.sha256(canonical(template)).hexdigest()
        path = ROOT / f"{name}.template.json"
        path.write_text(json.dumps(template, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        templates[name] = {
            "file": path.name,
            "content_sha256": template["content_sha256"],
            "replicates_hash": target["manifest_hash"],
        }
    index = {
        "kind": "dexagon.ainglish.manifest-bound-settlement-replication-index.v1",
        "snapshot_sha256": snapshot["content_sha256"],
        "item_commit": item_commit,
        "outputs": outputs,
        "templates": templates,
        "model_calls": 0,
        "governance_writes": 0,
        "blocker": "one common unseen holdout must qualify two non-Qwen/Gemma/Ornith lineages",
    }
    index["content_sha256"] = hashlib.sha256(canonical(index)).hexdigest()
    (ROOT / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return index


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--item-commit", help="full commit that first published the derived item artifacts")
    args = parser.parse_args()
    snapshot = checked(ROOT / "snapshot.json")
    unsigned = dict(snapshot)
    expected = unsigned.pop("content_sha256", None)
    if hashlib.sha256(canonical(unsigned)).hexdigest() != expected:
        raise SystemExit("REFUSING: target snapshot digest drift")
    outputs = build_items(snapshot)
    if not args.item_commit:
        print(json.dumps({"phase": "items", "outputs": outputs}, indent=2))
        return
    index = build_templates(snapshot, args.item_commit, outputs)
    print(json.dumps({
        "phase": "templates",
        "templates": len(index["templates"]),
        "content_sha256": index["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
