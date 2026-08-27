#!/usr/bin/env python3
"""Activate one template with an exact qualified reader panel, without making reader/API calls."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def arm_for(seed: int, reader: str, item_id: str) -> str:
    digest = hashlib.sha256(f"{seed}|{reader}|{item_id}".encode()).digest()
    return "ainglish" if digest[0] % 2 else "english"


def complete(template: dict, panel: list[dict], seed: int) -> bool:
    scientific = [row for row in template["items"] if not row.get("calibration")]
    counts = {
        row["id"]: {"english": 0, "ainglish": 0}
        for row in template["settlement_strata"]
    }
    for reader in panel:
        for item in scientific:
            counts[item["settlement_stratum"]][arm_for(seed, reader["name"], item["id"])] += 1
    return all(value[arm] > 0 for value in counts.values() for arm in ("english", "ainglish"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("template", type=Path)
    parser.add_argument("panel", type=Path, help="JSON list of two exact independently qualified reader objects")
    parser.add_argument("items_url", help="Published HTTPS URL, or @published for the immutable URL pinned by the template")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    template = json.loads(args.template.read_text(encoding="utf-8"))
    panel = json.loads(args.panel.read_text(encoding="utf-8"))
    assert isinstance(panel, list) and len(panel) >= 2
    assert len({row["name"] for row in panel}) == len(panel)
    assert all(isinstance(row, dict) and row.get("name") for row in panel)
    seed = int(template["seed"])
    while not complete(template, panel, seed):
        seed += 1
        if seed - int(template["seed"]) > 100_000:
            raise RuntimeError("no complete two-arm settlement deal found in 100,000 seeds")
    active = {key: value for key, value in template.items()
              if key not in {"content_sha256", "kind", "activation", "model_calls",
                             "governance_writes", "items", "items_artifact"}}
    active["kind"] = "ainglish.panel.runspec.v1"
    active["seed"] = seed
    active["panel"] = panel
    active["items_url"] = (template["items_artifact"]["published_url"]
                           if args.items_url == "@published" else args.items_url)
    assert active["items_url"].startswith("https://")
    active["items_sha256"] = template["items_artifact"]["items_sha256"]
    active["activation_receipt"] = {
        "template_sha256": template["content_sha256"],
        "items_sha256": active["items_sha256"],
        "items_url": active["items_url"],
        "panel_names": [row["name"] for row in panel],
        "seed_search_offset": seed - int(template["seed"]),
        "all_settlement_cells_have_both_arms": True,
        "reader_calls": 0,
    }
    encoded = json.dumps(active, indent=2, ensure_ascii=False) + "\n"
    args.output.write_text(encoded, encoding="utf-8")
    print(json.dumps(active["activation_receipt"], indent=2))


if __name__ == "__main__":
    main()
