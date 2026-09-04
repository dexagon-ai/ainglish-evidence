#!/usr/bin/env python3
"""Bind the current two-reader qualification receipts to the legacy runner."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
QUAL_ROOT = ROOT.parent / "reader-qualification-local-v1-2026-09-04"
OUTPUT = ROOT / "local-qualified-roster.json"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    fixed_roster = []
    receipts = []
    for stem in ("mistral", "gemma"):
        reader = load(QUAL_ROOT / f"{stem}-screen.json")["reader"]
        receipt = load(QUAL_ROOT / f"{stem}-qualification.json")["receipt"]
        if not receipt["result"]["passed"]:
            raise SystemExit(f"REFUSING: {stem} qualification did not pass")
        if reader["model"] != receipt["reader"]["model"]:
            raise SystemExit(f"REFUSING: {stem} model binding differs")
        if reader["model_digest"] != receipt["reader"]["model_digest"]:
            raise SystemExit(f"REFUSING: {stem} model digest binding differs")
        fixed_roster.append(
            {
                "name": reader["name"],
                "lineage": receipt["lineage"]["key"],
                "model": reader["model"],
                "model_digest": reader["model_digest"],
                "precision": reader["precision"],
                "seed": reader["seed"],
                "timeout_s": reader["timeout_s"],
                "qualification_roster_id": receipt["roster_id"],
                "qualification_valid_until": receipt["valid_until"],
            }
        )
        receipts.append(receipt)
    result = {
        "kind": "dexagon.ainglish.local-qualified-roster-adapter.v1",
        "roster_ready": len({row["lineage"] for row in fixed_roster}) == 2,
        "fixed_roster": fixed_roster,
        "qualification_receipts": receipts,
        "qualification_source": "reader-qualification-local-v1-2026-09-04",
        "evidentiary_limit": "target-independent ordinary-English reader qualification; not target evidence",
    }
    result["content_sha256"] = hashlib.sha256(canonical(result)).hexdigest()
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": OUTPUT.name, "content_sha256": result["content_sha256"]}))


if __name__ == "__main__":
    main()
