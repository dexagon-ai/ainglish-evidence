#!/usr/bin/env python3
"""Audit v8 balance, semantics surface, digests, and exact novelty offline."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from build_development_plans import canonical, checked


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    packet = checked(ROOT / "holdout.json")
    rows = packet["items"]
    if len(rows) != 64 or len({row["id"] for row in rows}) != 64:
        raise SystemExit("REFUSING: holdout population drift")
    axes = {axis: [row for row in rows if row["axis"] == axis] for axis in packet["axes"]}
    if any(len(group) != 8 for group in axes.values()):
        raise SystemExit("REFUSING: axis balance drift")
    if any(sorted(row["options"]) != sorted(packet["labels"]) or row["answer"] not in row["options"] for row in rows):
        raise SystemExit("REFUSING: label/options drift")
    positions = [0, 0, 0]
    for row in rows:
        positions[row["options"].index(row["answer"])] += 1
    if positions != [22, 21, 21] or positions != packet["answer_positions"]:
        raise SystemExit("REFUSING: answer-position drift")
    forbidden = ("ainglish", "we-including-you", "this-once", "by-construction", "same-one", "moved-earlier")
    if any(any(term in (row["premise"] + " " + row["hypothesis"]).lower() for term in forbidden) for row in rows):
        raise SystemExit("REFUSING: target construct leaked into qualification")
    prior_pairs = set()
    for path in REPO.rglob("*.json"):
        if ROOT in path.parents:
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        stack = [value]
        while stack:
            current = stack.pop()
            if isinstance(current, dict):
                if isinstance(current.get("premise"), str) and isinstance(current.get("hypothesis"), str):
                    prior_pairs.add((current["premise"], current["hypothesis"]))
                stack.extend(current.values())
            elif isinstance(current, list):
                stack.extend(current)
    overlaps = sorted((row["id"], row["premise"], row["hypothesis"]) for row in rows if (row["premise"], row["hypothesis"]) in prior_pairs)
    if overlaps:
        raise SystemExit(f"REFUSING: prior exact input overlap {overlaps[:3]}")
    report = {
        "kind": "ainglish.panel.reader-qualification-holdout-audit.v8",
        "holdout_sha256": packet["content_sha256"],
        "items": len(rows),
        "axes": {axis: len(group) for axis, group in axes.items()},
        "labels": {label: sum(row["answer"] == label for row in rows) for label in packet["labels"]},
        "answer_positions": positions,
        "prior_exact_pair_overlap": 0,
        "target_construct_terms": 0,
        "model_calls": 0,
        "network_calls": 0,
        "status": "passed",
    }
    report["content_sha256"] = hashlib.sha256(canonical(report)).hexdigest()
    if args.write:
        target = ROOT / "holdout-audit.json"
        if target.exists():
            if checked(target) != report:
                raise SystemExit("REFUSING: holdout audit drift")
        else:
            target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

