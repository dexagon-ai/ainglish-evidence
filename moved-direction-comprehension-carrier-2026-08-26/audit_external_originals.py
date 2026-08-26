#!/usr/bin/env python3
"""Verify the frozen carrier is pair-disjoint from every live moved-direction original."""

from __future__ import annotations

import json
from pathlib import Path
import urllib.request

from ainglish.client import AinglishClient


ROOT = Path(__file__).resolve().parent
TARGETS = {
    "3965fddd5d31ea9f9948a113dd549cd84bac61223b61941ec69bde0b0d326635": "moved-later-vs-careful",
    "c35249de0f0807215f4ec82e3a964f9f5ac419522b5986de10c0350ed9ae8bbb": "moved-later-vs-bare",
    "b755d553d4c1f890a54833731a841aef8fa40348d2f641b6ec42b3d1f571813c": "moved-earlier-vs-careful",
    "a7270b497fbb5a8012223fa2be74c18ffd68c2dcb5ce3e5c13d6e1d3ff86bbfb": "moved-earlier-vs-bare",
}


def rows(value: object) -> list[dict]:
    if isinstance(value, dict):
        value = value.get("items")
    if not isinstance(value, list) or not all(isinstance(row, dict) for row in value):
        raise SystemExit("REFUSING: an original item URL did not return a list of item objects")
    return value


def pair(row: dict) -> tuple[str, str]:
    values = row.get("english"), row.get("ainglish")
    if not all(isinstance(value, str) for value in values):
        raise SystemExit("REFUSING: a row lost its complete English/Ainglish pair")
    return values


def triple(row: dict) -> tuple[str, str, str]:
    values = pair(row) + (row.get("question"),)
    if not isinstance(values[2], str):
        raise SystemExit("REFUSING: a row lost its answer-bearing question")
    return values


def main() -> None:
    client = AinglishClient()
    reports = []
    for target_hash, campaign in TARGETS.items():
        measurement = client.measurement(target_hash)
        manifest = measurement.get("manifest") or {}
        item_url = manifest.get("items_url")
        if not isinstance(item_url, str):
            raise SystemExit(f"REFUSING: {target_hash[:12]} has no immutable item URL")
        with urllib.request.urlopen(item_url, timeout=30) as response:
            original = rows(json.load(response))
        packet = json.loads((ROOT / f"items-{campaign}.json").read_text(encoding="utf-8"))
        fresh = rows(packet)
        pair_overlap = set(map(pair, original)) & set(map(pair, fresh))
        triple_overlap = set(map(triple, original)) & set(map(triple, fresh))
        reports.append({
            "target_hash": target_hash,
            "campaign": campaign,
            "original_items_sha256": manifest.get("items_sha256"),
            "fresh_items_sha256": packet.get("items_sha256"),
            "original_rows": len(original),
            "fresh_rows": len(fresh),
            "complete_pair_overlap": len(pair_overlap),
            "answer_bearing_triple_overlap": len(triple_overlap),
        })
    if any(row["complete_pair_overlap"] or row["answer_bearing_triple_overlap"] for row in reports):
        raise SystemExit("REFUSING: the proposed replication corpus overlaps an original")
    print(json.dumps({"status": "passed", "targets": reports}, indent=2))


if __name__ == "__main__":
    main()
