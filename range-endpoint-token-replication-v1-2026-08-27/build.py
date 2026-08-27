#!/usr/bin/env python3
"""Freeze 32 fresh endpoint-membership pairs without tokenizing them."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "items.json"

CONTEXTS = (
    ("batch numbers", "12", "48"),
    ("release dates", "Tuesday", "Saturday"),
    ("supported versions", "3.2", "5.0"),
    ("temperature readings", "-8", "14"),
    ("network ports", "4100", "4199"),
    ("priority ranks", "20", "4"),
    ("log offsets", "900", "1200"),
    ("checkpoint times", "18:30", "06:15"),
)

FORMS = (
    (
        "include-both",
        lambda subject, start, end: f"{subject} {start} to {end}, include-both",
        lambda subject, start, end: f"{subject} from {start} to {end}, including both {start} and {end}",
    ),
    (
        "include-start-only",
        lambda subject, start, end: f"{subject} {start} to {end}, include-start-only",
        lambda subject, start, end: f"{subject} from {start}, including {start}, to {end}, excluding {end}",
    ),
    (
        "include-end-only",
        lambda subject, start, end: f"{subject} {start} to {end}, include-end-only",
        lambda subject, start, end: f"{subject} from {start}, excluding {start}, to {end}, including {end}",
    ),
    (
        "exclude-both",
        lambda subject, start, end: f"{subject} {start} to {end}, exclude-both",
        lambda subject, start, end: f"{subject} from {start} to {end}, excluding both {start} and {end}",
    ),
)


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    if TARGET.exists():
        raise SystemExit("REFUSING: items.json already exists")
    pairs = []
    for form, marked, careful in FORMS:
        for number, (subject, start, end) in enumerate(CONTEXTS, 1):
            pairs.append({
                "item_id": f"{form}-{number:02d}",
                "form": form,
                "ainglish": marked(subject, start, end),
                "english": careful(subject, start, end),
            })
    packet = {
        "kind": "dexagon.ainglish.range-endpoint-token-replication-items.v1",
        "proposal_revision": "include-both-include-start-only-include-end-only-exclude-bot",
        "replicates_hash": "893510f22c697fc45ab7c073147e90bfcc1a31cf888cb49cb511ed2ceee8e414",
        "metric": "token_delta",
        "models": ["cl100k_base", "o200k_base"],
        "pairs": pairs,
        "construction": "32 fresh complete mappings, eight per form; four numeric/date contexts are descending so start/end remain positions as written rather than lower/upper values",
        "evidentiary_limit": "Price evidence only; no comprehension, correctness, adoption, or flagship-quality claim.",
    }
    if len(pairs) != 32 or len({row["item_id"] for row in pairs}) != 32:
        raise SystemExit("population identity failure")
    if {form: sum(row["form"] == form for row in pairs) for form, *_ in FORMS} != {form: 8 for form, *_ in FORMS}:
        raise SystemExit("form balance failure")
    if len({(row["ainglish"], row["english"]) for row in pairs}) != 32:
        raise SystemExit("duplicate pair")
    packet["content_sha256"] = hashlib.sha256(canonical(packet)).hexdigest()
    TARGET.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"pairs": len(pairs), "sha256": packet["content_sha256"]}))


if __name__ == "__main__":
    main()
