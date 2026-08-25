#!/usr/bin/env python3
"""Freeze proxy comprehension scenarios; make no external or model calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CELLS = [
    ("education", "the course is engaging", "the proportion of learners who opened week seven"),
    ("health", "the clinic is accessible", "the median distance travelled by booked patients"),
    ("security", "the service is secure", "the number of blocked login attempts"),
    ("operations", "the queue is healthy", "the median job completion time"),
    ("finance", "the programme is affordable", "the mean invoice amount"),
    ("transport", "the route is reliable", "the count of on-time arrivals"),
    ("research", "the intervention is effective", "the change in a surrogate biomarker"),
    ("moderation", "the forum is civil", "the number of removed messages"),
    ("procurement", "the supplier is dependable", "the fraction of orders shipped on schedule"),
    ("environment", "the river is healthy", "the dissolved-oxygen reading at one station"),
    ("employment", "the team is satisfied", "the voluntary departure rate"),
    ("software", "the interface is usable", "the median task-completion time in a scripted test"),
]
FRAMES = [
    {
        "question": "Is the measured quantity the same construct as the claim, and has the bridge from measure to claim been verified?",
        "options": ["same=yes; bridge-verified=yes", "same=yes; bridge-verified=no", "same=no; bridge-verified=yes", "same=no; bridge-verified=no"],
        "answer": "same=no; bridge-verified=no",
    },
    {
        "question": "Is the measured quantity distinct from the claim, and does the message leave their connection unverified?",
        "options": ["distinct=yes; connection-unverified=yes", "distinct=yes; connection-unverified=no", "distinct=no; connection-unverified=yes", "distinct=no; connection-unverified=no"],
        "answer": "distinct=yes; connection-unverified=yes",
    },
    {
        "question": "Is the measure identical to the claimed construct, and is the inferential step still unverified?",
        "options": ["identical=yes; step-unverified=yes", "identical=yes; step-unverified=no", "identical=no; step-unverified=yes", "identical=no; step-unverified=no"],
        "answer": "identical=no; step-unverified=yes",
    },
    {
        "question": "Are measure and construct different, and has their connection been demonstrated?",
        "options": ["different=yes; demonstrated=yes", "different=yes; demonstrated=no", "different=no; demonstrated=yes", "different=no; demonstrated=no"],
        "answer": "different=yes; demonstrated=no",
    },
]


def rotate(values: list[str], index: int) -> list[str]:
    shift = index % len(values)
    return values[shift:] + values[:shift]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def calibrations() -> list[dict]:
    rows = []
    objects = ["amber card", "blue key", "cedar token", "dune seal", "elm badge", "fern pass", "gold tag", "hazel slip"]
    for index, obj in enumerate(objects):
        rows.append({
            "id": f"proxy-cal-{index + 1:02d}",
            "calibration": True,
            "english": f"A note mentions the {obj} but gives no locker number.",
            "ainglish": f"A note states that the {obj} is in locker seven.",
            "question": "Does the note state that opening locker seven would find the named object?",
            "options": rotate(["yes", "no", "cannot tell"], index),
            "answer": "yes",
            "set": "construct-free explicit-location known positive",
        })
    return rows


def main() -> None:
    rows = []
    for index in range(96):
        domain, claim, measure = CELLS[index % len(CELLS)]
        wave = index // len(CELLS) + 1
        frame = FRAMES[index % len(FRAMES)]
        claim_text = f"In audit wave {wave}, {claim}"
        measure_text = f"{measure} in the fixed audit sample"
        rows.append({
            "id": f"proxy-{index + 1:03d}",
            "scenario_id": f"proxy-wave-{wave:02d}-{domain}",
            "arms": {
                "proxy": f"{claim_text} proxy({measure_text}).",
                "careful_english": (
                    f"{claim_text}. We directly verified {measure_text}. That measured quantity is not the claimed "
                    "construct, and the inferential step from the measure to the claim has not been demonstrated."
                ),
                "bare": f"{claim_text}, and we measured {measure_text}.",
                "obs": f"{claim_text} obs({measure_text}).",
            },
            "question": frame["question"],
            "options": rotate(frame["options"], index // len(FRAMES)),
            "answer": frame["answer"],
            "strata": {"domain": domain, "wave": wave, "question_frame": index % len(FRAMES)},
        })
    assert len(rows) == 96
    assert len({row["id"] for row in rows}) == len(rows)
    assert all(row["answer"] in row["options"] for row in rows)
    blob = canonical(rows)
    (ROOT / "items.json").write_bytes(blob + b"\n")
    receipt = {}
    for comparison, right_arm in (("careful", "careful_english"), ("bare", "bare"), ("obs", "obs")):
        scientific = [{
            "id": row["id"],
            "scenario_id": row["scenario_id"],
            "english": row["arms"][right_arm],
            "ainglish": row["arms"]["proxy"],
            "question": row["question"],
            "options": row["options"],
            "answer": row["answer"],
            "strata": dict(row["strata"], comparator=right_arm),
        } for row in rows]
        panel_rows = scientific + calibrations()
        panel_blob = canonical(panel_rows)
        payload = {
            "kind": "ainglish.proxy-comprehension-items.v1",
            "comparison": comparison,
            "sha256": hashlib.sha256(panel_blob).hexdigest(),
            "design": "96 scientific pairs plus eight construct-free planted-effect calibration rows",
            "items": panel_rows,
        }
        panel_path = ROOT / f"{comparison}-items.json"
        panel_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        receipt[comparison] = {"file": panel_path.name, "rows": len(panel_rows), "scientific": 96, "calibration": 8, "items_sha256": payload["sha256"]}
    index = {
        "kind": "ainglish.proxy-comprehension-carrier.v1",
        "rows": len(rows),
        "arms": ["proxy", "careful_english", "bare", "obs"],
        "items_sha256": hashlib.sha256(blob).hexdigest(),
        "question_frames": len(FRAMES),
        "domains": len(CELLS),
        "panel_packets": receipt,
    }
    (ROOT / "index.json").write_text(json.dumps(index, indent=2, sort_keys=True) + "\n")
    print(json.dumps(index, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
