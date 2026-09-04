#!/usr/bin/env python3
"""Build fresh approx(N) robustness items without reader calls."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CLASSES = ["approximate", "exact", "unspecified", "absent"]
ANSWERS = {
    "approximate": "No — the sentence allowed for that difference",
    "exact": "Yes — the sentence committed to the precise figure",
    "unspecified": "The sentence gave the figure without stating whether it was exact",
    "absent": "The sentence did not give that figure",
}
FRAMES = [
    ("ferry crossing", "crossing time", "minutes", "vehicle limit", "vehicles", "crew count", "people", "fuel reserve"),
    ("image export", "archive size", "megabytes", "frame count", "frames", "colour count", "colours", "compression ratio"),
    ("seed trial", "germination rate", "percent", "tray count", "trays", "seed count", "seeds", "water volume"),
    ("radio survey", "signal reach", "kilometres", "mast count", "masts", "channel count", "channels", "noise floor"),
    ("library move", "box weight", "kilograms", "shelf count", "shelves", "book count", "books", "lift capacity"),
    ("battery test", "run time", "hours", "cell count", "cells", "cycle count", "cycles", "charge current"),
    ("harbour audit", "cargo mass", "tonnes", "crane count", "cranes", "container count", "containers", "berth depth"),
    ("orchard census", "tree height", "metres", "row count", "rows", "tree count", "trees", "fruit yield"),
    ("printing job", "ink use", "millilitres", "page count", "pages", "copy count", "copies", "paper weight"),
    ("satellite pass", "contact time", "seconds", "antenna count", "antennas", "packet count", "packets", "error rate"),
    ("museum scan", "scan duration", "minutes", "camera count", "cameras", "object count", "objects", "pixel depth"),
    ("water survey", "flow rate", "litres", "gauge count", "gauges", "sample count", "samples", "temperature"),
]
NUMBERS = [18, 27, 45, 64, 81, 96, 135, 220, 375, 640, 875, 1440]


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def options(answer: str, index: int) -> list[str]:
    rows = [ANSWERS[key] for key in CLASSES]
    offset = (rows.index(answer) + index) % 4
    return rows[offset:] + rows[:offset]


def off(value: int) -> int:
    return value + max(1, round(value / 10))


def build_items() -> list[dict]:
    rows = []
    for cycle in range(4):
        for f, frame in enumerate(FRAMES):
            context, approximate_label, approximate_unit, exact_label, exact_unit, bare_label, bare_unit, absent_label = frame
            approximate_n = NUMBERS[(f + cycle * 2) % len(NUMBERS)]
            exact_n = NUMBERS[(f + cycle * 3 + 4) % len(NUMBERS)]
            bare_n = NUMBERS[(f + cycle * 5 + 7) % len(NUMBERS)]
            key = CLASSES[(f + cycle) % 4]
            english = (
                f"For the {context}, the {approximate_label} was approximately {approximate_n} {approximate_unit}; "
                f"the {exact_label} was exactly {exact_n} {exact_unit}; the {bare_label} was {bare_n} {bare_unit}."
            )
            ainglish = english.replace(
                f"approximately {approximate_n} {approximate_unit}",
                f"approx({approximate_n}) {approximate_unit}",
                1,
            )
            target, value = {
                "approximate": (approximate_label, approximate_n),
                "exact": (exact_label, exact_n),
                "unspecified": (bare_label, bare_n),
                "absent": (absent_label, NUMBERS[(f + cycle + 9) % len(NUMBERS)]),
            }[key]
            answer = ANSWERS[key]
            index = len(rows)
            rows.append({
                "id": f"approx-robust-{cycle + 1:02d}-{f + 1:02d}",
                "english": english,
                "ainglish": ainglish,
                "question": f"Later, the {target} was found to be {off(value)}. Going only by the sentence, was the writer wrong about the {target}?",
                "options": options(answer, index),
                "answer": answer,
                "key_class": key,
            })
    assert len(rows) == 48
    return rows


def calibration() -> list[dict]:
    rows = []
    for index, frame in enumerate(FRAMES[:8]):
        context, label, unit, *_ = frame
        value = NUMBERS[(index * 3 + 1) % len(NUMBERS)]
        answer = ANSWERS["approximate"]
        rows.append({
            "id": f"approx-robust-cal-{index + 1:02d}",
            "calibration": True,
            "english": f"For the {context}, the {label} was exactly {value} {unit}.",
            "ainglish": f"For the {context}, the {label} was approx({value}) {unit}.",
            "question": f"Later, the {label} was found to be {off(value)}. Going only by the sentence, was the writer wrong about the {label}?",
            "options": options(answer, index),
            "answer": answer,
            "key_class": "approximate",
        })
    return rows


def main() -> None:
    items = build_items()
    controls = calibration()
    assert Counter(row["key_class"] for row in items) == Counter({key: 12 for key in CLASSES})
    assert Counter(row["options"].index(row["answer"]) for row in items) == Counter({i: 12 for i in range(4)})
    assert len({(row["english"], row["ainglish"]) for row in items}) == len(items)
    output = {
        "kind": "dexagon.ainglish.approx-robustness-settlement-carrier.v2",
        "proposal_public_id": "a-vkjb699gk6m14rar",
        "proposal_revision": "approx-n-approximation-marker-parenthesized-d-1-robust-5",
        "replicates_hash": "79caba68e4ee77f5caeb9bbabdf349819b60195b91c2e43cbae3352172ca9f28",
        "metric": "robustness_delta",
        "comparator": {"kind": "careful-english-approximately-n-v1"},
        "real_items": 48,
        "items": items,
    }
    (ROOT / "items.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    control_output = {"kind": "dexagon.ainglish.approx-robustness-calibration.v2", "items": controls}
    (ROOT / "calibration.json").write_text(json.dumps(control_output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    index = {
        "kind": "dexagon.ainglish.approx-robustness-settlement-index.v2",
        "model_calls": 0,
        "items_sha256": sha256(canonical(items)).hexdigest(),
        "calibration_sha256": sha256(canonical(controls)).hexdigest(),
        "real_items": len(items), "calibration_items": len(controls),
        "classes": dict(sorted(Counter(row["key_class"] for row in items).items())),
        "answer_positions": dict(sorted(Counter(row["options"].index(row["answer"]) for row in items).items())),
        "corruption": {"channel": "drop_char"},
        "target": output["replicates_hash"],
    }
    index["content_sha256"] = sha256(canonical(index)).hexdigest()
    (ROOT / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(index, indent=2))


if __name__ == "__main__":
    main()

