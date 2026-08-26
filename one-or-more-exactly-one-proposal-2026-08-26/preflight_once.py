#!/usr/bin/env python3
"""Run and freeze the authoritative non-writing proposal preflight once."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402


def main() -> None:
    target = ROOT / "preflight.json"
    if target.exists():
        raise SystemExit("REFUSING: preflight already frozen")
    draft = json.loads((ROOT / "draft.json").read_text(encoding="utf-8"))
    receipt = ainglish_client().preflight(draft)
    target.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: receipt.get(key) for key in (
        "valid", "filing_allowed", "ratification_gate_clear", "gates", "warnings",
    )}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
