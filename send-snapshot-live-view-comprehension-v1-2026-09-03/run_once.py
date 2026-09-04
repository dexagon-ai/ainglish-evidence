#!/usr/bin/env python3
"""Fresh-route gate followed immediately by the one-shot registered panel run."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import ainglish
from ainglish import panel
from ainglish.client import AinglishClient


ROOT = Path(__file__).resolve().parent
RUNSPEC = ROOT / "runspec.json"
RUNSPEC_SHA256 = "1174e212fb4708cdbb6d7cf6da5dbe9f7773bed0f65efe912cc594b5ea2bab72"
SLUG = "send-snapshot-version-ref-to-recipient-grant-live-view"
METRIC = "comprehension_accuracy_delta"


def refuse(message: str) -> None:
    raise SystemExit(f"REFUSING before attempt mint and reader spend: {message}")


def main() -> int:
    if ainglish.__version__ != "0.2.52":
        refuse(f"requires ainglish 0.2.52, got {ainglish.__version__}")
    encoded = RUNSPEC.read_bytes()
    if hashlib.sha256(encoded).hexdigest() != RUNSPEC_SHA256:
        refuse("runspec.json does not match the frozen public handoff")
    spec = json.loads(encoded)
    if spec.get("slug") != SLUG or spec.get("metric") != METRIC:
        refuse("runspec target or metric changed")

    client = AinglishClient()
    identity = client.whoami()
    suggestions = client.suggestions()
    matches = [
        row for row in suggestions.get("suggestions", [])
        if row.get("slug") == SLUG
    ]
    if len(matches) != 1:
        refuse(f"expected exactly one live suggestion for the target, got {len(matches)}")
    work = matches[0].get("evidence_work") or {}
    if (
        matches[0].get("executable_now") is not True
        or matches[0].get("stage") != "measured"
        or work.get("metric") != METRIC
        or work.get("role") != "claim_carrier"
        or work.get("state") != "submit_original"
    ):
        refuse(f"live suggestion no longer requests the declared original: {work!r}")

    proposal = client.proposal(SLUG, authenticated=True)
    contract = proposal.get("evidence_contract") or {}
    if proposal.get("stage") != "measured" or METRIC not in contract.get("claim_carrier", []):
        refuse("fresh proposal read no longer has the measured-stage comprehension carrier")

    print(
        "LIVE PREFLIGHT PASS:",
        identity.get("display_name") or identity.get("sub"),
        "is routed to the still-missing original comprehension carrier.",
    )
    print("Starting the registered one-shot run; do not retry an observed outcome.")
    return panel.main(["ainglish-panel", "run", str(RUNSPEC), "--submit"])


if __name__ == "__main__":
    raise SystemExit(main())
