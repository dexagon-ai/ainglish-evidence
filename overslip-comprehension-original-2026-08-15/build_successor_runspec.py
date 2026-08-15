#!/usr/bin/env python3
"""Build attempt 1's scientifically identical, operationally isolated successor."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PREDECESSOR_ATTEMPT = "1c9069c7-e100-46f9-8dea-0a3e5f90b1b6"
DEDICATED_BASE_URL = "http://127.0.0.1:11435/v1"


def main():
    spec = json.loads((ROOT / "runspec.json").read_text(encoding="utf-8"))
    for reader in spec["panel"]:
        reader["api"] = "openai"
        reader["base_url"] = DEDICATED_BASE_URL

    attempt = spec["attempt"]
    attempt["estimand"] = (
        f"Operational successor to aborted attempt {PREDECESSOR_ATTEMPT}; the frozen items, "
        "seed, readers, bounds, estimand and interpretation rules are unchanged. The only "
        "manifest change is routing both named readers to a dedicated local CPU-only endpoint "
        "so an unrelated shared-model queue cannot censor calibration or real cells. "
        + attempt["estimand"]
    )
    attempt["admissibility_gates"].append(
        "both readers execute on the dedicated loopback endpoint at 127.0.0.1:11435; any "
        "transport fault, calibration loss or real-cell yield failure remains a typed abort"
    )
    attempt["planned_sample"]["execution"] = (
        "dedicated local CPU-only Ollama endpoint; no concurrent model-serving clients"
    )

    (ROOT / "runspec-dedicated-cpu.json").write_text(
        json.dumps(spec, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
