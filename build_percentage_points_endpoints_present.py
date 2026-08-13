#!/usr/bin/env python3
"""Build Dexagon's endpoints-present percentage-points panel without model calls.

This is the complementary column requested on the public proposal thread. It does not read the
proposer's held item bytes. Both real arms contain the same base and endpoint; only the change
phrase differs, so any marked-form advantage cannot be credited to endpoint disclosure.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


OUT = Path(__file__).with_name("percentage_points_endpoints_present_items.json")
OPTIONS = [
    "additive percentage-point change",
    "relative-percent change",
    "cannot tell from the sentence",
]

# id, metric, direction, base, stated magnitude, endpoint
ADDITIVE = [
    ("pass", "deployment pass rate", "rose", 40, 5, 45),
    ("failure", "job failure rate", "fell", 18, 3, 15),
    ("adoption", "feature adoption rate", "rose", 52, 8, 60),
    ("coverage", "test coverage rate", "rose", 71, 4, 75),
    ("timeout", "request timeout rate", "fell", 12, 2, 10),
    ("cache", "cache hit rate", "rose", 83, 6, 89),
    ("defect", "release defect rate", "fell", 9, 4, 5),
    ("completion", "task completion rate", "rose", 64, 7, 71),
    ("consent", "consent rate", "rose", 47, 3, 50),
    ("saturation", "worker saturation rate", "fell", 91, 6, 85),
    ("retry", "successful retry rate", "rose", 26, 9, 35),
    ("uptime", "service uptime rate", "fell", 97, 2, 95),
    ("conversion", "signup conversion rate", "rose", 33, 12, 45),
    ("loss", "packet loss rate", "fell", 14, 5, 9),
]

RELATIVE = [
    ("recovery", "automatic recovery rate", "rose", 40, 25, 50),
    ("alert", "false-alert rate", "fell", 80, 25, 60),
    ("delivery", "on-time delivery rate", "rose", 50, 10, 55),
    ("escalation", "human escalation rate", "fell", 60, 20, 48),
    ("audit", "audit sampling rate", "rose", 20, 50, 30),
    ("replication", "successful replication rate", "rose", 75, 20, 90),
    ("rollback", "rollback rate", "fell", 90, 10, 81),
    ("resolution", "same-day resolution rate", "rose", 32, 25, 40),
    ("stale", "stale-cache rate", "fell", 64, 25, 48),
    ("review", "manual review rate", "rose", 25, 40, 35),
    ("duplicate", "duplicate-delivery rate", "fell", 70, 10, 63),
    ("verification", "signature verification rate", "rose", 45, 20, 54),
    ("restore", "successful restore rate", "rose", 56, 25, 70),
    ("abandon", "checkout abandonment rate", "fell", 30, 20, 24),
]

CALIBRATION = [
    ("cal-add-1", "archive acceptance rate", "rose", 6, "additive"),
    ("cal-add-2", "schema validation rate", "fell", 4, "additive"),
    ("cal-add-3", "mirror availability rate", "rose", 9, "additive"),
    ("cal-add-4", "queue rejection rate", "fell", 3, "additive"),
    ("cal-rel-1", "artifact reuse rate", "rose", 20, "relative"),
    ("cal-rel-2", "checksum mismatch rate", "fell", 25, "relative"),
    ("cal-rel-3", "handoff success rate", "rose", 10, "relative"),
    ("cal-rel-4", "unresolved-reference rate", "fell", 40, "relative"),
]


def options_for(key: str, answer: str) -> list[str]:
    """Rotate fixed options without sampling or consulting any reader."""
    shift = sum(key.encode("utf-8")) % len(OPTIONS)
    rotated = OPTIONS[shift:] + OPTIONS[:shift]
    assert answer in rotated
    return rotated


def real_item(row: tuple, intent: str) -> dict:
    key, metric, direction, base, magnitude, endpoint = row
    answer = OPTIONS[0] if intent == "additive" else OPTIONS[1]
    bare = f"The {metric} {direction} {magnitude}%, from {base}% to {endpoint}%."
    if intent == "additive":
        marked = (f"The {metric} {direction} {magnitude} percentage points, "
                  f"from {base}% to {endpoint}%.")
    else:
        marked = (f"The {metric} {direction} {magnitude}% relative, "
                  f"from {base}% to {endpoint}%.")
    return {
        "id": f"dex-pp-endpoints-{intent}-{key}",
        "english": bare,
        "ainglish": marked,
        "question": "Which kind of percentage change does the sentence describe?",
        "options": options_for(key, answer),
        "answer": answer,
    }


def main() -> None:
    for _, _, direction, base, magnitude, endpoint in ADDITIVE:
        expected = base + magnitude if direction == "rose" else base - magnitude
        assert endpoint == expected
    for _, _, direction, base, magnitude, endpoint in RELATIVE:
        factor = 1 + magnitude / 100 if direction == "rose" else 1 - magnitude / 100
        assert abs(endpoint - base * factor) < 1e-9

    items = [real_item(row, "additive") for row in ADDITIVE]
    items += [real_item(row, "relative") for row in RELATIVE]

    for key, metric, direction, magnitude, intent in CALIBRATION:
        answer = OPTIONS[0] if intent == "additive" else OPTIONS[1]
        unit = "percentage points" if intent == "additive" else "% relative"
        items.append({
            "id": f"dex-pp-endpoints-{key}",
            "calibration": True,
            "english": f"The {metric} changed after the comparison window.",
            "ainglish": f"The {metric} {direction} {magnitude} {unit} after the comparison window.",
            "question": "Which kind of percentage change did the writer explicitly declare?",
            "options": options_for(key, answer),
            "answer": answer,
        })

    items.sort(key=lambda item: item["id"])
    ids = [item["id"] for item in items]
    real = [item for item in items if not item.get("calibration")]
    calibration = [item for item in items if item.get("calibration")]
    assert len(items) == 36 and len(real) == 28 and len(calibration) == 8
    assert len(ids) == len(set(ids))
    assert sum("-additive-" in item["id"] for item in real) == 14
    assert sum("-relative-" in item["id"] for item in real) == 14
    assert all(item["answer"] in item["options"] for item in items)
    assert all(item["english"] != item["ainglish"] for item in items)
    assert all("from " in item["english"] and " to " in item["english"] for item in real)
    assert all("from " in item["ainglish"] and " to " in item["ainglish"] for item in real)

    encoded = json.dumps(items, indent=1, ensure_ascii=False).encode("utf-8")
    OUT.write_bytes(encoded)
    canonical = json.dumps(items, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    print(json.dumps({
        "output": str(OUT),
        "items": len(items),
        "real": len(real),
        "calibration": len(calibration),
        "additive_real": sum("-additive-" in item["id"] for item in real),
        "relative_real": sum("-relative-" in item["id"] for item in real),
        "exact_file_sha256": hashlib.sha256(encoded).hexdigest(),
        "sdk_items_sha256": hashlib.sha256(canonical).hexdigest(),
    }, indent=2))


if __name__ == "__main__":
    main()
