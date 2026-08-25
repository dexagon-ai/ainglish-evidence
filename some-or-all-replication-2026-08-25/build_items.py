#!/usr/bin/env python3
"""Freeze a fresh, form-specific replication carrier for Reticuli's some-or-all original."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SEED = 2026082517
DOMAINS = [
    ("museum", "exhibits", "passed the humidity inspection"),
    ("observatory", "telescopes", "recorded the transit"),
    ("library", "manuscripts", "received a condition report"),
    ("orchard", "plots", "showed frost damage"),
    ("harbour", "berths", "cleared the depth check"),
    ("studio", "recordings", "contain the reference tone"),
    ("bakery", "batches", "met the temperature rule"),
    ("arena", "entrances", "accepted the access badge"),
    ("aquarium", "tanks", "triggered the oxygen alert"),
    ("foundry", "casts", "passed the surface test"),
    ("courier", "parcels", "arrived before the cutoff"),
    ("theatre", "performances", "used the revised lighting cue"),
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def rotate(options: list[str], index: int) -> list[str]:
    shift = index % len(options)
    return options[shift:] + options[:shift]


def main() -> None:
    scientific = []
    for index in range(96):
        domain, noun, predicate = DOMAINS[index % len(DOMAINS)]
        cycle = index // len(DOMAINS) + 51
        marked = f"In {domain} cycle {cycle}, some-or-all {noun} {predicate}."
        careful = (
            f"In {domain} cycle {cycle}, at least one of the contextually identified {noun} {predicate}, "
            f"and it remains possible that every one of those {noun} {predicate}."
        )
        lower = index < 48
        polarity = (index // 12) % 2
        if lower and polarity == 0:
            question = f"Would the message be contradicted if none of the identified {noun} {predicate}?"
            answer = "affirmative"
        elif lower:
            question = f"Is a zero-{noun} case compatible with the message?"
            answer = "negative"
        elif polarity == 0:
            question = f"Must the described condition be false for at least one of the identified {noun}?"
            answer = "negative"
        else:
            question = f"Does the message leave open that every identified {noun} {predicate}?"
            answer = "affirmative"
        scientific.append({
            "id": f"some-or-all-rep-{index + 1:03d}",
            "english": careful,
            "ainglish": marked,
            "question": question,
            "options": rotate(["affirmative", "negative", "indeterminate"], index),
            "answer": answer,
            "marker": "some-or-all",
            "scenario_id": f"fresh-upper-bound-{index + 1:03d}",
            "strata": {"domain": domain, "probe": "lower" if lower else "upper", "polarity": polarity},
        })
    calibration = []
    objects = ["agate disk", "birch key", "cobalt card", "dahlia seal", "ebony tag", "fennel pass",
               "garnet token", "heather badge", "indigo slip", "juniper chip", "kelp marker", "lilac ticket"]
    for index, obj in enumerate(objects):
        calibration.append({
            "id": f"some-or-all-rep-cal-{index + 1:02d}", "calibration": True,
            "english": f"A log mentions the {obj} but gives no shelf.",
            "ainglish": f"A log explicitly places the {obj} on shelf twelve.",
            "question": "Would checking shelf twelve follow the stated location?",
            "options": rotate(["affirmative", "negative", "indeterminate"], index),
            "answer": "affirmative", "set": "construct-free explicit-location positive control",
        })
    rows = scientific + calibration
    assert len(rows) == 108 and len(scientific) == 96
    assert len({row["id"] for row in rows}) == 108
    assert len({(row["english"], row["ainglish"]) for row in scientific}) == 96
    assert sum(row["strata"]["probe"] == "lower" for row in scientific) == 48
    assert sum(row["strata"]["probe"] == "upper" for row in scientific) == 48
    digest = hashlib.sha256(canonical(rows)).hexdigest()
    payload = {
        "kind": "ainglish.some-or-all-fresh-replication-items.v1",
        "seed": SEED,
        "sha256": digest,
        "reader_calls": 0,
        "design": "96 wholly fresh complete pairs: 48 lower-bound and 48 upper-bound consequence probes, plus 12 construct-free calibration rows.",
        "items": rows,
    }
    (ROOT / "items.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    receipt = {
        "kind": "ainglish.some-or-all-fresh-replication-freeze.v1",
        "items": "items.json", "items_sha256": digest,
        "scientific": 96, "lower": 48, "upper": 48, "calibration": 12,
        "reader_calls": 0,
    }
    receipt["content_sha256"] = hashlib.sha256(canonical(receipt)).hexdigest()
    (ROOT / "freeze-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
