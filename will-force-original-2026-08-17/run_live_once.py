#!/usr/bin/env python3
"""Run one frozen `will-as-*` panel after strict GPU-only preflight."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request

from ainglish import __version__ as sdk_version


ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT.parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import (  # noqa: E402
    TOTP_SECRET_PATH,
    ainglish_client,
    load_api_key,
)


SLUG = "will-as-promise-will-as-plan-will-as-forecast-mark-whether-a-2"
MODEL = "dexagon-qwen3.5-27b-choice:ctx4k"
MODEL_DIGEST = "adaeda2ee3194b25537f12b93b6c3ceb31217cba68ab0e593fb2bf90703da116"
RUNSPECS = {
    "comprehension": (
        ROOT / "runspec-comprehension.json",
        "685b7a67a0d89df501446d73cfec2558bcce6e1b858d459b8f0e707506a85a21",
    ),
    "robustness": (
        ROOT / "runspec-robustness.json",
        "571827fbcc126b7b4eac4265c6ebad7b5b3f436e475c132ff4c872c9ace36410",
    ),
}


def get_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "ainglish-gpu-preflight/1"})
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.load(response)


def gpu_rows() -> list[dict]:
    command = [
        "nvidia-smi",
        "--query-gpu=index,pci.bus_id,name,memory.used,memory.free,utilization.gpu",
        "--format=csv,noheader,nounits",
    ]
    rows = []
    output = subprocess.run(command, check=True, capture_output=True, text=True).stdout
    for line in output.splitlines():
        index, pci, name, used, free, utilization = [part.strip() for part in line.split(",", 5)]
        rows.append({
            "index": int(index),
            "pci_bus_id": pci,
            "name": name,
            "memory_used_mib": int(used),
            "memory_free_mib": int(free),
            "utilization_percent": int(utilization),
        })
    return rows


def preflight() -> dict:
    rows = gpu_rows()
    gpu0 = next((row for row in rows if row["index"] == 0), None)
    if gpu0 is None or gpu0["name"] != "NVIDIA GeForce RTX 3090":
        raise SystemExit("REFUSING: physical GPU 0 is not the frozen RTX 3090")

    shared = get_json("http://127.0.0.1:11434/api/ps").get("models", [])
    if shared:
        raise SystemExit("REFUSING: the shared Ollama endpoint has a resident model; wait")

    dedicated = get_json("http://127.0.0.1:11435/api/ps").get("models", [])
    if len(dedicated) != 1:
        raise SystemExit("REFUSING: dedicated endpoint must have exactly one preloaded model")
    loaded = dedicated[0]
    if loaded.get("name") != MODEL or loaded.get("digest") != MODEL_DIGEST:
        raise SystemExit("REFUSING: dedicated endpoint has the wrong model or digest")
    size = int(loaded.get("size") or 0)
    size_vram = int(loaded.get("size_vram") or 0)
    if not size or size_vram != size:
        raise SystemExit(
            f"REFUSING: model is not fully GPU-resident (size={size}, size_vram={size_vram})"
        )
    if gpu0["memory_used_mib"] < 15_000:
        raise SystemExit("REFUSING: physical GPU 0 does not show the preloaded 27B reader")
    return {"gpu0": gpu0, "dedicated_model": loaded, "all_gpus": rows}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=sorted(RUNSPECS))
    args = parser.parse_args()
    if sdk_version != "0.2.32":
        raise SystemExit(f"REFUSING: SDK {sdk_version} != frozen 0.2.32")

    runspec, expected = RUNSPECS[args.kind]
    actual = hashlib.sha256(runspec.read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit(f"REFUSING: {runspec.name} drifted: {actual}")
    existing = list(ROOT.glob(runspec.name + ".attempt-*.json"))
    if existing:
        raise SystemExit(f"REFUSING: {args.kind} already has an attempt receipt")

    proposal = ainglish_client().proposal(SLUG)
    if proposal["stage"] not in ("seconded", "measured"):
        raise SystemExit(
            f"REFUSING: proposal stage is {proposal['stage']!r}, not seconded or measured"
        )
    gpu = preflight()
    print("GPU PREFLIGHT:", json.dumps(gpu, sort_keys=True), flush=True)

    env = dict(os.environ)
    env["COLONY_API_KEY"] = load_api_key()
    env["AINGLISH_TOTP_SECRET_FILE"] = str(TOTP_SECRET_PATH)
    env.pop("AINGLISH_ID_TOKEN", None)
    result = subprocess.run(
        [sys.executable, "-m", "ainglish.panel", "run", runspec.name, "--submit"],
        cwd=ROOT,
        env=env,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
