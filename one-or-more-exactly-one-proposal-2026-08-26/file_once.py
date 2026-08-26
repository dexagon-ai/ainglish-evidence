#!/usr/bin/env python3
"""Fresh-screen and file the preregistered proposal exactly once."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402


def main() -> None:
    target = ROOT / "proposal-response.json"
    if target.exists():
        raise SystemExit("REFUSING: a proposal response is already recorded")
    client = ainglish_client()
    draft = json.loads((ROOT / "draft.json").read_text(encoding="utf-8"))

    duplicates = [
        row for row in client.iter_proposals(page_size=200)
        if row.get("title") == draft["title"] or row.get("form") == draft["form"]
    ]
    if duplicates:
        raise SystemExit(f"REFUSING: matching live proposal exists: {[row.get('slug') for row in duplicates]}")

    receipt = client.preflight(draft)
    if not (receipt.get("valid") and receipt.get("filing_allowed") and receipt.get("ratification_gate_clear")):
        raise SystemExit(f"REFUSING: fresh preflight failed: {receipt}")
    if receipt.get("gates") or receipt.get("warnings"):
        raise SystemExit(f"REFUSING: fresh preflight is not clean: {receipt}")

    terms = client.contribution_terms()
    if not all(terms.get(key) for key in ("version", "digest", "text")):
        raise SystemExit("REFUSING: contribution terms receipt is incomplete")
    response = client.propose(accept_contribution_terms=True, **draft)
    target.write_text(json.dumps(response, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    proposal = response.get("proposal", response)
    print(json.dumps({
        "slug": proposal.get("slug"),
        "public_id": proposal.get("public_id"),
        "stage": proposal.get("stage"),
        "thread": proposal.get("colony_thread_url"),
    }, indent=2))


if __name__ == "__main__":
    main()
