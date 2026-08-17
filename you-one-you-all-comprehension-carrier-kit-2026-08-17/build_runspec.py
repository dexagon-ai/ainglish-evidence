#!/usr/bin/env python3
"""Build a commit-pinned SDK 0.2.32 runspec after carriers and readers are frozen."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from validate_block import SLUG, ValidationError, canonical_sha, require


COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--items", type=Path, required=True)
    parser.add_argument("--readers", type=Path, required=True)
    parser.add_argument("--freeze-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        require(COMMIT_RE.fullmatch(args.freeze_commit) is not None,
                "freeze commit must be a full lowercase 40-hex Git commit")
        item_doc = json.loads(args.items.read_text(encoding="utf-8"))
        require(item_doc.get("kind") == "ainglish.panel.items.v1", "items kind is wrong")
        items = item_doc.get("items")
        require(isinstance(items, list) and len(items) == 216,
                "merged items must contain 200 science and 16 calibration rows")
        require(sum(not item.get("calibration") for item in items) == 200,
                "merged items must contain exactly 200 science rows")
        require(sum(bool(item.get("calibration")) for item in items) == 16,
                "merged items must contain exactly 16 calibration rows")
        items_sha = canonical_sha(items)
        require(item_doc.get("sha256") == items_sha, "merged item commitment drifted")

        reader_doc = json.loads(args.readers.read_text(encoding="utf-8"))
        require(reader_doc.get("kind") == "ainglish.you-number.reader-roster.v1",
                "reader roster kind is wrong")
        panel = reader_doc.get("panel")
        require(isinstance(panel, list) and len(panel) >= 2,
                "freeze at least two genuinely distinct reader families")
        names = [reader.get("name") for reader in panel]
        require(all(isinstance(name, str) and name.strip() for name in names),
                "every reader needs a non-empty name")
        require(len({name.casefold() for name in names}) == len(names), "reader names repeat")
        families = [reader.get("family") for reader in panel]
        require(all(isinstance(family, str) and family.strip() for family in families),
                "every reader must name its model family")
        require(len({family.casefold() for family in families}) >= 2,
                "use at least two distinct reader families")
        required_reader = {"name", "family", "provider", "model", "precision", "max_tokens"}
        for index, reader in enumerate(panel):
            require(required_reader <= set(reader), f"reader {index} misses required identity/transport fields")
            require(isinstance(reader["max_tokens"], int) and reader["max_tokens"] > 0,
                    f"reader {index}.max_tokens must be a positive integer")
        panel_neff = reader_doc.get("panel_neff")
        require(isinstance(panel_neff, int) and 2 <= panel_neff <= len(panel),
                "panel_neff must be an integer from 2 through the roster size")

        carrier_ops = {
            block["carrier"]["operator_id"]
            for block in item_doc.get("source", {}).get("blocks", [])
            if block.get("carrier", {}).get("operator_id") != "undisclosed"
        }
        executor_op = reader_doc.get("operator_id")
        require(isinstance(executor_op, str) and executor_op.strip()
                and "REPLACE" not in executor_op, "reader roster must declare executor operator_id")
        require(executor_op not in carrier_ops,
                "reader executor shares a disclosed operator with an item carrier")

        seed_material = f"{items_sha}|{'|'.join(sorted(names))}".encode("utf-8")
        seed = int(hashlib.sha256(seed_material).hexdigest()[:8], 16)
        items_url = (
            "https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/"
            f"{args.freeze_commit}/you-one-you-all-comprehension-carrier-kit-2026-08-17/items.json"
        )
        spec = {
            "construct": "you-one / you-all",
            "slug": SLUG,
            "metric": "comprehension_accuracy_delta",
            "seed": seed,
            "planted_arm": "ainglish",
            "calibration_min_gap": 0.5,
            "panel_neff": panel_neff,
            "panel": [{key: value for key, value in reader.items() if key != "family"} for reader in panel],
            "items_url": items_url,
            "items_sha256": items_sha,
            "attempt": {
                "proposal_revision": SLUG,
                "estimand": (
                    "Original comprehension_accuracy_delta in percentage points for exact joint "
                    "recovery of the utterance-time addressee set and its cardinality from "
                    "you-one / you-all versus their full careful-English mappings. One hundred "
                    "paired scenarios per form come from two independent carrier blocks. Forms "
                    "and carrier blocks remain separate; the registered -5pp non-inferiority "
                    "margin is interpreted per form, never rescued by the pooled headline."
                ),
                "admissibility_gates": [
                    "two carrier blocks validate independently and have distinct agent UUIDs",
                    "neither answer-bearing carrier is controlled by the proposal author",
                    "all 200 real scenarios were frozen before any reader call",
                    "all 16 construct-free calibration rows run first in both arms for every reader",
                    "the planted calibration accuracy gap is at least 0.5",
                    "you-one and you-all, each carrier, channel, position and frame remain separately reportable",
                    "a valid result is filed regardless of sign; each form is interpreted against -5pp separately",
                    "the pooled headline cannot rescue a form whose own estimate fails or is unresolved",
                    "reader families, versions, precisions and answer bounds are frozen before attempt minting",
                    "reader execution is dedicated RTX 3090 GPU-only; CPU fallback is prohibited",
                    "any digest, resource, calibration, transport or yield failure becomes a typed abort",
                ],
                "planned_sample": {
                    "real_items": 200,
                    "real_items_per_form": 100,
                    "calibration_items": 16,
                    "carrier_blocks": 2,
                    "reader_members": len(panel),
                    "reader_families": sorted(set(families)),
                    "real_cells": 200 * len(panel),
                    "calibration_cells": 16 * 2 * len(panel),
                    "execution": "dedicated RTX 3090; one loaded model/request at a time; no CPU fallback",
                },
            },
        }
        encoded = (json.dumps(spec, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        args.output.write_bytes(encoded)
        print(json.dumps({
            "output": str(args.output),
            "seed": seed,
            "items_sha256": items_sha,
            "runspec_exact_file_sha256": hashlib.sha256(encoded).hexdigest(),
            "reader_families": sorted(set(families)),
        }, indent=2))
    except (OSError, UnicodeError, json.JSONDecodeError, ValidationError) as exc:
        print(f"REFUSING: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
