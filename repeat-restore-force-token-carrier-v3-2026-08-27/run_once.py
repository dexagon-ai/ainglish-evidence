#!/usr/bin/env python3
"""Run v2's reviewed one-shot harness against the v3 packet and source path."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "repeat-restore-force-token-carrier-v2-2026-08-26" / "run_once.py"
spec = importlib.util.spec_from_file_location("repeat_restore_v2_runner", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load reviewed repeat/restore runner")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
runner.ROOT = ROOT
runner.REPO = ROOT.parent


if __name__ == "__main__":
    runner.main()

