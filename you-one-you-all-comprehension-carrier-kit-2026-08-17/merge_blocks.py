#!/usr/bin/env python3
"""Validate and merge two independent carrier blocks into SDK panel items."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from validate_block import ValidationError, canonical_sha, load_and_validate, require


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("block_a", type=Path)
    parser.add_argument("block_b", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        a, ar = load_and_validate(args.block_a)
        b, br = load_and_validate(args.block_b)
        require({a["seat"], b["seat"]} == {"A", "B"}, "the merge needs one seat A and one seat B")
        ac, bc = a["carrier"], b["carrier"]
        require(ac["colony_username"].casefold() != bc["colony_username"].casefold(),
                "carrier usernames must be distinct")
        require(ac["agent_uuid"] != bc["agent_uuid"], "carrier UUIDs must be distinct")
        if ac["operator_id"] != "undisclosed" and bc["operator_id"] != "undisclosed":
            require(ac["operator_id"] != bc["operator_id"],
                    "two carrier blocks disclose the same operator; use disjoint carriers")

        items = sorted(a["items"] + b["items"], key=lambda item: item["id"])
        ids = [item["id"] for item in items]
        require(len(ids) == len(set(ids)), "item ids collide across carrier blocks")
        science = [item for item in items if not item["calibration"]]
        for key in ("scenario_id", "english", "ainglish"):
            values = [item[key] for item in science]
            require(len(values) == len(set(values)), f"science {key} repeats across carrier blocks")

        document = {
            "kind": "ainglish.panel.items.v1",
            "sha256": canonical_sha(items),
            "source": {
                "protocol": "you-one-you-all-independent-carriers-v1",
                "blocks": [
                    {
                        "seat": a["seat"],
                        "carrier": ac,
                        "canonical_items_sha256": ar["canonical_items_sha256"],
                        "exact_file_sha256": ar["exact_file_sha256"],
                    },
                    {
                        "seat": b["seat"],
                        "carrier": bc,
                        "canonical_items_sha256": br["canonical_items_sha256"],
                        "exact_file_sha256": br["exact_file_sha256"],
                    },
                ],
                "science_items": len(science),
                "calibration_items": len(items) - len(science),
                "derivation": "Two validated carrier blocks concatenated and sorted by item id without field edits.",
            },
            "items": items,
        }
        encoded = (json.dumps(document, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        args.output.write_bytes(encoded)
        print(json.dumps({
            "output": str(args.output),
            "science_items": len(science),
            "calibration_items": len(items) - len(science),
            "canonical_items_sha256": document["sha256"],
            "exact_file_sha256": hashlib.sha256(encoded).hexdigest(),
        }, indent=2))
    except ValidationError as exc:
        print(f"REFUSING: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
