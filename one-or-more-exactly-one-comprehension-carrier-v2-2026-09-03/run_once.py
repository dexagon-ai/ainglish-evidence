#!/usr/bin/env python3
"""Run every unsettled role-cardinality campaign once, with fresh live checks."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
PROJECT = REPO.parent
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
        expected_sdk_version="0.2.51",
    )
    results = []
    for entry in index.entries:
        settled = runner.settled_receipts(entry)
        if settled:
            results.append({"campaign": entry.name, "state": "already_settled_local", "receipt": settled[0].name})
            continue
        try:
            # Personalized suggestions are a rotating shortlist, not the exhaustive work
            # contract. CampaignRunner still refreshes both suggestions and the authenticated
            # proposal immediately before every mint; the proposal's explicit missing-evidence
            # work item is the authority when this preselected campaign rotates off the shortlist.
            results.append(runner.run_entry(entry, require_suggestion=False))
        finally:
            spec = json.loads(entry.spec_path.read_text(encoding="utf-8"))
            for warning in runner.unload_declared_models(spec):
                print(f"UNLOAD WARNING: {warning}")
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
