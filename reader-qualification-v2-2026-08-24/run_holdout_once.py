#!/usr/bin/env python3
"""Run the published v2 qualification holdout exactly once."""

from pathlib import Path

from qualification_common import run


ROOT = Path(__file__).resolve().parent


if __name__ == "__main__":
    run(ROOT / "holdout.json", ROOT / "holdout-result.json")
