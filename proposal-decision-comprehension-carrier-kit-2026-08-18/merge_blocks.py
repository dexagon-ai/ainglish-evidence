#!/usr/bin/env python3
"""Validate and merge two independent proposal-by / decision-by carrier blocks."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from validate_block import ValidationError, canonical_sha, exact_sha, validate_document


ROOT = Path(__file__).resolve().parent
PROTOCOL_PATH = ROOT / "protocol.json"


def normalized(value: str) -> str:
    return " ".join(value.casefold().split())


def load(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    document = json.loads(path.read_text(encoding="utf-8"))
    return document, validate_document(document)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("block_a", type=Path)
    parser.add_argument("block_b", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        first, first_receipt = load(args.block_a)
        second, second_receipt = load(args.block_b)
        receipts = [first_receipt, second_receipt]
        if {row["seat"] for row in receipts} != {"A", "B"}:
            raise ValidationError("the two blocks must occupy distinct seats A and B")
        if len({row["agent_uuid"] for row in receipts}) != 2:
            raise ValidationError("the two blocks must come from distinct agent UUIDs")
        if len({row["carrier"].casefold() for row in receipts}) != 2:
            raise ValidationError("the two blocks must come from distinct Colony usernames")
        if len({row["operator_id"].casefold() for row in receipts}) != 2:
            raise ValidationError("the two blocks disclose the same operator; strict carrier independence fails")

        documents = sorted([first, second], key=lambda row: row["seat"])
        scenarios = [item for document in documents for item in document["scenarios"]]
        calibrations = [item for document in documents for item in document["calibration_items"]]
        ids = [item["id"] for item in scenarios + calibrations]
        if len(ids) != len(set(ids)):
            raise ValidationError("cross-block item ids collide")

        prose_fingerprints: set[str] = set()
        for item in scenarios:
            for field in ("context", "marked_surface", "careful_surface", "short_surface"):
                fingerprint = hashlib.sha256(normalized(item[field]).encode("utf-8")).hexdigest()
                if fingerprint in prose_fingerprints:
                    raise ValidationError(f"cross-block duplicate normalized prose in {item['id']}/{field}")
                prose_fingerprints.add(fingerprint)

        content = {"scenarios": scenarios, "calibration_items": calibrations}
        output = {
            "kind": "ainglish.proposal-decision.comprehension-scenarios.v1",
            "proposal_revision": first["proposal_revision"],
            "protocol_sha256": exact_sha(PROTOCOL_PATH),
            "carrier_blocks": [
                {
                    "seat": document["seat"],
                    "carrier": document["carrier"],
                    "content_sha256": document["sha256"],
                }
                for document in documents
            ],
            "sha256": canonical_sha(content),
            **content,
        }
        encoded = (json.dumps(output, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        args.output.write_bytes(encoded)
        print(json.dumps({
            "output": str(args.output),
            "scenarios": len(scenarios),
            "calibration_items": len(calibrations),
            "content_sha256": output["sha256"],
            "exact_file_sha256": hashlib.sha256(encoded).hexdigest(),
            "carriers": [row["carrier"] for row in receipts],
        }, indent=2))
    except (OSError, UnicodeError, json.JSONDecodeError, ValidationError) as exc:
        print(f"REFUSING: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
