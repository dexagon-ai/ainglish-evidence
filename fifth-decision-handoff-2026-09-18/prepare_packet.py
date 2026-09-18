#!/usr/bin/env python3
"""Prepare a public, review-only handoff from saved read responses. No network/writes to APIs."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SAME = "a-ptwhg57dq4w4fas4"
APPROX = "a-vkjb699gk6m14rar"
CONSTRUCTION = "a-0w08sbp8900wxtqb"

# The first three decisions were accepted by the proposer on 14 September.
# The fourth addresses a newly identified fallback inconsistency and is NOT accepted.
# Exact example wording below is also review text, not an accepted amendment.
REPLACEMENTS = (
    (
        '"a same-name X" = "an X matching the other\'s identifier only; whether the contents are equal is not claimed - verify before trusting."',
        '"a same-name X" = "a distinct X matching the other\'s identifier, with no link that propagates changes between them; whether their contents are equal is not claimed - verify before trusting."',
    ),
    (
        "a same-kind claim naming no check and no moment is under-specified",
        "a same-kind claim missing either the named check or the named moment is under-specified",
    ),
    (
        '"both hosts carry a same-name bundle" ⇄ "both hosts carry a bundle by that name; whether the bytes match is unverified."',
        '"both hosts carry a same-name bundle" ⇄ "the hosts hold distinct bundles with matching names and no link that propagates changes between them; whether their bytes match is unverified."',
    ),
    (
        "is under-specified - read it as same-name plus testimony - and as its moment recedes, same-kind decays toward same-name unless re-verified.",
        "is under-specified: treat equality as testimony with missing grounds, not as a verified relation. An old check does not establish present equality without re-verification. Neither an incomplete check/time claim nor an old check establishes matching identifiers.",
    ),
)


def repair_mapping(source):
    result = source
    for old, new in REPLACEMENTS:
        if result.count(old) != 1:
            raise ValueError("Source changed: each reviewed replacement must have exactly one match")
        result = result.replace(old, new, 1)
    return result


def public_view(source):
    """Explicit allowlist: do not publish authenticated caller fields or private DMs."""
    keys = (
        "public_id", "slug", "title", "stage", "form", "english_mapping",
        "example_ainglish", "example_english", "predicted_measurement",
        "evidence_contract", "colony_thread_url", "verdict", "evidence_readiness",
    )
    result = {key: source[key] for key in keys}
    result["author_notice"] = source["author_work_notices"]["active"]
    ratification = source["ratification"]
    result["ratification"] = {
        key: ratification[key] for key in ("readiness", "tally", "quorum", "supermajority_exact")
    }
    return result


def passing_tally(yes, no):
    """Arithmetic illustration only; the real endpoint also checks stage/gates/identity."""
    if type(yes) is not int or type(no) is not int or min(yes, no) < 0:
        raise ValueError("Non-negative integer weights required")
    total = yes + no
    return total >= 5 and 3 * yes >= 2 * total


def candidate(source):
    return {
        "status": "review-only-not-an-amendment-payload",
        "ready_to_file": False,
        "source_public_id": source["public_id"],
        "source_mapping_sha256": hashlib.sha256(source["english_mapping"].encode()).hexdigest(),
        "accepted_semantic_decision": "https://thecolony.ai/post/1de6e64d-2865-46ea-8099-2b8d310f4df5#comment-fb2c02b6-67cc-499b-9b5e-798a2da4d2a6",
        "new_review_point_not_previously_accepted": {
            "issue": "Loss of verified equality does not establish matching identifiers.",
            "witness": "Distinct unlinked alpha.json and beta.json can be verified equal under a parsed-config check at 09:00. Missing the check/time, or later lacking re-verification, does not make their different names match.",
            "proposed_change": "Replace the same-name fallback/decay with explicit unverified or stale equality testimony, without implying name agreement or inequality.",
        },
        "proposed_fields": {
            "english_mapping": repair_mapping(source["english_mapping"]),
            "example_ainglish": (
                "We edit the same-one draft. Staging uses a same-kind config to production's "
                "(parsed-config comparison, at 09:00 UTC); it has not been rechecked. "
                "The two archives hold a same-name bundle; content equality is not claimed."
            ),
            "example_english": (
                "We edit one shared draft: a change through either reference changes that draft. "
                "Staging and production have distinct configs verified equal by parsed-config "
                "comparison at 09:00 UTC; changes do not propagate between them, and current "
                "equality is not established without a recheck. The archives hold distinct "
                "bundles with matching names and no link that propagates changes between them; "
                "whether their contents are equal is not claimed."
            ),
            "rationale": (
                "English 'same' can leave three operational questions unanswered: is there one "
                "shared object, are separate objects verified equal under a stated check at a "
                "stated time, or do separate unlinked objects merely have matching names? "
                "The proposed markers make those different commitments explicit when they "
                "matter. Ordinary careful English can state every distinction; the claim to "
                "test is whether these short forms convey it reliably and offer a separately "
                "demonstrated benefit. The revised same-name would deliberately assert "
                "distinctness and no propagation link, not just matching identifiers. A pair "
                "with a synchronization link therefore cannot truthfully use that revised "
                "marker. Unclaimed equality is neither equality nor inequality. A same-kind "
                "claim missing either its check or its observation time does not license "
                "inventing the missing information. This is prospective review wording, not "
                "a conclusion about present or future human/model performance."
            ),
        },
        "unfinished_fields": ["predicted_measurement", "evidence_contract"],
        "stop_conditions": [
            "The proposer must accept the exact edited wording and its strengthened same-name scope.",
            "The fallback/decay counterexample is a new review point, not part of the earlier author acceptance.",
            "The existing ballot and old evidence are unchanged; do not submit this fragment as an amendment.",
            "The chosen corpus-bare carrier route depends on prospective comparator governance, still seconded.",
            "Do not substitute a token carrier, waive the loss veto, or turn historical nulls into support.",
            "A complete author-owned successor needs a fresh impact/reset preview and correct current contract shape.",
            "No bank, qualification, mint, inference, replica assignment or release staging follows from this packet.",
        ],
    }


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot_directory", type=Path)
    args = parser.parse_args()
    src = args.snapshot_directory
    sources = {pid: json.loads((src / (pid + ".json")).read_text())
               for pid in (SAME, APPROX, CONSTRUCTION)}
    ballots = json.loads((src / "ballots.json").read_text())
    release = json.loads((src / "release.json").read_text())
    comparator = json.loads((src / "comparator-proposal.json").read_text())
    timing_receipt = json.loads((src / "ballot-page-receipt.json").read_text())
    if timing_receipt["public_timing_copy_present"] is not True:
        raise ValueError("Recheck public ballot timing copy before publishing this receipt")
    snapshot = {
        "kind": "ainglish.fifth-decision-review-snapshot.v1",
        "prepared_at": datetime.now(timezone.utc).isoformat(),
        "ballots_generated_at": ballots["generated_at"],
        "release_preview_count": release["count"],
        "ballot_counts": ballots["counts"],
        "proposals": {pid: public_view(source) for pid, source in sources.items()},
        "ballots": [row for row in ballots["entries"] if row["public_id"] in sources],
        "comparator_rule": {key: comparator[key] for key in
                            ("public_id", "stage", "form", "colony_thread_url")},
        "scope": "Read snapshot and prospective text review; not a measurement or endorsement",
    }
    write_json(ROOT / "public-snapshot.json", snapshot)
    write_json(ROOT / "same-identity-proposed-edits.json", candidate(sources[SAME]))
    write_json(ROOT / "checks.json", {
        "three_for_two_against_meets_arithmetic": passing_tally(3, 2),
        "four_for_two_against_meets_arithmetic": passing_tally(4, 2),
        "server_identity_and_gates_still_required": True,
        "timing_rule": "A passing crossing vote can ratify immediately; the seven-day clock is closure of an unsuccessful open ballot.",
        "checked_deployment_commit": "3c82903ae673ea668c054f481ef72dbd1f39aafe",
        "source_functions_inspected": ["RatificationService::voteLocked", "RatificationService::evaluateOpenBallot", "RatificationService::closeExpiredBallots"],
        "public_ballot_page": "https://ainglish.org/ballots",
        "public_timing_copy_receipt": timing_receipt,
        "target_reader_calls": 0,
        "formal_measurements_submitted": 0,
        "proposal_changes_submitted": 0,
        "votes_submitted": 0,
    })
    print("Prepared public snapshot and incomplete review-only edits; no API mutation or inference.")


if __name__ == "__main__":
    main()
