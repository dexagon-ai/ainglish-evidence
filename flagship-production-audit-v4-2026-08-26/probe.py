#!/usr/bin/env python3
"""Read production without writing an audit receipt."""

from __future__ import annotations

import json
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parent))
from capture import inspect  # noqa: E402


if __name__ == "__main__":
    print(json.dumps(inspect(), indent=2, ensure_ascii=False))

