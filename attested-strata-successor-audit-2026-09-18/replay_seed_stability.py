"""Run the inspected source packet four times without modifying that packet."""
import json
import os
from pathlib import Path
import subprocess
import sys


if __name__ == "__main__":
    packet, output = map(Path, sys.argv[1:3])
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    for seed in range(4):
        result = subprocess.run(
            [sys.executable, "-B", str(packet / "reference.py"), "--raw", str(packet / "raw"),
             "--out", str(output / f"reference-seed-{seed}.json")],
            env={**os.environ, "PYTHONHASHSEED": str(seed)},
            text=True, capture_output=True, timeout=360, check=True,
        )
        lines = result.stdout.splitlines()
        row = {"seed": seed, "exit_code": result.returncode,
               "outcomes_digest_line": lines[-2], "all_match_line": lines[-1]}
        print(row, flush=True)
        rows.append(row)
    (output / "seed-stability.json").write_text(json.dumps(rows, indent=2) + "\n")
