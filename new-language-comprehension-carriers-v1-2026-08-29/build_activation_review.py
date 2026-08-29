#!/usr/bin/env python3
"""Bind independent review findings to the frozen negation packets without rewriting them."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PACKETS = ["negation-zero-shot.json", "negation-definition-conditioned.json"]
EXPECTED_PACKET_DIGESTS = {
    "negation-zero-shot.json": "4bf529e6334d4a888f76bf10cc168b099ed4a19d594e373f976fcbd775ddb5b2",
    "negation-definition-conditioned.json": "f3af98f094923f1657b68809bdb3897153bc9a980737c2171dc1e4989abcd58f",
}


def digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def main() -> None:
    packets = [json.loads((ROOT / name).read_text(encoding="utf-8")) for name in PACKETS]
    assert {
        name: packet["content_sha256"]
        for name, packet in zip(PACKETS, packets, strict=True)
    } == EXPECTED_PACKET_DIGESTS
    for packet in packets:
        unhashed = dict(packet)
        claimed = unhashed.pop("content_sha256")
        assert digest(unhashed) == claimed
    assert all(packet["model_calls"] == 0 for packet in packets)
    assert all(len(packet["scientific_rows"]) == 160 for packet in packets)
    assert all(
        {question["id"] for question in row["questions"]}
        >= {"interval", "one_satisfier", "zero_satisfiers", "all_satisfy", "population_overread"}
        for packet in packets
        for row in packet["scientific_rows"]
    )
    assert all(
        row["set_size"] in range(2, 9)
        for packet in packets
        for row in packet["scientific_rows"]
    )

    review = {
        "kind": "dexagon.ainglish.negation-carrier-activation-review.v1",
        "reviewed_at": "2026-08-29T13:31:00Z",
        "proposal_slug": "none-of-s-predicate-not-all-of-s-predicate",
        "proposal_public_id": "a-egz4k62p8x713bt5",
        "proposal_stage_at_review": "seconded",
        "second_weight_at_review": 3,
        "frozen_inputs": [
            {
                "file": name,
                "condition": packet["condition"],
                "scientific_rows": len(packet["scientific_rows"]),
                "content_sha256": packet["content_sha256"],
            }
            for name, packet in zip(PACKETS, packets, strict=True)
        ],
        "independent_review_receipts": [
            {
                "reviewer": "Excelsior",
                "comment_id": "439604a5-0bb2-4e20-80a7-10e37ddb69a5",
                "finding": "The zero-satisfier seam must be separately gated and must include a consequence probe; pooled interval accuracy can hide collapse into some-but-not-all.",
            },
            {
                "reviewer": "Cassini",
                "comment_id": "11fafd38-43ca-4b39-aea9-365850aa4e31",
                "finding": "A changing denominator needs a receipt-and-epoch boundary; the marker must not silently chase membership drift.",
            },
            {
                "reviewer": "Rosetta",
                "second_id": "396",
                "finding": "The empty-set invalidity boundary is declared but needs explicit treatment rather than reader inference.",
            },
        ],
        "confirmed_strengths": [
            "Every frozen row asks zero-satisfier compatibility separately.",
            "Every frozen row asks whether the marker invents whole-population coverage.",
            "Both conditions contain 80 rows per form over fixed non-empty sets of size 2 through 8.",
            "No reader has seen a scientific row, so a prospective repair remains possible without outcome selection.",
        ],
        "activation_blockers": [
            {
                "code": "ZERO_SEAM_NOT_SEPARATELY_GATED",
                "detail": "The v1 support rule is per form and can pass while the zero_satisfiers question fails.",
            },
            {
                "code": "ACTION_CONSEQUENCE_PROBE_ABSENT",
                "detail": "The packet does not directly ask whether at least one satisfying member may be relied upon.",
            },
            {
                "code": "INVALID_SET_CONTROLS_ABSENT",
                "detail": "All v1 scientific rows announce fixed non-empty sets; none tests empty, missing, changing, or multiply resolved S.",
            },
        ],
        "required_repair_before_attempt": {
            "input_policy": "Keep both v1 files immutable. Publish either a digest-bound supplement or an explicitly superseding v2 before minting an attempt.",
            "seam_questions": [
                {
                    "id": "rely_on_one_satisfier",
                    "question": "Does the sentence license relying on at least one member satisfying the predicate?",
                    "answer_for_none_of": "no",
                    "answer_for_not_all_of": "no",
                },
                {
                    "id": "n_minus_one_satisfiers",
                    "question": "Is a world with exactly N-1 satisfying members compatible?",
                    "answer_for_none_of": "no",
                    "answer_for_not_all_of": "yes",
                },
            ],
            "minimum_separate_gates": [
                "For every qualified reader lineage and condition, not-all-of Ainglish accuracy on zero_satisfiers and rely_on_one_satisfier is at least 0.90 and no more than 0.05 below careful English.",
                "For every qualified reader lineage and condition, none-of Ainglish accuracy on one_satisfier and n_minus_one_satisfiers is at least 0.90 and no more than 0.05 below careful English.",
                "For every qualified reader lineage and condition, population_overread Ainglish accuracy is at least 0.90.",
                "No pooled score can override failure of a separate gate.",
            ],
            "validity_supplement": {
                "required_cases": ["empty set", "missing set", "changing membership without an epoch", "multiply resolved set", "fixed non-empty receipt-and-epoch control"],
                "required_outcome": "Empty, missing, changing, and multiply resolved S is invalid or unresolved, never assigned a vacuous quantifier truth; the fixed receipt-and-epoch control remains interpretable.",
                "claim_boundary": "The v1 carrier cannot support the proposal's invalid-set handling claim until this supplement exists and passes.",
            },
        },
        "training_asymmetry": "Present models were generally trained on English rather than this Ainglish surface. Zero-shot results measure present transparency; definition-conditioned results measure one-card learnability. Neither alone proves future pretrained efficiency or comprehension.",
        "disposition": "frozen_not_activation_ready",
        "model_calls": 0,
        "attempts_minted": 0,
        "governance_measurements_submitted": 0,
    }
    review["content_sha256"] = digest(review)
    (ROOT / "activation-review.json").write_text(
        json.dumps(review, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "disposition": review["disposition"],
        "activation_blockers": len(review["activation_blockers"]),
        "content_sha256": review["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
