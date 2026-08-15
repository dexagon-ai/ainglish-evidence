#!/usr/bin/env python3
"""Capture the deterministic zero-reader dry-run transcript."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent


def main() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "ainglish.panel", "run", "runspec-dedicated-gpu0.json", "--dry-run"],
        cwd=ROOT,
        env=dict(os.environ),
        capture_output=True,
        text=True,
        check=False,
    )
    transcript = result.stdout + result.stderr
    (ROOT / "dry-run.txt").write_text(transcript, encoding="utf-8")
    if result.returncode != 0:
        raise SystemExit(result.returncode)
    if "zero API calls" not in transcript or "DRY-RUN" not in transcript:
        raise SystemExit("dry-run transcript lost its non-evidence/zero-call stamp")
    print(transcript, end="")


if __name__ == "__main__":
    main()
