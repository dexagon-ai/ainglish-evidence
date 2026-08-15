#!/usr/bin/env python3
"""Execute the frozen successor once, after strict GPU and queue preflight."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request

from ainglish import __version__ as sdk_version


ROOT = Path(__file__).resolve().parent
RUNSPEC = ROOT / "runspec-dedicated-gpu0.json"
RUNSPEC_SHA256 = "0e138d04bde0c6cf981438937ac386d458735fe93e74a624e5e602526f2a8be2"
SCRIPTS = ROOT.parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import TOTP_SECRET_PATH, load_api_key  # noqa: E402


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.load(response)


def gpu_preflight() -> dict:
    command = [
        "nvidia-smi",
        "--query-gpu=index,pci.bus_id,name,memory.used,memory.free,utilization.gpu",
        "--format=csv,noheader,nounits",
    ]
    rows = []
    for line in subprocess.run(command, check=True, capture_output=True, text=True).stdout.splitlines():
        index, pci, name, used, free, utilization = [part.strip() for part in line.split(",", 5)]
        rows.append({"index": int(index), "pci_bus_id": pci, "name": name,
                     "memory_used_mib": int(used), "memory_free_mib": int(free),
                     "utilization_percent": int(utilization)})
    selected = next((row for row in rows if row["index"] == 0), None)
    if selected is None or selected["name"] != "NVIDIA GeForce RTX 3090":
        raise SystemExit("REFUSING: frozen GPU 0 identity is unavailable")
    if selected["memory_free_mib"] < 20_000:
        raise SystemExit("REFUSING: GPU 0 has less than 20,000 MiB free")
    for url in ("http://127.0.0.1:11434/api/ps", "http://127.0.0.1:11435/api/ps"):
        if get_json(url).get("models"):
            raise SystemExit(f"REFUSING: Ollama endpoint already has a resident model: {url}")
    return selected


def main() -> None:
    if sdk_version != "0.2.29":
        raise SystemExit(f"REFUSING: SDK {sdk_version} != frozen 0.2.29")
    digest = hashlib.sha256(RUNSPEC.read_bytes()).hexdigest()
    if digest != RUNSPEC_SHA256:
        raise SystemExit(f"REFUSING: runspec drifted: {digest}")
    existing = list(ROOT.glob("runspec-dedicated-gpu0.json.attempt-*.json"))
    if existing:
        raise SystemExit("REFUSING: an attempt receipt already exists; do not rerun in place")
    selected = gpu_preflight()
    print("GPU PREFLIGHT:", json.dumps(selected, sort_keys=True), flush=True)

    env = dict(os.environ)
    env["COLONY_API_KEY"] = load_api_key()
    env["AINGLISH_TOTP_SECRET_FILE"] = str(TOTP_SECRET_PATH)
    env.pop("AINGLISH_ID_TOKEN", None)
    result = subprocess.run(
        [sys.executable, "-m", "ainglish.panel", "run", RUNSPEC.name, "--submit"],
        cwd=ROOT,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
