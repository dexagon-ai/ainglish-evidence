#!/usr/bin/env python3
"""Build fresh endpoints-absent correctness items without reader calls.

Every scientific pair differs only in the change phrase.  A neutral approximate
headcount anchor elsewhere in the message pins the writer's intended reading,
but neither arm states the final percentage.  The item set targets Reticuli's
f9e78cc0... comprehension original and does not reuse Dexagon's endpoints-
present or detectability scenarios.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "items.json"
OPTIONS = ("ADD_FINAL", "REL_FINAL", "cannot tell from the message")
READERS = (
    "mistral-small3.2-24b-pp-task-q4_k_m",
    "gemma3-12b-pp-task-q4_k_m",
)

# label, metric, direction, base percentage, stated magnitude
ADDITIVE = [
    ("prenatal", "prenatal appointment attendance rate", "rose", 61, 7),
    ("digitisation", "manuscript digitisation completion rate", "rose", 34, 9),
    ("soil", "soil-sample contamination rate", "fell", 18, 5),
    ("telescope", "telescope observation success rate", "rose", 47, 6),
    ("cold-store", "vaccine cold-storage compliance rate", "rose", 72, 8),
    ("legal-aid", "legal-aid intake abandonment rate", "fell", 29, 4),
    ("buoy", "coastal buoy reporting rate", "rose", 53, 11),
    ("interloan", "library interloan rejection rate", "fell", 24, 7),
    ("food", "food-inspection pass rate", "rose", 66, 5),
    ("wildfire", "wildfire sensor outage rate", "fell", 16, 3),
    ("scholarship", "scholarship acceptance rate", "rose", 38, 12),
    ("meter", "water-meter unreadable rate", "fell", 21, 6),
    ("freight-seal", "freight-seal verification rate", "rose", 57, 4),
    ("archaeology", "archaeology catalogue omission rate", "fell", 13, 5),
    ("hearing", "hearing transcript error rate", "fell", 19, 7),
    ("habitat-photo", "habitat photo rejection rate", "fell", 27, 8),
]

RELATIVE = [
    ("telemedicine", "telemedicine follow-up completion rate", "rose", 40, 15),
    ("grant", "grant disbursement delay rate", "fell", 60, 10),
    ("rail-refund", "rail-ticket refund completion rate", "rose", 80, 5),
    ("air-alert", "air-quality false-alert rate", "fell", 50, 20),
    ("fishery", "fishery licence renewal rate", "rose", 25, 20),
    ("audio-guide", "museum audio-guide failure rate", "fell", 75, 8),
    ("cloud-filter", "satellite-image cloud-filter pass rate", "rose", 30, 20),
    ("shelter", "emergency-shelter no-show rate", "fell", 45, 20),
    ("seed-bank", "seed-bank germination rate", "rose", 70, 10),
    ("court", "court-filing rejection rate", "fell", 20, 25),
    ("reef", "reef-survey image acceptance rate", "rose", 64, 25),
    ("ambulance", "ambulance handoff delay rate", "fell", 32, 25),
    ("orchard", "orchard pollination coverage rate", "rose", 90, 10),
    ("archive-box", "archive-box mislabelling rate", "fell", 55, 20),
    ("flood-map", "flood-map validation rate", "rose", 48, 25),
    ("labour", "labour-inspection appeal rate", "fell", 35, 20),
]

FRAMES = (
    "Sampling note", "Audit update", "Field memo", "Operations brief",
    "Review record", "Handoff summary", "Control note", "Monthly report",
)

CALIBRATION = [
    ("harbour", "harbour inspection clearance rate", 41, 48),
    ("clinic", "clinic referral completion rate", 56, 63),
    ("forest", "forest plot coverage rate", 68, 72),
    ("permit", "permit correction rate", 37, 31),
    ("ferry", "ferry boarding success rate", 74, 79),
    ("nursery", "tree-nursery loss rate", 22, 17),
    ("court-cal", "court notice delivery rate", 83, 88),
    ("reservoir", "reservoir sensor fault rate", 19, 14),
]


def fmt(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else str(round(value, 4)).rstrip("0").rstrip(".")


def rotate_options(index: int, intent: str, additive_final: float, relative_final: float) -> list[str]:
    rendered = [f"{fmt(additive_final)}%", f"{fmt(relative_final)}%", OPTIONS[2]]
    shift = (index - 1 + (0 if intent == "additive" else 1)) % 3
    return rendered[shift:] + rendered[:shift]


def arm_for(seed: int, reader: str, item_id: str) -> str:
    digest = hashlib.sha256(f"{seed}|{reader}|{item_id}".encode()).digest()
    return "ainglish" if digest[0] % 2 else "english"


def real_item(index: int, row: tuple, intent: str) -> dict:
    label, metric, direction, base, magnitude = row
    sign = 1 if direction == "rose" else -1
    additive_final = base + sign * magnitude
    relative_final = base * (1 + sign * magnitude / 100)
    intended_final = additive_final if intent == "additive" else relative_final
    assert additive_final != relative_final
    change_pp = abs(intended_final - base)
    anchor_count = int(round(change_pp * 10))
    assert abs(anchor_count / 10 - change_pp) < 1e-9
    base_count = base * 10
    more_or_fewer = "additional" if direction == "rose" else "fewer"
    item_id = f"dex-pp-open-rep-{intent[:3]}-{index:02d}-{label}"
    frame = FRAMES[(index - 1) % len(FRAMES)]
    anchor = (
        f"{frame}: before the change, {base_count} of every 1,000 observations met the "
        f"named condition ({base}%). The latest sample has approximately {anchor_count} "
        f"{more_or_fewer} such observations per 1,000."
    )
    english = f"{anchor} The {metric} {direction} {magnitude}%."
    marked_change = (
        f"{magnitude} percentage points" if intent == "additive" else f"{magnitude}% relative"
    )
    ainglish = f"{anchor} The {metric} {direction} {marked_change}."
    options = rotate_options(index, intent, additive_final, relative_final)
    answer = f"{fmt(intended_final)}%"
    assert answer in options
    return {
        "id": item_id,
        "english": english,
        "ainglish": ainglish,
        "question": f"What new percentage does the writer intend for the {metric}?",
        "options": options,
        "answer": answer,
        "intent": intent,
        "direction": direction,
        "domain": label,
        "numbers": {
            "base_percent": base,
            "stated_magnitude": magnitude,
            "anchor_change_per_1000": anchor_count,
            "additive_final_percent": additive_final,
            "relative_final_percent": relative_final,
        },
    }


def calibration_item(index: int, row: tuple) -> dict:
    label, metric, old_rate, new_rate = row
    item_id = f"dex-pp-open-rep-cal-{index:02d}-{label}"
    old_count = old_rate * 10
    new_count = new_rate * 10
    english = (
        f"Calibration note: the previous sample had {old_count} of every 1,000 observations "
        f"meeting the condition ({old_rate}%). A new sample was collected, but its count is not stated."
    )
    ainglish = (
        f"Calibration note: the previous sample had {old_count} of every 1,000 observations "
        f"meeting the condition ({old_rate}%). The new sample has {new_count} of every 1,000 "
        "observations meeting it."
    )
    distractor = old_rate + (old_rate - new_rate)
    if distractor == new_rate or not 0 <= distractor <= 100:
        distractor = old_rate
    options = [f"{new_rate}%", f"{distractor}%", "cannot tell from the message"]
    shift = sum(item_id.encode("utf-8")) % 3
    options = options[shift:] + options[:shift]
    return {
        "id": item_id,
        "calibration": True,
        "english": english,
        "ainglish": ainglish,
        "question": f"What percentage does the new sample report for the {metric}?",
        "options": options,
        "answer": f"{new_rate}%",
    }


def balanced_seed(items: list[dict], start: int) -> tuple[int, dict]:
    real = [item for item in items if not item.get("calibration")]
    for seed in range(start, start + 2_000_000):
        counts = Counter(
            (reader, item["intent"], item["direction"], arm_for(seed, reader, item["id"]))
            for reader in READERS for item in real
        )
        if any(
            not 14 <= sum(
                counts[(reader, intent, direction, arm)]
                for intent in ("additive", "relative") for direction in ("rose", "fell")
            ) <= 18
            for reader in READERS for arm in ("english", "ainglish")
        ):
            continue
        if any(
            not 14 <= sum(counts[(reader, intent, direction, arm)] for reader in READERS for direction in ("rose", "fell")) <= 18
            for intent in ("additive", "relative")
            for arm in ("english", "ainglish")
        ):
            continue
        if any(
            not 14 <= sum(counts[(reader, intent, direction, arm)] for reader in READERS for intent in ("additive", "relative")) <= 18
            for direction in ("rose", "fell")
            for arm in ("english", "ainglish")
        ):
            continue
        if any(sum(counts[(reader, intent, direction, arm)] for reader in READERS
                   for intent in ("additive", "relative") for direction in ("rose", "fell")) != 32
               for arm in ("english", "ainglish")):
            continue
        if any(
            not 2 <= counts[(reader, intent, direction, arm)] <= 6
            for reader in READERS
            for intent in ("additive", "relative")
            for direction in ("rose", "fell")
            for arm in ("english", "ainglish")
        ):
            continue
        positions = {arm: Counter() for arm in ("english", "ainglish")}
        for reader in READERS:
            for item in real:
                arm = arm_for(seed, reader, item["id"])
                positions[arm][item["options"].index(item["answer"])] += 1
        if all(
            set(counts_) == {0, 1, 2} and max(counts_.values()) - min(counts_.values()) <= 3
            for counts_ in positions.values()
        ):
            return seed, {
                "stratum_arm_counts": {
                    f"{reader}/{intent}/{direction}/{arm}": counts[(reader, intent, direction, arm)]
                    for reader in READERS
                    for intent in ("additive", "relative")
                    for direction in ("rose", "fell")
                    for arm in ("english", "ainglish")
                },
                "correct_option_positions": {
                    arm: {str(k): v for k, v in sorted(positions[arm].items())}
                    for arm in ("english", "ainglish")
                },
            }
    raise RuntimeError("no fully balanced seed found")


def main() -> None:
    items = [real_item(i, row, "additive") for i, row in enumerate(ADDITIVE, 1)]
    items += [real_item(i, row, "relative") for i, row in enumerate(RELATIVE, 1)]
    items += [calibration_item(i, row) for i, row in enumerate(CALIBRATION, 1)]
    items.sort(key=lambda item: item["id"])

    real = [item for item in items if not item.get("calibration")]
    calibration = [item for item in items if item.get("calibration")]
    assert len(real) == 32 and len(calibration) == 8
    assert len({item["id"] for item in items}) == len(items)
    assert Counter(item["intent"] for item in real) == {"additive": 16, "relative": 16}
    assert Counter((item["intent"], item["direction"]) for item in real) == {
        ("additive", "rose"): 8,
        ("additive", "fell"): 8,
        ("relative", "rose"): 8,
        ("relative", "fell"): 8,
    }
    assert all(item["english"] != item["ainglish"] for item in items)
    assert all(item["answer"] in item["options"] for item in items)

    canonical = json.dumps(items, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    canonical_sha = hashlib.sha256(canonical).hexdigest()
    seed, deal = balanced_seed(items, int(canonical_sha[:8], 16))
    document = {
        "kind": "dexagon.percentage_points_opener_replication.items.v1",
        "sdk_items_sha256": canonical_sha,
        "design": (
            "32 fresh endpoints-absent correctness scenarios: 16 additive and 16 relative intent; "
            "each intent splits 8 rise and 8 fall; approximate per-1000 headcount anchors pin intent"
        ),
        "items": items,
    }
    encoded = json.dumps(document, indent=1, ensure_ascii=False).encode()
    OUT.write_bytes(encoded)
    print(json.dumps({
        "output": str(OUT),
        "exact_file_sha256": hashlib.sha256(encoded).hexdigest(),
        "sdk_items_sha256": canonical_sha,
        "items": len(items),
        "real": len(real),
        "calibration": len(calibration),
        "seed_start": int(canonical_sha[:8], 16),
        "seed": seed,
        "deal": deal,
        "reader_calls": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
