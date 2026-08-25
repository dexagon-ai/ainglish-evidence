#!/usr/bin/env python3
"""Select a scientific roster from never-repeated qualified phase results."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    target = ROOT / "selected-result.json"
    if target.exists():
        raise SystemExit("REFUSING: selected-result.json already exists")
    paths = [ROOT / "phase-a-result.json", ROOT / "reserve-result.json"]
    if not all(path.exists() for path in paths):
        raise SystemExit("REFUSING: phase A and reserve B results are both required")
    phi = ROOT / "phi-reserve-result.json"
    if phi.exists():
        paths.append(phi)
    results = [json.loads(path.read_text()) for path in paths]
    panel_by_name = {}
    qualifications = {}
    for result in results:
        for reader in result.get("fixed_roster", []):
            if reader["name"] in panel_by_name:
                raise SystemExit("REFUSING: a reader appears in more than one phase")
            panel_by_name[reader["name"]] = reader
        qualifications.update(result.get("qualification", {}))
    fixed = list(panel_by_name.values())
    ready = len({reader["lineage"] for reader in fixed}) >= 2
    selected = {
        "kind": "ainglish.panel.reader-qualification-selected-result.v5",
        "evidentiary_status": "instrument qualification only; never proposal evidence",
        "source_results": [{"file": path.name, "content_sha256": result["content_sha256"]} for path, result in zip(paths, results)],
        "qualification": qualifications, "roster_ready": ready, "fixed_roster": fixed,
        "selection_rule": "at least two distinct lineages that independently cleared 64/64 exact codes, 60/64 total, 7/8 every axis, and zero thinking bytes; no reader repeated",
    }
    selected["content_sha256"] = hashlib.sha256(canonical(selected)).hexdigest()
    target.write_text(json.dumps(selected, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"roster_ready": ready, "fixed_roster": [row["name"] for row in fixed], "sha256": selected["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
