#!/usr/bin/env python3
"""Freeze a deletion-capable approx(N) robustness challenge without reader calls.

This is deliberately a *new original*, not a replication of bb920921...: changing the
corruption channel from substitution to deletion changes a load-bearing rule.  The seed search
uses only item bytes and the released harness's deterministic corrupt() output.  It cannot see,
and never invokes, a model answer.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ITEMS_OUT = ROOT / "items.json"
CALIBRATION_OUT = ROOT / "calibration.json"
RECEIPT_OUT = ROOT / "corruption-receipt.json"
PANEL_SHA256 = "7e5b4234b2b28b5c7366dc429d78425ac2ac1f74ff9a6bdd59db01324620dbaa"
ORIGINAL_HASH = "bb920921f943941bbbde35db423dd6df225874f679c6ae6b911b9b80db8a2d9a"
OPTIONS = ["approximate", "exact", "cannot tell"]
QUESTION = (
    "What did the writer declare about the numeric figure: is it approximate, exact, "
    "or was no such declaration made (cannot tell)?"
)

# Fresh, terse agent-message surfaces keep a one-character event near the claim carrier.  No
# sentence or number is copied from the original 30-item artifact.
ROWS = [
    ("ETA", "6", "min"),
    ("load", "73", "pct"),
    ("queue", "28", "jobs"),
    ("cache", "3", "GB"),
    ("delay", "11", "sec"),
    ("cost", "64", "credits"),
    ("rate", "14", "req/s"),
    ("age", "5", "days"),
    ("batch", "460", "rows"),
    ("risk", "18", "pct"),
    ("uptime", "97", "pct"),
    ("drift", "9", "ms"),
    ("workers", "42", "nodes"),
    ("window", "17", "min"),
    ("volume", "760", "MB"),
    ("budget", "85", "tokens"),
    ("depth", "23", "levels"),
    ("span", "13", "months"),
    ("sample", "340", "cases"),
    ("retry", "7", "times"),
    ("fanout", "31", "peers"),
    ("jitter", "4", "ms"),
    ("lag", "16", "blocks"),
    ("coverage", "81", "pct"),
    ("throughput", "520", "msg/s"),
    ("storage", "6", "TB"),
    ("warmup", "19", "sec"),
    ("backlog", "270", "tasks"),
    ("confidence", "74", "pct"),
    ("lifetime", "8", "years"),
    ("burst", "55", "events"),
    ("margin", "12", "pct"),
    ("latency", "21", "ms"),
    ("replicas", "10", "hosts"),
    ("interval", "33", "sec"),
    ("payload", "900", "KB"),
    ("capacity", "68", "slots"),
    ("retention", "15", "days"),
    ("accuracy", "89", "pct"),
    ("rollout", "26", "sites"),
    ("timeout", "44", "sec"),
    ("traffic", "610", "req/min"),
    ("reserve", "32", "units"),
    ("refresh", "7", "hours"),
    ("errors", "2", "pct"),
    ("cohort", "390", "agents"),
    ("cycle", "24", "days"),
    ("savings", "58", "credits"),
]


def rotate_options(index: int, answer: str) -> list[str]:
    shift = index % len(OPTIONS)
    options = OPTIONS[shift:] + OPTIONS[:shift]
    assert answer in options
    return options


def build_items() -> list[dict]:
    items = []
    for index, (label, number, unit) in enumerate(ROWS, 1):
        answer = "approximate"
        items.append({
            "id": f"dex-approx-drop-R-{index:02d}",
            "english": f"{label}: ~{number} {unit}.",
            "ainglish": f"{label}: approx({number}) {unit}.",
            "question": QUESTION,
            "options": rotate_options(index - 1, answer),
            "answer": answer,
        })

    calibration = [
        ("license", "16", "seats", "approximate"),
        ("depot", "640", "units", "approximate"),
        ("term", "27", "months", "approximate"),
        ("invoice", "9", "lines", "exact"),
        ("vault", "6", "keys", "exact"),
        ("panel", "11", "members", "exact"),
    ]
    for index, (label, number, unit, answer) in enumerate(calibration, 1):
        marker = "approx" if answer == "approximate" else "exactly"
        items.append({
            "id": f"dex-approx-drop-C-{index:02d}",
            "calibration": True,
            "english": f"{label}: {number} {unit}.",
            "ainglish": (
                f"{label}: approx({number}) {unit}." if marker == "approx"
                else f"{label}: exactly {number} {unit}."
            ),
            "question": QUESTION,
            "options": rotate_options(index + len(ROWS) - 1, answer),
            "answer": answer,
        })
    ids = [item["id"] for item in items]
    assert len(ids) == len(set(ids)) == 54
    real = [item for item in items if not item.get("calibration")]
    assert len(real) == 48
    for item in real:
        assert item["english"].count("~") == 1
        match = re.search(r"~([^ ]+)", item["english"])
        assert match is not None
        assert item["ainglish"] == item["english"].replace(
            match.group(0), f"approx({match.group(1)})", 1
        )
    return items


def load_panel(path: Path):
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != PANEL_SHA256:
        raise SystemExit(
            f"panel.py sha256 {digest} is not the frozen SDK 0.2.29 byte hash {PANEL_SHA256}"
        )
    spec = importlib.util.spec_from_file_location("ainglish_029_panel", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def deleted_position(before: str, after: str) -> tuple[int, str]:
    if len(after) != len(before) - 1:
        raise AssertionError("drop_char did not remove exactly one code point")
    index = next((i for i, (left, right) in enumerate(zip(before, after)) if left != right), len(after))
    if before[:index] + before[index + 1:] != after:
        raise AssertionError("drop_char changed bytes other than its one deletion")
    return index, before[index]


def carrier_positions(text: str, arm: str) -> set[int]:
    if arm == "english":
        positions = {i for i, char in enumerate(text) if char == "~"}
        assert len(positions) == 1
        return positions
    match = re.search(r"approx\([^)]*\)", text)
    assert match is not None
    # The value inside the parentheses is payload.  The six letters and both parentheses carry
    # the approximation declaration and are the claim-marker deletion surface.
    opening = text.index("(", match.start(), match.end())
    closing = match.end() - 1
    return set(range(match.start(), opening + 1)) | {closing}


def corruption_receipt(items: list[dict], seed: int, panel) -> dict:
    cells = []
    counts = {"english": 0, "ainglish": 0, "paired": 0}
    real = [item for item in items if not item.get("calibration")]
    per_item = {}
    for item in real:
        hits = {}
        for arm in ("english", "ainglish"):
            before = item[arm]
            key = f"{seed}:{item['id']}:{arm}"
            after = panel.corrupt(before, key, "drop_char")
            index, deleted = deleted_position(before, after)
            hit = index in carrier_positions(before, arm)
            hits[arm] = hit
            counts[arm] += int(hit)
            cell = {
                "item_id": item["id"],
                "arm": arm,
                "key": key,
                "baseline": before,
                "corrupted": after,
                "deleted_index": index,
                "deleted_character": deleted,
                "claim_marker_hit": hit,
                "deletion_class": "claim_marker" if hit else "payload_or_context",
            }
            cells.append(cell)
        paired = hits["english"] and hits["ainglish"]
        counts["paired"] += int(paired)
        per_item[item["id"]] = paired
    return {
        "kind": "ainglish.corruption-freeze.v1",
        "sdk_version": "0.2.29",
        "sdk_release_commit": "f03150869bd06cf2fd50f13ce276de556e55ec99",
        "panel_py_sha256": PANEL_SHA256,
        "channel": "drop_char",
        "seed": seed,
        "scored_items": len(real),
        "coverage": {
            "english_tilde_hits": counts["english"],
            "ainglish_approx_marker_hits": counts["ainglish"],
            "paired_marker_hits": counts["paired"],
            "english_rate": counts["english"] / len(real),
            "ainglish_rate": counts["ainglish"] / len(real),
            "paired_rate": counts["paired"] / len(real),
        },
        "classification": (
            "English claim carrier is the single '~'. Ainglish claim carrier is the six letters "
            "of 'approx', its opening parenthesis, and its closing parenthesis; enclosed digits "
            "are payload. Classification is positional and computed before reader calls."
        ),
        "cells": cells,
    }


def coverage_passes(receipt: dict) -> bool:
    coverage = receipt["coverage"]
    return (
        coverage["english_tilde_hits"] >= 6
        and coverage["ainglish_approx_marker_hits"] >= 20
        and coverage["paired_marker_hits"] >= 3
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel", required=True, type=Path, help="exact SDK 0.2.29 panel.py")
    args = parser.parse_args()
    panel = load_panel(args.panel)
    all_items = build_items()
    items = [item for item in all_items if not item.get("calibration")]
    calibration = [item for item in all_items if item.get("calibration")]
    canonical = json.dumps(items, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    items_sha256 = hashlib.sha256(canonical).hexdigest()

    # Deterministic, pre-inference exposure rule: start at the item digest prefix and take the
    # first seed meeting the declared minimum carrier-hit counts.  This is a deletion challenge,
    # not an estimate of ambient byte-loss prevalence.  No reader is imported or called here.
    seed_start = int(items_sha256[:8], 16)
    for seed in range(seed_start, seed_start + 1_000_000):
        receipt = corruption_receipt(items, seed, panel)
        if coverage_passes(receipt):
            break
    else:
        raise SystemExit("no seed met the preregistered coverage gate in one million candidates")

    document = {
        "sha256": items_sha256,
        "design": (
            "48 fresh scored approx(N)/~N minimal pairs plus six calibration items for a new "
            "deletion-capable robustness_delta original; not a replication of substitution-channel "
            f"row {ORIGINAL_HASH}"
        ),
        "items": items,
    }
    ITEMS_OUT.write_text(json.dumps(document, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    CALIBRATION_OUT.write_text(
        json.dumps({"items": calibration}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    receipt.update({
        "items_sdk_sha256": items_sha256,
        "items_exact_file_sha256": hashlib.sha256(ITEMS_OUT.read_bytes()).hexdigest(),
        "seed_selection": {
            "start": seed_start,
            "rule": (
                "first integer seed at or above int(items_sdk_sha256[:8], 16) with at least "
                "6/48 English tilde hits, 20/48 Ainglish approx-marker hits, and 3/48 paired hits"
            ),
            "candidates_examined": seed - seed_start + 1,
            "uses_reader_outputs": False,
        },
        "interpretation_boundary": (
            "Exposure-enriched carrier-deletion challenge. The coverage rates are properties of "
            "this frozen deal and must not be represented as real-world deletion prevalence."
        ),
    })
    RECEIPT_OUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({
        "items": str(ITEMS_OUT),
        "calibration": str(CALIBRATION_OUT),
        "receipt": str(RECEIPT_OUT),
        "items_sdk_sha256": items_sha256,
        "items_exact_file_sha256": receipt["items_exact_file_sha256"],
        "calibration_exact_file_sha256": hashlib.sha256(CALIBRATION_OUT.read_bytes()).hexdigest(),
        "receipt_exact_file_sha256": hashlib.sha256(RECEIPT_OUT.read_bytes()).hexdigest(),
        "seed": seed,
        "seed_candidates_examined": receipt["seed_selection"]["candidates_examined"],
        "coverage": receipt["coverage"],
        "reader_calls": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
