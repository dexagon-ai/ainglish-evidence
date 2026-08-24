#!/usr/bin/env python3
"""Run the one frozen v3 development-stage configuration revision."""

from pathlib import Path

from qualification_common import run


ROOT = Path(__file__).resolve().parent


if __name__ == "__main__":
    run(ROOT / "development-tuned.json", ROOT / "development-tuned-result.json")
