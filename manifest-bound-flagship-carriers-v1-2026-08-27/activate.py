#!/usr/bin/env python3
"""Activate one template with an exact qualified reader panel, without making reader/API calls."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


HEX = set("0123456789abcdef")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


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


def normal_digest(value: object) -> str:
    assert isinstance(value, str)
    digest = value.removeprefix("sha256:").lower()
    assert len(digest) == 64 and set(digest) <= HEX
    return digest


def validate_panel(panel: object, constraints: dict | None = None) -> list[dict]:
    assert isinstance(panel, list) and len(panel) >= 2
    required = {"name", "model", "model_digest", "provider", "lineage", "qualification_receipt"}
    assert all(isinstance(row, dict) and required <= set(row) for row in panel)
    assert len({row["name"] for row in panel}) == len(panel)
    assert len({row["lineage"] for row in panel}) >= 2, "at least two independently qualified lineages required"
    holdouts = set()
    for row in panel:
        receipt = row["qualification_receipt"]
        assert isinstance(receipt, dict) and receipt.get("qualified") is True
        assert receipt.get("lineage") == row["lineage"]
        assert receipt.get("model") == row["model"]
        assert normal_digest(receipt.get("model_digest")) == normal_digest(row["model_digest"])
        holdout = normal_digest(receipt.get("holdout_sha256"))
        holdouts.add(holdout)
        sealed = dict(receipt)
        expected = normal_digest(sealed.pop("content_sha256", None))
        assert hashlib.sha256(canonical(sealed)).hexdigest() == expected
    assert len(holdouts) == 1, "all readers must qualify on the same frozen holdout"
    constraints = constraints or {}
    forbidden = tuple(str(value).casefold() for value in constraints.get("forbidden_lineage_fragments", []))
    if forbidden:
        offenders = [
            row["lineage"] for row in panel
            if any(fragment in row["lineage"].casefold() for fragment in forbidden)
        ]
        assert not offenders, f"replication panel overlaps forbidden original lineage families: {offenders}"
    return panel


def attempt_block(template: dict, panel: list[dict], seed: int) -> dict:
    scientific = [row for row in template["items"] if not row.get("calibration")]
    calibration = [row for row in template["items"] if row.get("calibration")]
    strata = [row["id"] for row in template["settlement_strata"]]
    target = template.get("replicates_hash")
    role = "Fresh-input replication" if target else "Original"
    receipt_hashes = [row["qualification_receipt"]["content_sha256"] for row in panel]
    holdout = panel[0]["qualification_receipt"]["holdout_sha256"]
    gates = [
        f"the proposal is freshly read immediately before mint and still accepts {'replication of ' + target if target else 'an original comprehension row'} at revision {template['proposal_revision']}",
        f"the unactivated template verifies at content_sha256 {template['content_sha256']}",
        f"the public item artifact resolves to items_sha256 {template['items_artifact']['items_sha256']}",
        f"all {len(strata)} settlement strata have planned exposure in both arms at deterministic assignment seed {seed}",
        f"every panel member carries a byte-verified qualified=true receipt on common holdout {holdout} and at least two distinct base-model lineages are present",
        "every configured reader model and live model digest matches its qualification receipt before mint",
        "construct-free calibration runs first in both arms for every reader and must show a planted-arm gap of at least 0.5",
        "zero reader transport faults and zero response-bound truncations are required for the clean committed manifest",
        "supportive, null, adverse, ceiling-bound, and floor-bound finite outcomes are filed once without outcome retry",
        "these answer-bearing inputs and this attempt are never reused as a fresh independent confirmation",
    ]
    independence = template.get("reader_independence") or {}
    forbidden = independence.get("forbidden_lineage_fragments") or []
    if forbidden:
        gates.insert(
            6,
            "the replication panel contains no lineage whose declared family includes any of: "
            + ", ".join(forbidden),
        )
    diagnostics = template.get("report_only_diagnostics") or []
    if diagnostics:
        gates.append(
            "report the frozen diagnostic axes without promoting any observed subgroup into a "
            "post-hoc settlement gate: " + ", ".join(diagnostics)
        )
    return {
        "proposal_revision": template["proposal_revision"],
        "estimand": (
            f"{role} comprehension_accuracy_delta for {template['construct']} versus "
            f"{template['comparator']['description']} Every declared settlement stratum is "
            f"load-bearing under the frozen equal-weight contract: {template['settlement_design']}. "
            "Report absolute arms, interval, resolution, per-reader values, every stratum, "
            "calibration, yield, transport, and resample-down receipts; no favourable stratum "
            "may rescue a failed one."
        ),
        "admissibility_gates": gates,
        "planned_sample": {
            "scientific_items": len(scientific),
            "calibration_items": len(calibration),
            "settlement_strata": len(strata),
            "readers": len(panel),
            "reader_lineages": sorted({row["lineage"] for row in panel}),
            "panel_neff": len({row["lineage"] for row in panel}),
            "qualification_holdout_sha256": holdout,
            "qualification_receipt_sha256s": receipt_hashes,
            "replicates_hash": target,
            "report_only_diagnostics": diagnostics,
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
    panel = validate_panel(
        json.loads(args.panel.read_text(encoding="utf-8")),
        template.get("reader_independence"),
    )
    unsigned = dict(template)
    expected = unsigned.pop("content_sha256")
    assert hashlib.sha256(canonical(unsigned)).hexdigest() == expected
    artifact = json.loads((args.template.parent / template["items_artifact"]["file"]).read_text(encoding="utf-8"))
    assert artifact["items"] == template["items"]
    assert hashlib.sha256(canonical(artifact["items"])).hexdigest() == template["items_artifact"]["items_sha256"]
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
    assert len(canonical(active)) <= 20_000, "attempt manifest exceeds register cap"
    encoded = json.dumps(active, indent=2, ensure_ascii=False) + "\n"
    args.output.write_text(encoded, encoding="utf-8")
    print(json.dumps(active["activation_receipt"], indent=2))


if __name__ == "__main__":
    main()
