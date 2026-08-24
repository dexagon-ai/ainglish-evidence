#!/usr/bin/env python3
"""Run the frozen native no-thinking development revision exactly once."""

from pathlib import Path

from qualification_native import run


ROOT = Path(__file__).resolve().parent


if __name__ == "__main__":
    run(ROOT / "development-tuned.json", ROOT / "development-tuned-result.json")
