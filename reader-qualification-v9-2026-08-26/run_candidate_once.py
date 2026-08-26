#!/usr/bin/env python3
"""Run the generic one-shot candidate runner with the v9 package as root."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
GENERIC = ROOT.parent / "reader-fresh-lineage-v1-2026-08-26"
sys.path.insert(0, str(GENERIC))
spec = importlib.util.spec_from_file_location("generic_candidate_runner", GENERIC / "run_candidate_once.py")
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
module.ROOT = ROOT
module.REPO = ROOT.parent
module.main()
