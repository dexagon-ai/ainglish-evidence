#!/usr/bin/env python3
"""Run the frozen reference-loaded campaigns once through evidence_factory."""

from __future__ import annotations

import argparse
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign", help="run one named pending campaign")
    args = parser.parse_args()
    index = CampaignIndex.load(ROOT / "runspec-index.json")
    runner = CampaignRunner(
        index,
        client_factory=ainglish_client,
        ask_fn=panel_harness.ask,
        expected_sdk_version="0.2.35",
    )
    if args.campaign:
        matches = [entry for entry in index.entries if entry.name == args.campaign]
        if len(matches) != 1:
            raise SystemExit(f"unknown campaign {args.campaign!r}")
        results = [runner.run_entry(matches[0], require_suggestion=False)]
    else:
        results = runner.run_all(require_suggestion=False)
    payload = {
        "kind": "ainglish.flagship-reference-loaded-results.v1",
        "runspec_index": index.content_digest,
        "results": results,
    }
    (ROOT / "results.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
