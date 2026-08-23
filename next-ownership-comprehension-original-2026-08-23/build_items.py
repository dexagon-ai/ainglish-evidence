#!/usr/bin/env python3
"""Freeze balanced next-step ownership comprehension items without reader calls."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

from ainglish.panel import arm_for


ROOT = Path(__file__).resolve().parent
READERS = [
    "mistral-small3.2-24b-pp-task-q4_k_m",
    "gemma3-12b-pp-task-q4_k_m",
]
MARKERS = ("next-you", "next-me", "next-any", "next-none")
OPTIONS = [
    "addressee",
    "writer",
    "any one participant",
    "nobody",
]
ANSWERS = dict(zip(MARKERS, OPTIONS))
EXPANSIONS = {
    "next-you": "The next step belongs to you, the addressee.",
    "next-me": "The next step remains with me, the writer.",
    "next-any": "Any participant may claim the next step; one taker is sufficient.",
    "next-none": "No further step is owed by anyone.",
}
QUESTION = "Who owns the next step?"

ROWS = [
    ("checksum", "The checksum table is ready.", "next-you"),
    ("invoice", "The invoice variance is documented.", "next-me"),
    ("mirrors", "The stale mirrors need checking.", "next-any"),
    ("archive", "The incident summary is archived.", "next-none"),
    ("consent", "The consent forms are indexed.", "next-me"),
    ("venue", "The venue options are listed.", "next-any"),
    ("sensor", "The sensor fault is isolated.", "next-none"),
    ("release", "The release notes are drafted.", "next-you"),
    ("ledger", "The ledger discrepancy is marked.", "next-any"),
    ("certificate", "The certificate request is prepared.", "next-you"),
    ("batch", "The failed batch is quarantined.", "next-none"),
    ("archive-team", "The archive contact is identified.", "next-me"),
    ("manifests", "The two manifests are available.", "next-you"),
    ("calibration-log", "The calibration log is attached.", "next-none"),
    ("diagram", "The corrected diagram is sketched.", "next-any"),
    ("duplicate", "The duplicate record is flagged.", "next-me"),
    ("labels", "The unused labels are collected.", "next-none"),
    ("snapshots", "The old snapshots are enumerated.", "next-me"),
    ("total", "The disputed total is highlighted.", "next-you"),
    ("glossary", "The glossary candidate is quoted.", "next-any"),
    ("signatures", "The final signatures are recorded.", "next-none"),
    ("sample", "The damaged sample is sealed.", "next-you"),
    ("meeting", "The meeting change is announced.", "next-me"),
    ("branch", "The obsolete branch is labelled.", "next-any"),
    ("reimbursement", "The reimbursement record is open.", "next-you"),
    ("key", "The replacement key is packaged.", "next-me"),
    ("alert", "The duplicate alert is acknowledged.", "next-none"),
    ("fallback", "The fallback route is documented.", "next-any"),
    ("translation", "The translation candidates are ranked.", "next-me"),
    ("window", "The migration window is confirmed.", "next-none"),
    ("access", "The access list is sorted.", "next-you"),
    ("inventory", "The inventory exceptions are grouped.", "next-any"),
]

CALIBRATION = [
    ("cal-handover", "The handover note is complete.", "next-you"),
    ("cal-draft", "The draft correction is scoped.", "next-me"),
    ("cal-cache", "The cache candidates are named.", "next-any"),
    ("cal-closure", "The closure receipt is filed.", "next-none"),
    ("cal-review", "The review packet is assembled.", "next-you"),
    ("cal-query", "The query revision is outlined.", "next-me"),
    ("cal-sample", "The sample folders are listed.", "next-any"),
    ("cal-final", "The final notice is posted.", "next-none"),
]


def rotate_options(index: int) -> list[str]:
    offset = index % len(OPTIONS)
    return OPTIONS[offset:] + OPTIONS[:offset]


def tagged(clause: str, marker: str) -> str:
    return clause.rstrip(".") + f", {marker}."


def find_seed() -> int:
    for seed in range(2026082301, 2026099999):
        ok = True
        assignments = {}
        for reader in READERS:
            rows = [
                (marker, arm_for(seed, reader, f"dex-next-{row_id}"))
                for row_id, _, marker in ROWS
            ]
            assignments[reader] = rows
            total = Counter(arm for _, arm in rows)
            if total["ainglish"] != 16:
                ok = False
                break
            for marker in MARKERS:
                count = sum(
                    arm == "ainglish" for row_marker, arm in rows if row_marker == marker
                )
                if not 3 <= count <= 5:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            first, second = (assignments[reader] for reader in READERS)
            opposite = {
                marker: sum(
                    left_arm != right_arm
                    for (left_marker, left_arm), (right_marker, right_arm)
                    in zip(first, second)
                    if left_marker == right_marker == marker
                )
                for marker in MARKERS
            }
            if not (14 <= sum(opposite.values()) <= 18 and all(3 <= n <= 5 for n in opposite.values())):
                ok = False
        if ok:
            return seed
    raise RuntimeError("no balanced seed found")


def make_items(comparator: str) -> list[dict]:
    items = []
    for index, (row_id, clause, marker) in enumerate(ROWS):
        english = clause if comparator == "untagged" else f"{clause} {EXPANSIONS[marker]}"
        items.append({
            "id": f"dex-next-{row_id}",
            "english": english,
            "ainglish": tagged(clause, marker),
            "question": QUESTION,
            "options": rotate_options(index),
            "answer": ANSWERS[marker],
            "marker": marker,
        })
    for offset, (row_id, clause, marker) in enumerate(CALIBRATION, start=len(items)):
        items.append({
            "id": row_id,
            "calibration": True,
            "english": clause,
            "ainglish": f"{clause} {EXPANSIONS[marker]}",
            "question": QUESTION,
            "options": rotate_options(offset),
            "answer": ANSWERS[marker],
            "marker": marker,
            "set": "heldout_explicit-owner_positive_control",
        })
    return items


def write(comparator: str, seed: int) -> None:
    items = make_items(comparator)
    digest = hashlib.sha256(json.dumps(
        items, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode()).hexdigest()
    document = {
        "kind": "dexagon.next_ownership.comprehension_items.v1",
        "comparator": comparator,
        "seed": seed,
        "sha256": digest,
        "design": (
            "32 scored messages balanced eight per hidden owner class, plus eight "
            "calibration rows. The untagged comparator deliberately withholds a balanced "
            "writer intent and forces four-way recovery; the careful comparator states "
            "the exact registered expansion."
        ),
        "items": items,
    }
    path = ROOT / f"{comparator}-items.json"
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"path": str(path), "items_sha256": digest, "items": len(items), "seed": seed}))


def main() -> None:
    counts = Counter(marker for _, _, marker in ROWS)
    if len(ROWS) != 32 or counts != Counter({marker: 8 for marker in MARKERS}):
        raise RuntimeError(f"scientific rows are not balanced: {counts}")
    if Counter(marker for _, _, marker in CALIBRATION) != Counter({marker: 2 for marker in MARKERS}):
        raise RuntimeError("calibration rows are not balanced")
    seed = find_seed()
    write("untagged", seed)
    write("careful", seed)


if __name__ == "__main__":
    main()
