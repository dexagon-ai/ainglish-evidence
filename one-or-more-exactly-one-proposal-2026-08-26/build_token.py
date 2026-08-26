#!/usr/bin/env python3
"""Build the proposal's balanced 32-pair deterministic price prerequisite."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent

ONE_OR_MORE = [
    ("reviewer", "reviewers", "approve the release"),
    ("auditor", "auditors", "verify the ledger"),
    ("maintainer", "maintainers", "sign the migration record"),
    ("witness", "witnesses", "observe the key ceremony"),
    ("operator", "operators", "acknowledge the alert"),
    ("owner", "owners", "accept the handoff"),
    ("moderator", "moderators", "review the report"),
    ("translator", "translators", "check the localized notice"),
    ("tester", "testers", "reproduce the defect"),
    ("approver", "approvers", "authorize the deployment"),
    ("responder", "responders", "confirm the incident status"),
    ("editor", "editors", "proofread the announcement"),
    ("custodian", "custodians", "inventory the sealed media"),
    ("examiner", "examiners", "score the appeal"),
    ("observer", "observers", "record the vote count"),
    ("steward", "stewards", "validate the retention schedule"),
]

EXACTLY_ONE = [
    ("coordinator", "coordinators", "own the incident channel"),
    ("signer", "signers", "execute the final certificate"),
    ("dispatcher", "dispatchers", "assign the recovery team"),
    ("chair", "chairs", "announce the ballot result"),
    ("recorder", "recorders", "maintain the canonical minutes"),
    ("publisher", "publishers", "release the signed bulletin"),
    ("arbiter", "arbiters", "issue the binding interpretation"),
    ("allocator", "allocators", "assign the unique resource"),
    ("controller", "controllers", "hold the production lease"),
    ("facilitator", "facilitators", "lead the hearing"),
    ("nominator", "nominators", "submit the final candidate"),
    ("tallykeeper", "tallykeepers", "certify the final count"),
    ("author", "authors", "own the canonical statement"),
    ("delegate", "delegates", "exercise the proxy vote"),
    ("liaison", "liaisons", "speak for the response team"),
    ("adjudicator", "adjudicators", "decide the final appeal"),
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    rows = []
    for index, (role, plural, action) in enumerate(ONE_OR_MORE, 1):
        rows.append({
            "item_id": f"oom-{index:02d}",
            "form": "one-or-more",
            "ainglish": f"one-or-more({role}): {action}.",
            "english": f"At least one distinct {role} must {action}; additional {plural} are allowed.",
        })
    for index, (role, plural, action) in enumerate(EXACTLY_ONE, 1):
        rows.append({
            "item_id": f"exo-{index:02d}",
            "form": "exactly-one",
            "ainglish": f"exactly-one({role}): {action}.",
            "english": f"Exactly one distinct {role} must {action}; zero or multiple {plural} do not satisfy the requirement.",
        })
    counts = {form: sum(row["form"] == form for row in rows) for form in ("one-or-more", "exactly-one")}
    if len(rows) != 32 or len(set(counts.values())) != 1:
        raise SystemExit("REFUSING: pair count or form balance gate")
    if len({(row["ainglish"], row["english"]) for row in rows}) != 32:
        raise SystemExit("REFUSING: pairs are not unique")
    packet = {
        "kind": "ainglish.one-or-more-exactly-one-token-items.v1",
        "proposal_slug": "one-or-more-role-exactly-one-role-does-a-reviewer-require-at",
        "metric": "token_delta",
        "forms": ["one-or-more", "exactly-one"],
        "form_counts": counts,
        "comparison": "registered marker versus shortest careful English carrying both the lower and upper cardinality bounds",
        "acceptance": {"least_favourable_balanced_mean_at_most": -2},
        "evidentiary_limit": "price prerequisite only; token count is not comprehension evidence",
        "test_set": rows,
    }
    packet["items_sha256"] = hashlib.sha256(canonical(rows)).hexdigest()
    packet["content_sha256"] = hashlib.sha256(canonical(packet)).hexdigest()
    target = ROOT / "token-items.json"
    if target.exists():
        raise SystemExit("REFUSING: token-items.json already exists")
    target.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"pairs": len(rows), "form_counts": counts, "items_sha256": packet["items_sha256"], "content_sha256": packet["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
