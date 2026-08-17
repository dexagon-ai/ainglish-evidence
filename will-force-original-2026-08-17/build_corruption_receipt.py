#!/usr/bin/env python3
"""Freeze an exposure-enriched corruption deal without reader inference.

The seed search can inspect only deterministic corrupted bytes and declared
semantic-carrier spans.  It cannot import, invoke, or inspect a reader.  This is
a direct carrier stress test, not an estimate of ambient character-error rates.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ITEMS_FILE = ROOT / "robustness-items.json"
OUT = ROOT / "corruption-freeze-receipt.json"
SDK_VERSION = "0.2.32"
SDK_RELEASE_COMMIT = "4036874b3816599ee66afe1e2a75b075b9bacbbf"


def panel_module():
    import ainglish.panel

    path = Path(ainglish.panel.__file__).resolve()
    raw = path.read_bytes()
    spec = importlib.util.spec_from_file_location("ainglish_032_frozen_panel", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module, path, hashlib.sha256(raw).hexdigest()


def spans(text: str, needles: list[str]) -> set[int]:
    positions: set[int] = set()
    for needle in needles:
        start = text.index(needle)
        positions.update(range(start, start + len(needle)))
    return positions


def carrier_positions(item: dict, arm: str) -> set[int]:
    text = item[arm]
    form = item["form"]
    if arm == "ainglish":
        return spans(text, [form])
    if form == "will-as-promise":
        return spans(text, ["promise", "commits me to bringing that result about"])
    if form == "will-as-plan":
        return spans(text, ["current plan", "must tell you if it does"])
    if form == "will-as-forecast":
        return spans(text, ["expect", "prediction and does not commit me to cause it"])
    raise AssertionError(form)


def changed_position(before: str, after: str) -> tuple[int, str, str]:
    changed = [i for i, (left, right) in enumerate(zip(before, after)) if left != right]
    if len(changed) != 1 or len(before) != len(after):
        raise AssertionError("corrupt_char did not replace exactly one code point")
    index = changed[0]
    return index, before[index], after[index]


def receipt_for(items: list[dict], seed: int, panel) -> dict:
    cells = []
    counts = {"english": 0, "ainglish": 0, "paired": 0}
    per_form = {
        form: {"english": 0, "ainglish": 0, "paired": 0}
        for form in ("will-as-promise", "will-as-plan", "will-as-forecast")
    }
    for item in items:
        hit = {}
        for arm in ("english", "ainglish"):
            key = f"{seed}:{item['id']}:{arm}"
            before = item[arm]
            after = panel.corrupt(before, key, "corrupt_char")
            index, old, new = changed_position(before, after)
            is_hit = index in carrier_positions(item, arm)
            hit[arm] = is_hit
            counts[arm] += int(is_hit)
            per_form[item["form"]][arm] += int(is_hit)
            cells.append({
                "item_id": item["id"],
                "form": item["form"],
                "arm": arm,
                "key": key,
                "baseline": before,
                "corrupted": after,
                "changed_index": index,
                "old": old,
                "new": new,
                "force_carrier_hit": is_hit,
            })
        paired = hit["english"] and hit["ainglish"]
        counts["paired"] += int(paired)
        per_form[item["form"]]["paired"] += int(paired)
    return {"seed": seed, "counts": counts, "per_form": per_form, "cells": cells}


def passes(receipt: dict) -> bool:
    # At least half the deal directly corrupts each representation's force
    # carrier and at least a quarter does so in both paired arms, with all three
    # forms represented.  Remaining rows retain a context/payload corruption
    # control.
    return (
        receipt["counts"]["english"] >= 12
        and receipt["counts"]["ainglish"] >= 12
        and receipt["counts"]["paired"] >= 6
        and all(row["paired"] >= 1 for row in receipt["per_form"].values())
    )


def main() -> None:
    from ainglish import __version__

    if __version__ != SDK_VERSION:
        raise SystemExit(f"REFUSING: SDK {__version__} != frozen {SDK_VERSION}")
    document = json.loads(ITEMS_FILE.read_text(encoding="utf-8"))
    items = document["items"]
    panel, panel_path, panel_sha256 = panel_module()
    start = int(document["sha256"][:8], 16)
    for seed in range(start, start + 2_000_000):
        receipt = receipt_for(items, seed, panel)
        if passes(receipt):
            break
    else:
        raise SystemExit("no seed met the frozen coverage rule in two million candidates")

    receipt.update({
        "kind": "ainglish.corruption-freeze.v1:will-force-carrier-stress",
        "sdk_version": SDK_VERSION,
        "sdk_release_commit": SDK_RELEASE_COMMIT,
        "panel_py_path_at_freeze": str(panel_path),
        "panel_py_sha256": panel_sha256,
        "items_sdk_sha256": document["sha256"],
        "items_exact_file_sha256": hashlib.sha256(ITEMS_FILE.read_bytes()).hexdigest(),
        "channel": "corrupt_char",
        "seed_selection": {
            "start": start,
            "rule": (
                "first integer seed with >=12/24 carrier hits in each arm, >=6/24 paired "
                "carrier hits, and >=1 paired hit for each of the three forms"
            ),
            "candidates_examined": seed - start + 1,
            "uses_reader_outputs": False,
        },
        "interpretation_boundary": (
            "Exposure-enriched direct force-carrier stress test. Hit rates describe this frozen "
            "deal and must not be represented as ambient character-error prevalence."
        ),
        "reader_calls": 0,
    })
    OUT.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "seed": seed,
        "candidates_examined": receipt["seed_selection"]["candidates_examined"],
        "counts": receipt["counts"],
        "per_form": receipt["per_form"],
        "panel_py_sha256": panel_sha256,
        "reader_calls": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
