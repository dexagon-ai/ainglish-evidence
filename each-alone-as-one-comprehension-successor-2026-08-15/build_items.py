#!/usr/bin/env python3
"""Build successor items from unchanged Rosetta science plus the new held-out bank."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ORIGINAL = ROOT.parent / "each-alone-as-one-comprehension-original-2026-08-15" / "items.json"
ORIGINAL_ITEMS_SHA256 = "4040959fc87172d52b9a2eb8d38abfc8d5f13d37874318b93d5579e917ab4ae5"
ROSETTA_SOURCE_SHA256 = "4b51b2a0077356a16541e52644c9e3dea934eb0f3a907cdc46a2a88203c96e25"


def canonical_sha(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def main() -> None:
    original = json.loads(ORIGINAL.read_text(encoding="utf-8"))
    if original.get("sha256") != ORIGINAL_ITEMS_SHA256:
        raise SystemExit("REFUSING: original derived-item commitment drifted")
    if original.get("source", {}).get("source_sha256") != ROSETTA_SOURCE_SHA256:
        raise SystemExit("REFUSING: Rosetta source commitment drifted")
    science = [item for item in original["items"] if item.get("set") == "comprehension"]
    if len(science) != 19 or canonical_sha(science) != "68e566a9558bc234e4cc055debc965739a00469426266406558eb8dbfa1bdab8":
        raise SystemExit("REFUSING: the 19 unchanged scientific rows drifted")

    bank = json.loads((ROOT / "calibration-bank.json").read_text(encoding="utf-8"))
    controls = bank.get("items", [])
    if len(controls) != 12 or len({item["id"] for item in controls}) != 12:
        raise SystemExit("REFUSING: held-out bank must contain 12 unique controls")
    answers = {answer: sum(item.get("answer") == answer for item in controls)
               for answer in ("one", "three", "cannot_tell")}
    if answers != {"one": 5, "three": 5, "cannot_tell": 2}:
        raise SystemExit(f"REFUSING: held-out answer balance drifted: {answers}")
    forbidden = ("each-alone", "as-one", "rosetta-amount")
    if any(token in json.dumps(controls, ensure_ascii=False) for token in forbidden):
        raise SystemExit("REFUSING: proposal content leaked into held-out controls")
    if any(item["english"] == item["ainglish"] for item in controls):
        raise SystemExit("REFUSING: calibration arms must not be byte-identical")

    items = science + controls
    document = {
        "kind": "ainglish.panel.items.v1",
        "sha256": canonical_sha(items),
        "source": {
            "scientific_author": "Rosetta",
            "scientific_source_sha256": ROSETTA_SOURCE_SHA256,
            "original_items_sha256": ORIGINAL_ITEMS_SHA256,
            "scientific_rows_retained_without_field_edits": 19,
            "heldout_bank_sha256": canonical_sha(bank),
            "heldout_controls": 12,
            "derivation": "Unchanged 19-row Rosetta science plus the fresh construct-free held-out bank.",
        },
        "items": items,
    }
    (ROOT / "items.json").write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n",
                                     encoding="utf-8")
    print(f"scientific rows: {len(science)}")
    print(f"held-out controls: {len(controls)}")
    print(f"held-out bank canonical sha256: {canonical_sha(bank)}")
    print(f"combined item array canonical sha256: {document['sha256']}")


if __name__ == "__main__":
    main()
