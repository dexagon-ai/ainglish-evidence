#!/usr/bin/env python3
"""Run the fresh some-or-all replication once."""

from __future__ import annotations

import json
from pathlib import Path
import sys

from ainglish import panel as panel_harness


ROOT = Path(__file__).resolve().parent
REPOSITORY = ROOT.parent
PROJECT = REPOSITORY.parent
sys.path.insert(0, str(REPOSITORY))
sys.path.insert(0, str(PROJECT / "scripts"))

from evidence_factory import CampaignIndex, CampaignRunner  # noqa: E402
from local_colony_auth import ainglish_client  # noqa: E402


def main() -> None:
    index = CampaignIndex.load(ROOT / "runspec-index.json")
    runner = CampaignRunner(index, client_factory=ainglish_client, ask_fn=panel_harness.ask, expected_sdk_version="0.2.35")
    result = runner.run_entry(index.entries[0], require_suggestion=True)
    (ROOT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
