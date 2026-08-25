#!/usr/bin/env python3
"""Publish the first ready v6 roster, or the final no-roster handoff."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RESULTS = ("phase-a-result.json", "reserve-b-result.json", "final-reserve-result.json")


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    sealed = dict(value)
    expected = sealed.pop("content_sha256")
    if hashlib.sha256(canonical(sealed)).hexdigest() != expected:
        raise SystemExit(f"REFUSING: digest drift in {path.name}")
    return value


def main() -> None:
    target = ROOT / "selected-result.json"
    if target.exists():
        raise SystemExit("REFUSING: selected-result.json already exists")
    plan = checked(ROOT / "plan.json")
    paths = []
    for name in RESULTS:
        path = ROOT / name
        if path.exists():
            paths.append(path)
        else:
            break
    if not paths:
        raise SystemExit("REFUSING: phase A has not completed")
    results = [checked(path) for path in paths]
    fixed = results[-1]["accumulated_fixed_roster"]
    ready = len({reader["lineage"] for reader in fixed}) >= plan["selection_rule"]["minimum_distinct_qualified_lineages"]
    if not ready and paths[-1].name != "final-reserve-result.json":
        raise SystemExit("REFUSING: roster is not ready and declared reserve tranches remain unspent")
    qualification = {}
    for result in results:
        if result["plan_sha256"] != plan["content_sha256"]:
            raise SystemExit("REFUSING: result belongs to another plan")
        overlap = set(qualification) & set(result["qualification"])
        if overlap:
            raise SystemExit(f"REFUSING: repeated readers across tranches: {sorted(overlap)}")
        qualification.update(result["qualification"])
    selected = {
        "kind": "ainglish.panel.reader-qualification-selected-result.v6",
        "evidentiary_status": plan["evidentiary_status"],
        "plan_sha256": plan["content_sha256"],
        "source_results": [
            {"file": path.name, "content_sha256": result["content_sha256"]}
            for path, result in zip(paths, results)
        ],
        "qualification": qualification,
        "roster_ready": ready,
        "fixed_roster": fixed,
        "selection_rule": plan["selection_rule"],
    }
    selected["content_sha256"] = hashlib.sha256(canonical(selected)).hexdigest()
    with target.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(selected, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({
        "roster_ready": ready,
        "fixed_roster": [row["name"] for row in fixed],
        "source_results": [path.name for path in paths],
        "sha256": selected["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
