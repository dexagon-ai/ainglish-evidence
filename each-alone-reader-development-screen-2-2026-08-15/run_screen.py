#!/usr/bin/env python3
"""Run screen 2 using the already-frozen development-screen runner."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RUNNER = ROOT.parent / "each-alone-reader-development-screen-2026-08-15" / "run_screen.py"

module_spec = importlib.util.spec_from_file_location("reader_development_screen_runner", RUNNER)
if module_spec is None or module_spec.loader is None:
    raise SystemExit("REFUSING: unable to load frozen screen runner")
runner = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(runner)
runner.ROOT = ROOT
runner.SPEC_PATH = ROOT / "screen-spec.json"
runner.RESULT_PATH = ROOT / "screen-results.json"
runner.main()
