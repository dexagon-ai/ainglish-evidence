#!/usr/bin/env python3
"""Fresh-read, mint, execute and settle the one-shot replication."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
PROJECT = REPO.parent
SDK = PROJECT / "worktrees" / "sdk-release-0.2.52-F6xAFh" / "src"
sys.path.insert(0, str(SDK))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(PROJECT / "scripts"))

from ainglish import panel as panel_harness  # noqa: E402
from evidence_factory import CampaignIndex, CampaignRunner  # noqa: E402
from local_colony_auth import ainglish_client  # noqa: E402


def main() -> None:
    index = CampaignIndex.load(ROOT / "runspec-index.json")
    runner = CampaignRunner(
        index,
        client_factory=ainglish_client,
        ask_fn=panel_harness.ask,
        expected_sdk_version="0.2.52",
    )
    entry = index.entries[0]
    if runner.settled_receipts(entry):
        raise SystemExit("REFUSING: this one-shot campaign already has a settlement receipt")
    try:
        result = runner.run_entry(entry, require_suggestion=True)
    finally:
        spec = json.loads(entry.spec_path.read_text(encoding="utf-8"))
        for warning in runner.unload_declared_models(spec):
            print(f"UNLOAD WARNING: {warning}")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
