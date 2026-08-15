#!/usr/bin/env python3
"""Build the scientifically identical, resource-bounded GPU successor."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PREDECESSOR_ATTEMPTS = (
    "1c9069c7-e100-46f9-8dea-0a3e5f90b1b6",
    "878cd707-87ab-440e-93c7-82b71e05c553",
)
DEDICATED_BASE_URL = "http://127.0.0.1:11435/v1"


def main():
    spec = json.loads((ROOT / "runspec.json").read_text(encoding="utf-8"))
    for reader in spec["panel"]:
        reader["api"] = "openai"
        reader["base_url"] = DEDICATED_BASE_URL

    attempt = spec["attempt"]
    attempt["estimand"] = (
        "Operational successor to aborted attempts "
        f"{PREDECESSOR_ATTEMPTS[0]} and {PREDECESSOR_ATTEMPTS[1]}; the frozen items, seed, "
        "readers, bounds, estimand and interpretation rules are unchanged. The only manifest "
        "change is execution on a dedicated local RTX 3090 endpoint pinned to GPU 0, with one "
        "loaded model and one request permitted at a time. This replaces the CPU-only topology "
        "that was followed by an abrupt host restart. "
        + attempt["estimand"]
    )
    attempt["admissibility_gates"].extend(
        [
            "both readers execute on the dedicated loopback endpoint at 127.0.0.1:11435, "
            "pinned with CUDA_VISIBLE_DEVICES=0, OLLAMA_MAX_LOADED_MODELS=1 and "
            "OLLAMA_NUM_PARALLEL=1; CPU fallback is prohibited",
            "immediately before minting, GPU 0 is an RTX 3090 with at least 20 GiB free VRAM, "
            "the shared Ollama server reports no loaded model, and nvidia-smi reports no compute "
            "process; a competing workload or GPU-health fault causes a typed abort",
            "any transport fault, calibration loss or real-cell yield failure remains a typed "
            "abort",
        ]
    )
    attempt["planned_sample"]["execution"] = (
        "dedicated local RTX 3090 GPU 0; CUDA_VISIBLE_DEVICES=0; one loaded model; one request "
        "at a time; no CPU fallback; wait rather than run if the GPU is contested"
    )

    (ROOT / "runspec-dedicated-gpu0.json").write_text(
        json.dumps(spec, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
