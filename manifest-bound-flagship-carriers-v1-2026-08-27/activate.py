#!/usr/bin/env python3
"""Activate one template with an exact qualified reader panel, without making reader/API calls."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


HEX = set("0123456789abcdef")


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


def validate_panel(panel: object) -> list[dict]:
    assert isinstance(panel, list) and len(panel) >= 2
    required = {"name", "model", "provider", "lineage", "qualification_receipt"}
    assert all(isinstance(row, dict) and required <= set(row) for row in panel)
    assert len({row["name"] for row in panel}) == len(panel)
    assert len({row["lineage"] for row in panel}) >= 2, "at least two independently qualified lineages required"
    for row in panel:
        receipt = row["qualification_receipt"]
        assert isinstance(receipt, dict) and receipt.get("qualified") is True
        digest = receipt.get("content_sha256")
        assert isinstance(digest, str) and len(digest) == 64 and set(digest) <= HEX
    return panel


def attempt_block(template: dict, panel: list[dict], seed: int) -> dict:
    scientific = [row for row in template["items"] if not row.get("calibration")]
    calibration = [row for row in template["items"] if row.get("calibration")]
    strata = [row["id"] for row in template["settlement_strata"]]
    return {
        "proposal_revision": template["proposal_revision"],
        "estimand": (
            f"Original comprehension_accuracy_delta for {template['construct']} versus "
            f"{template['comparator']['description']} Every declared settlement stratum is "
            f"load-bearing under the frozen equal-weight contract: {template['settlement_design']}. "
            "Report absolute arms, interval, resolution, per-reader values, every stratum, "
            "calibration, yield, transport, and resample-down receipts; no favourable stratum "
            "may rescue a failed one."
        ),
        "admissibility_gates": [
            f"the proposal is freshly read immediately before mint and still accepts an original comprehension row at revision {template['proposal_revision']}",
            f"the unactivated template verifies at content_sha256 {template['content_sha256']}",
            f"the public item artifact resolves to items_sha256 {template['items_artifact']['items_sha256']}",
            f"all {len(strata)} settlement strata have planned exposure in both arms at deterministic assignment seed {seed}",
            "every panel member carries a digest-bound qualified=true ordinary-English holdout receipt and at least two distinct base-model lineages are present",
            "every configured reader model and transport matches its qualification receipt before mint",
            "construct-free calibration runs first in both arms for every reader and must show a planted-arm gap of at least 0.5",
            "zero reader transport faults and zero response-bound truncations are required for the clean committed manifest",
            "supportive, null, adverse, ceiling-bound, and floor-bound finite outcomes are filed once without outcome retry",
            "a different principal with wholly fresh answer-bearing inputs is required for any later confirmation",
        ],
        "planned_sample": {
            "scientific_items": len(scientific),
            "calibration_items": len(calibration),
            "settlement_strata": len(strata),
            "readers": len(panel),
            "reader_lineages": sorted({row["lineage"] for row in panel}),
            "panel_neff": len({row["lineage"] for row in panel}),
            "real_reader_cells": len(scientific) * len(panel),
            "calibration_reader_cells": len(calibration) * len(panel) * 2,
            "assignment_seed": seed,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("template", type=Path)
    parser.add_argument("panel", type=Path, help="JSON list of two exact independently qualified reader objects")
    parser.add_argument("items_url", help="Published HTTPS URL, or @published for the immutable URL pinned by the template")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    template = json.loads(args.template.read_text(encoding="utf-8"))
    panel = validate_panel(json.loads(args.panel.read_text(encoding="utf-8")))
    unsigned = dict(template)
    expected = unsigned.pop("content_sha256")
    assert hashlib.sha256(json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest() == expected
    artifact = json.loads((args.template.parent / template["items_artifact"]["file"]).read_text(encoding="utf-8"))
    assert artifact["items"] == template["items"]
    assert hashlib.sha256(json.dumps(artifact["items"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest() == template["items_artifact"]["items_sha256"]
    assert "REPLACE_AFTER_FIRST_COMMIT" not in template["items_artifact"]["published_url"]
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
    active["attempt"] = attempt_block(template, panel, seed)
    active["activation_receipt"] = {
        "template_sha256": template["content_sha256"],
        "items_sha256": active["items_sha256"],
        "items_url": active["items_url"],
        "panel_names": [row["name"] for row in panel],
        "seed_search_offset": seed - int(template["seed"]),
        "all_settlement_cells_have_both_arms": True,
        "reader_calls": 0,
        "attempt_mints": 0,
    }
    encoded = json.dumps(active, indent=2, ensure_ascii=False) + "\n"
    args.output.write_text(encoded, encoding="utf-8")
    print(json.dumps(active["activation_receipt"], indent=2))


if __name__ == "__main__":
    main()
