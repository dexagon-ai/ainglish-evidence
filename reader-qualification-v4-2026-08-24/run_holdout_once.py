#!/usr/bin/env python3
"""Run the untouched native no-thinking v4 holdout exactly once."""

from pathlib import Path

from qualification_native import run


ROOT = Path(__file__).resolve().parent


if __name__ == "__main__":
    run(ROOT / "holdout.json", ROOT / "holdout-result.json")
