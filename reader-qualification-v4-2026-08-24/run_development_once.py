#!/usr/bin/env python3
"""Run the frozen v4 development controls exactly once."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "reader-qualification-v3-2026-08-24"))
from qualification_common import run  # noqa: E402


if __name__ == "__main__":
    run(ROOT / "development.json", ROOT / "development-result.json")
