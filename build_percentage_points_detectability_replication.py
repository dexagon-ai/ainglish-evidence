#!/usr/bin/env python3
"""Build a fresh endpoints-present detectability replication without reader calls.

The scored task preserves Reticuli's original estimand: the writer intends an additive
percentage-point change; English uses bare percent, Ainglish names percentage points, and both
arms carry identical endpoints. Clean rows are arithmetically additive, collision rows carry the
equally plausible relative-percent endpoint, and break-both rows match neither reading.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path


OUT = Path(__file__).with_name("percentage_points_detectability_replication_items.json")
OPTIONS = ["consistent", "contradictory", "cannot be determined"]
QUESTION = "Considering only the numeric claims in this report, are they mutually consistent?"

# condition, label, metric, direction, base, additive delta, stated endpoint
ROWS = [
    ("clean", "drone", "drone inspection coverage", "rose", 34, 7, 41),
    ("clean", "archive", "archive checksum pass rate", "fell", 88, 6, 82),
    ("clean", "glossary", "translation glossary match rate", "rose", 43, 9, 52),
    ("clean", "cold-chain", "cold-chain alarm failure rate", "fell", 17, 4, 13),
    ("clean", "irrigation", "irrigation sensor availability", "rose", 62, 11, 73),
    ("clean", "grants", "grant application rejection rate", "fell", 29, 5, 24),
    ("clean", "seismic", "seismic classifier recall", "rose", 55, 8, 63),
    ("clean", "customs", "customs document error rate", "fell", 14, 3, 11),
    ("clean", "downlink", "satellite downlink completion rate", "rose", 48, 12, 60),
    ("clean", "inventory", "library inventory mismatch rate", "fell", 21, 7, 14),
    ("clean", "fisheries", "fisheries sample traceability rate", "rose", 71, 6, 77),
    ("clean", "legal-intake", "legal intake abandonment rate", "fell", 33, 9, 24),
    ("clean", "museum", "museum image tagging accuracy", "rose", 79, 5, 84),
    ("clean", "transit", "transit missed-connection rate", "fell", 26, 8, 18),
    ("clean", "weather", "weather station reporting rate", "rose", 37, 10, 47),
    ("clean", "escrow", "escrow reconciliation exception rate", "fell", 12, 4, 8),
    ("collision", "triage", "case triage completion rate", "rose", 40, 25, 50),
    ("collision", "water", "water-quality sample rejection rate", "fell", 80, 15, 68),
    ("collision", "catalogue", "catalogue record enrichment rate", "rose", 60, 10, 66),
    ("collision", "permits", "permit review escalation rate", "fell", 50, 20, 40),
    ("collision", "habitat", "habitat survey completion rate", "rose", 32, 25, 40),
    ("collision", "settlement", "trade settlement exception rate", "fell", 72, 25, 54),
    ("collision", "caption", "lecture caption approval rate", "rose", 45, 20, 54),
    ("collision", "dispatch", "emergency dispatch transfer rate", "fell", 90, 10, 81),
    ("break_both", "orchard", "orchard disease detection rate", "rose", 25, 20, 37),
    ("break_both", "appeal", "benefit appeal reversal rate", "fell", 70, 10, 55),
    ("break_both", "coral", "coral image classification accuracy", "rose", 52, 15, 73),
    ("break_both", "freight", "freight manifest correction rate", "fell", 44, 5, 35),
    ("break_both", "manuscript", "manuscript metadata recovery rate", "rose", 18, 30, 40),
    ("break_both", "vaccination", "vaccination reminder failure rate", "fell", 96, 12, 76),
    ("break_both", "turbine", "wind-turbine inspection completion rate", "rose", 67, 8, 82),
    ("break_both", "licence", "professional licence renewal lapse rate", "fell", 38, 15, 19),
]

FRAMES = [
    "Field bulletin", "Verification memo", "Monthly ledger", "Handoff note",
    "Quality review", "Operations record", "Assessment update", "Control summary",
]


def number(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else str(round(value, 4)).rstrip("0").rstrip(".")


def rotate_options(index: int, answer: str) -> list[str]:
    shift = index % 3
    options = OPTIONS[shift:] + OPTIONS[:shift]
    assert answer in options
    return options


def arm_for(seed: int, reader: str, item_id: str) -> str:
    digest = hashlib.sha256(f"{seed}|{reader}|{item_id}".encode()).digest()
    return "ainglish" if digest[0] % 2 else "english"


def build_items() -> list[dict]:
    items = []
    for index, (condition, label, metric, direction, base, delta, final) in enumerate(ROWS, 1):
        additive = base + delta if direction == "rose" else base - delta
        relative = base * (1 + delta / 100 if direction == "rose" else 1 - delta / 100)
        if condition == "clean":
            assert math.isclose(final, additive)
            answer = "consistent"
        elif condition == "collision":
            assert math.isclose(final, relative) and not math.isclose(final, additive)
            answer = "contradictory"
        else:
            assert not math.isclose(final, additive) and not math.isclose(final, relative)
            answer = "contradictory"
        frame = FRAMES[(index - 1) % len(FRAMES)]
        stem = (f"{frame}: the {metric} {direction} by {delta}% during the comparison window, "
                f"from {number(base)}% to {number(final)}%.")
        marked = (f"{frame}: the {metric} {direction} by {delta} percentage points during the "
                  f"comparison window, from {number(base)}% to {number(final)}%.")
        items.append({
            "id": f"dex-pp-det-rep-{index:02d}-{label}",
            "english": stem,
            "ainglish": marked,
            "question": QUESTION,
            "options": rotate_options(index - 1, answer),
            "answer": answer,
            "cell": "endpoints_present",
            "condition": condition,
            "writer_intent": "additive percentage-point change",
            "numbers": {
                "base": base,
                "delta_pp": delta,
                "final_stated": final,
                "final_additive": additive,
                "final_relative": round(relative, 4),
            },
            "clean_twin_marked_arm": (
                f"{frame}: the {metric} {direction} by {delta} percentage points during the "
                f"comparison window, from {number(base)}% to {number(additive)}%."
            ),
            "mutable_field": None if condition == "clean" else "final value",
        })

    calibration = [
        ("consistent", "The reconciliation note was checked.",
         "The reconciliation note was checked; its numeric claims were explicitly verified as consistent."),
        ("contradictory", "The sampling note was checked.",
         "The sampling note was checked; its numeric claims were explicitly found contradictory."),
        ("consistent", "The allocation note was checked.",
         "The allocation note was checked; its numeric claims were explicitly verified as consistent."),
        ("contradictory", "The retention note was checked.",
         "The retention note was checked; its numeric claims were explicitly found contradictory."),
    ]
    for index, (answer, english, ainglish) in enumerate(calibration, 1):
        items.append({
            "id": f"dex-pp-det-rep-cal-{index:02d}",
            "calibration": True,
            "english": english,
            "ainglish": ainglish,
            "question": "What verdict about the numeric claims does the note explicitly state?",
            "options": rotate_options(index + 31, answer),
            "answer": answer,
        })
    return items


def passing_seed(items: list[dict], start: int, reader: str) -> tuple[int, dict]:
    real = [item for item in items if not item.get("calibration")]
    for seed in range(start, start + 1_000_000):
        cells = Counter((item["condition"], arm_for(seed, reader, item["id"])) for item in real)
        if any(cells[(condition, arm)] != target for condition, target in
               (("clean", 8), ("collision", 4), ("break_both", 4))
               for arm in ("english", "ainglish")):
            continue
        positions = {arm: Counter() for arm in ("english", "ainglish")}
        for item in real:
            arm = arm_for(seed, reader, item["id"])
            positions[arm][item["options"].index(item["answer"])] += 1
        if all(max(counts.values()) - min(counts.values()) <= 1
               and set(counts) == {0, 1, 2} for counts in positions.values()):
            return seed, {
                "condition_arm_counts": {f"{condition}/{arm}": cells[(condition, arm)]
                                         for condition in ("clean", "collision", "break_both")
                                         for arm in ("english", "ainglish")},
                "correct_option_positions": {
                    arm: {str(position): count for position, count in sorted(counts.items())}
                    for arm, counts in positions.items()
                },
            }
    raise RuntimeError("no balanced seed found in search window")


def main() -> None:
    items = build_items()
    canonical = json.dumps(items, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    canonical_sha = hashlib.sha256(canonical).hexdigest()
    reader = "Dexagon-local-Gemma3-12B-Q4_K_M"
    seed, deal = passing_seed(items, int(canonical_sha[:8], 16), reader)
    document = {
        "sha256": canonical_sha,
        "design": ("fresh different-manifest replication of 0ad586c99e429f93234d7ab45c25be06a578585e219ba56236409a3305c97cd2; "
                   "endpoints-present detectability, writer intent additive, 16 clean / 8 relative-collision / 8 break-both"),
        "items": items,
    }
    encoded = json.dumps(document, indent=1, ensure_ascii=False).encode()
    OUT.write_bytes(encoded)
    print(json.dumps({
        "output": str(OUT),
        "exact_file_sha256": hashlib.sha256(encoded).hexdigest(),
        "sdk_items_sha256": canonical_sha,
        "items": len(items),
        "real": 32,
        "calibration": 4,
        "reader": reader,
        "seed_start": int(canonical_sha[:8], 16),
        "seed": seed,
        "deal": deal,
        "reader_calls": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
