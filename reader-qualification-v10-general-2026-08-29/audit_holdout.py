#!/usr/bin/env python3
"""Audit the general-scope holdout without making model or network calls."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
WORKTREES = REPO.parent / "worktrees"


def canonical(value: dict) -> bytes:
    material = copy.deepcopy(value)
    material.pop("content_sha256", None)
    return json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if hashlib.sha256(canonical(value)).hexdigest() != value.get("content_sha256"):
        raise SystemExit(f"REFUSING: digest drift: {path}")
    return value


def prior_pairs() -> tuple[set[tuple[str, str]], int]:
    pairs: set[tuple[str, str]] = set()
    files = 0
    roots = [REPO]
    if WORKTREES.exists():
        # Qualification drafts are relevant; duplicated web/corpus worktrees are
        # not and can contain gigabytes of the same generated training shard.
        roots.extend(path for path in WORKTREES.glob("reader-qualification*") if path.is_dir())
    for scan_root in roots:
        for path in scan_root.rglob("*.json"):
            if ROOT == path.parent or ROOT in path.parents:
                continue
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                continue
            files += 1
            stack = [value]
            while stack:
                current = stack.pop()
                if isinstance(current, dict):
                    if isinstance(current.get("premise"), str) and isinstance(current.get("hypothesis"), str):
                        pairs.add((current["premise"], current["hypothesis"]))
                    stack.extend(current.values())
                elif isinstance(current, list):
                    stack.extend(current)
    return pairs, files


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    packet = checked(ROOT / "holdout.json")
    rows = packet["items"]
    if len(rows) != 64 or len({row["id"] for row in rows}) != 64:
        raise SystemExit("REFUSING: holdout population drift")
    groups = {axis: [row for row in rows if row["axis"] == axis] for axis in packet["axes"]}
    if len(groups) != 8 or any(len(group) != 8 for group in groups.values()):
        raise SystemExit("REFUSING: axis balance drift")
    if any(sorted(row["options"]) != sorted(packet["labels"]) or row["answer"] not in row["options"] for row in rows):
        raise SystemExit("REFUSING: answer/options drift")
    positions = [0, 0, 0]
    for row in rows:
        positions[row["options"].index(row["answer"])] += 1
    if positions != [22, 21, 21] or positions != packet["answer_positions"]:
        raise SystemExit("REFUSING: answer-position drift")
    forbidden = ("ainglish", "we-including-you", "this-once", "by-construction", "same-one", "moved-earlier", "it(<ref>)", "none-of")
    leaks = [row["id"] for row in rows if any(term in (row["premise"] + " " + row["hypothesis"]).lower() for term in forbidden)]
    if leaks:
        raise SystemExit(f"REFUSING: target-language leakage: {leaks}")
    prior, files = prior_pairs()
    overlaps = [row["id"] for row in rows if (row["premise"], row["hypothesis"]) in prior]
    if overlaps:
        raise SystemExit(f"REFUSING: prior exact premise/hypothesis overlap: {overlaps}")
    plans = [checked(ROOT / "holdout-qwen-plan.json"), checked(ROOT / "holdout-seed-plan.json")]
    if any(plan["semantic_stage"]["packet"]["content_sha256"] != packet["content_sha256"] for plan in plans):
        raise SystemExit("REFUSING: plan/holdout binding drift")
    lineages = {plan["candidate"]["details"]["family"] for plan in plans}
    if lineages != {"qwen35moe", "seed_oss"}:
        raise SystemExit("REFUSING: lineage independence drift")
    report = {
        "kind": "ainglish.panel.reader-qualification-holdout-audit.v8",
        "instance": packet["instance"],
        "holdout_sha256": packet["content_sha256"],
        "items": len(rows),
        "axes": {axis: len(group) for axis, group in groups.items()},
        "labels": {label: sum(row["answer"] == label for row in rows) for label in packet["labels"]},
        "answer_positions": positions,
        "prior_json_files_scanned": files,
        "prior_exact_pair_overlap": 0,
        "target_construct_terms": 0,
        "candidate_families": sorted(lineages),
        "scope_boundary": "general Ainglish comprehension carriers only; not eligible for restricted this-once replication work",
        "model_calls": 0,
        "network_calls": 0,
        "status": "passed",
    }
    report["content_sha256"] = hashlib.sha256(canonical(report)).hexdigest()
    target = ROOT / "holdout-audit.json"
    if args.write:
        rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        if target.exists() and target.read_text(encoding="utf-8") != rendered:
            raise SystemExit("REFUSING: frozen audit drift")
        if not target.exists():
            target.write_text(rendered, encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
