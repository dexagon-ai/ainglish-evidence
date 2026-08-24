#!/usr/bin/env python3
"""Run the published v2 development controls once."""

from pathlib import Path

from qualification_common import run


ROOT = Path(__file__).resolve().parent


if __name__ == "__main__":
    run(ROOT / "development.json", ROOT / "development-result.json")
