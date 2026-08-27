#!/usr/bin/env python3
"""Atomically activate all five carriers after the independent-reader gate clears."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile


ROOT = Path(__file__).resolve().parent
KEYS = ("clusivity", "addressee", "uncertainty", "delegation", "collectivity")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def arm_for(seed: int, reader: str, item_id: str) -> str:
    digest = hashlib.sha256(f"{seed}|{reader}|{item_id}".encode()).digest()
    return "ainglish" if digest[0] % 2 else "english"


def validate_panel(panel: object) -> list[dict]:
    assert isinstance(panel, list) and len(panel) >= 2
    required = {"name", "model", "provider", "lineage", "qualification_receipt"}
    assert all(isinstance(row, dict) and required <= set(row) for row in panel)
    assert len({row["name"] for row in panel}) == len(panel)
    assert len({row["lineage"] for row in panel}) >= 2, "at least two independently qualified lineages required"
    for row in panel:
        receipt = row["qualification_receipt"]
        assert isinstance(receipt, dict) and receipt.get("qualified") is True
        assert isinstance(receipt.get("content_sha256"), str) and len(receipt["content_sha256"]) == 64
    return panel


def complete(template: dict, panel: list[dict], seed: int) -> bool:
    ids = {row["id"] for row in template["settlement_strata"]}
    counts = {ident: {"english": 0, "ainglish": 0} for ident in ids}
    for reader in panel:
        for item in template["items"]:
            if not item.get("calibration"):
                counts[item["settlement_stratum"]][arm_for(seed, reader["name"], item["id"])] += 1
    return all(counts[ident][arm] for ident in ids for arm in ("english", "ainglish"))


def activate(template: dict, panel: list[dict]) -> dict:
    unsigned = dict(template)
    expected = unsigned.pop("content_sha256")
    assert hashlib.sha256(canonical(unsigned)).hexdigest() == expected
    artifact = json.loads((ROOT / template["items_artifact"]["file"]).read_text(encoding="utf-8"))
    assert artifact["items"] == template["items"]
    assert hashlib.sha256(canonical(artifact["items"])).hexdigest() == template["items_artifact"]["items_sha256"]
    assert "REPLACE_AFTER_FIRST_COMMIT" not in template["items_artifact"]["published_url"]
    seed = int(template["seed"])
    while not complete(template, panel, seed):
        seed += 1
        if seed - int(template["seed"]) > 100_000:
            raise RuntimeError("no complete two-arm deal found")
    active = {key: value for key, value in template.items() if key not in {
        "kind", "content_sha256", "items", "items_artifact", "activation", "model_calls", "governance_writes"
    }}
    active.update({
        "kind": "ainglish.panel.runspec.v1",
        "seed": seed,
        "panel": panel,
        "items_url": template["items_artifact"]["published_url"],
        "items_sha256": template["items_artifact"]["items_sha256"],
        "activation_receipt": {
            "template_sha256": expected,
            "seed_search_offset": seed - int(template["seed"]),
            "all_settlement_cells_have_both_arms": True,
            "panel_lineages": sorted({row["lineage"] for row in panel}),
            "reader_calls": 0,
            "governance_writes": 0,
        },
    })
    assert len(canonical(active)) <= 20_000, "attempt manifest exceeds register cap"
    return active


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("panel", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    panel = validate_panel(json.loads(args.panel.read_text(encoding="utf-8")))
    active = {key: activate(json.loads((ROOT / f"{key}.template.json").read_text(encoding="utf-8")), panel)
              for key in KEYS}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=args.output_dir) as temp:
        staging = Path(temp)
        outputs = {}
        for key, value in active.items():
            data = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
            name = f"{key}.runspec.json"
            (staging / name).write_text(data, encoding="utf-8")
            outputs[key] = {"file": name, "sha256": hashlib.sha256(data.encode()).hexdigest()}
        index = {
            "kind": "dexagon.ainglish.flagship-activation-index.v2",
            "outputs": outputs,
            "atomic_batch": True,
            "reader_calls": 0,
            "governance_writes": 0,
        }
        index["content_sha256"] = hashlib.sha256(canonical(index)).hexdigest()
        (staging / "activation-index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
        for path in staging.iterdir():
            os.replace(path, args.output_dir / path.name)
    print(json.dumps(index, indent=2))


if __name__ == "__main__":
    main()
