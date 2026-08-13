#!/usr/bin/env python3
"""Derive Dexagon's whole/part v2 run artifact without editing any item bytes.

Rosetta's original 126-item freeze remains immutable.  Its calibration-labelled rows contain four
genuine planted arm contrasts and two useful bare-overread controls whose English and Ainglish arms
are byte-identical.  ainglish-panel 0.2.24 assigns one arm per calibration item and gates on the
between-arm accuracy difference, so identical-arm controls can make the declared positive-control
gap unattainable solely because of the hash allocation.

This derivative keeps every one of the 120 real rows and the four genuine contrasts verbatim.  It
excludes cal-03 and cal-06 from the harness run rather than relabelling them or allowing them to
dilute the construct estimand.  They remain visible in the source freeze as separately identified
diagnostics.  No model call occurs here.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "whole_part_items_8c43d4fd.json"
OUTPUT = HERE / "whole_part_true_contrasts_v2_items.json"
SOURCE_FILE_SHA256 = "8c43d4fd12a4200d3f362dcae4bca3508dabcf9041f6fcc1d656db5f6b1db5d7"
EXCLUDED_DIAGNOSTICS = {"rosetta-wp-cal-03", "rosetta-wp-cal-06"}
TRUE_CONTRASTS = {
    "rosetta-wp-cal-01",
    "rosetta-wp-cal-02",
    "rosetta-wp-cal-04",
    "rosetta-wp-cal-05",
}
SEED = 1883303993
READER_NAME = "Dexagon-local-Gemma3-12B-Q4_K_M"


def arm_for(seed: int, panelist: str, item_id: str) -> str:
    """Byte-identical copy of ainglish-panel 0.2.24's assignment rule."""
    digest = hashlib.sha256(f"{seed}|{panelist}|{item_id}".encode()).digest()
    return "ainglish" if digest[0] % 2 else "english"


def main() -> None:
    source_bytes = SOURCE.read_bytes()
    assert hashlib.sha256(source_bytes).hexdigest() == SOURCE_FILE_SHA256
    source = json.loads(source_bytes)
    assert isinstance(source, list) and len(source) == 126
    assert source == sorted(source, key=lambda item: item["id"])

    by_id = {item["id"]: item for item in source}
    assert len(by_id) == len(source)
    calibration_ids = {item["id"] for item in source if item.get("calibration")}
    assert calibration_ids == TRUE_CONTRASTS | EXCLUDED_DIAGNOSTICS
    assert all(by_id[item_id]["english"] == by_id[item_id]["ainglish"]
               for item_id in EXCLUDED_DIAGNOSTICS)
    assert all(by_id[item_id]["english"] != by_id[item_id]["ainglish"]
               for item_id in TRUE_CONTRASTS)

    derived = [item for item in source if item["id"] not in EXCLUDED_DIAGNOSTICS]
    real = [item for item in derived if not item.get("calibration")]
    calibration = [item for item in derived if item.get("calibration")]
    assert len(derived) == 124 and len(real) == 120 and len(calibration) == 4
    assert {item["id"] for item in calibration} == TRUE_CONTRASTS
    assert all(item is by_id[item["id"]] for item in derived)

    allocation = {"ainglish": [], "english": []}
    for item in calibration:
        allocation[arm_for(SEED, READER_NAME, item["id"])].append(item["id"])
    assert allocation == {
        "ainglish": ["rosetta-wp-cal-02", "rosetta-wp-cal-04", "rosetta-wp-cal-05"],
        "english": ["rosetta-wp-cal-01"],
    }

    encoded = json.dumps(derived, indent=1, ensure_ascii=False).encode("utf-8")
    canonical = json.dumps(
        derived, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    OUTPUT.write_bytes(encoded)
    print(json.dumps({
        "source": str(SOURCE),
        "output": str(OUTPUT),
        "source_exact_file_sha256": SOURCE_FILE_SHA256,
        "exact_file_sha256": hashlib.sha256(encoded).hexdigest(),
        "sdk_items_sha256": hashlib.sha256(canonical).hexdigest(),
        "items": len(derived),
        "real": len(real),
        "calibration": len(calibration),
        "excluded_diagnostics": sorted(EXCLUDED_DIAGNOSTICS),
        "seed": SEED,
        "reader_name": READER_NAME,
        "calibration_allocation": allocation,
    }, indent=2))


if __name__ == "__main__":
    main()
