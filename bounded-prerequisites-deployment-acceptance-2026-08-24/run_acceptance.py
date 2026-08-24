#!/usr/bin/env python3
"""Non-mutating live acceptance matrix for bounded evidence prerequisites."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import urllib.request

from ainglish.client import AinglishClient, AinglishError


SLUG = "some-or-all-some-but-not-all-does-some-leave-room-for-all-2"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    client = AinglishClient()
    proposal = client.proposal(SLUG)
    base = {
        key: proposal[key]
        for key in client.AMENDMENT_FIELDS
        if proposal.get(key) is not None
    }
    base["title"] = "Deployment acceptance probe only — " + base["title"]

    cases = [
        ("legacy_string", ["token_delta"], True),
        ("bounded_at_most", [{"metric": "token_delta", "at_most": 4}], True),
        ("bounded_at_least", [{"metric": "learnability", "at_least": 0.5}], True),
        ("both_bounds", [{"metric": "token_delta", "at_most": 4, "at_least": -4}], False),
        ("missing_bound", [{"metric": "token_delta"}], False),
        ("boolean_bound", [{"metric": "token_delta", "at_most": True}], False),
        ("unknown_key", [{"metric": "token_delta", "at_most": 4, "unit": "tokens"}], False),
        ("duplicate_across_roles", [{"metric": "comprehension_accuracy_delta", "at_least": 0}], False),
    ]
    results = []
    for name, prerequisites, expected in cases:
        draft = dict(base)
        draft["evidence_contract"] = {
            "claim_carrier": ["comprehension_accuracy_delta"],
            "prerequisites": prerequisites,
        }
        try:
            response = client.preflight(draft)
            actual = bool(response.get("valid") and response.get("filing_allowed"))
            detail = {"valid": response.get("valid"), "filing_allowed": response.get("filing_allowed")}
        except AinglishError as error:
            actual = False
            detail = {"status": error.status, "message": str(error)}
        results.append({"case": name, "expected_accepted": expected, "accepted": actual, "pass": actual == expected, **detail})

    bounded_claim = dict(base)
    bounded_claim["evidence_contract"] = {
        "claim_carrier": [{"metric": "comprehension_accuracy_delta", "at_least": 0}],
        "prerequisites": [],
    }
    try:
        response = client.preflight(bounded_claim)
        actual = bool(response.get("valid") and response.get("filing_allowed"))
        detail = {"valid": response.get("valid"), "filing_allowed": response.get("filing_allowed")}
    except AinglishError as error:
        actual = False
        detail = {"status": error.status, "message": str(error)}
    results.append({"case": "bounded_claim_carrier", "expected_accepted": False, "accepted": actual, "pass": not actual, **detail})

    with urllib.request.urlopen("https://ainglish.org/openapi.json", timeout=30) as response:
        spec = json.load(response)
    contract = spec["components"]["schemas"]["NewProposal"]["properties"]["evidence_contract"]["properties"]
    openapi = {
        "claim_carrier_declares_object": "oneOf" in contract["claim_carrier"]["items"],
        "prerequisites_declares_object": "oneOf" in contract["prerequisites"]["items"],
    }
    openapi["matches_runtime_roles"] = not openapi["claim_carrier_declares_object"] and openapi["prerequisites_declares_object"]

    receipt = {
        "schema": "ainglish-bounded-prerequisite-deployment-acceptance/v1",
        "checked_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "base_url": "https://ainglish.org",
        "non_mutating": True,
        "cases": results,
        "runtime_matrix_pass": all(row["pass"] for row in results),
        "openapi": openapi,
        "overall_pass": all(row["pass"] for row in results) and openapi["matches_runtime_roles"],
    }
    encoded = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded)
    print(encoded, end="")
    return int(not receipt["overall_pass"])


if __name__ == "__main__":
    raise SystemExit(main())
