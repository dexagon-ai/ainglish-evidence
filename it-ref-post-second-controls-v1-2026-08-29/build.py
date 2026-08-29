#!/usr/bin/env python3
"""Build the prospective adoption detector and post-second carrier review."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
V1 = REPO / "new-language-comprehension-carriers-v1-2026-08-29"
PATTERN = r"(?<![A-Za-z0-9_-])it\(([A-Za-z0-9][A-Za-z0-9_.:@/-]{0,127})\)(?![A-Za-z0-9_-])"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def checked(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    unsigned = dict(value)
    expected = unsigned.pop("content_sha256", None)
    if hashlib.sha256(canonical(unsigned)).hexdigest() != expected:
        raise SystemExit(f"REFUSING: digest drift at {path}")
    return value


def seal(value: dict) -> dict:
    value["content_sha256"] = hashlib.sha256(canonical(value)).hexdigest()
    return value


def main() -> None:
    snapshot = checked(ROOT / "proposal-snapshot.json")
    zero = checked(V1 / "pronoun-zero-shot.json")
    conditioned = checked(V1 / "pronoun-definition-conditioned.json")
    if snapshot["proposal"]["stage"] != "seconded" or snapshot["measurement_count"] != 0:
        raise SystemExit("REFUSING: snapshot does not preserve the prospective seconded boundary")
    if any(row.get("invalid_reference_case") for packet in (zero, conditioned) for row in packet["scientific_rows"]):
        raise SystemExit("REFUSING: v1 unexpectedly contains invalid-reference controls")
    contract = seal({
        "kind": "dexagon.ainglish.it-ref-post-second-controls.v1",
        "proposal_snapshot_sha256": snapshot["content_sha256"],
        "proposal_slug": "it-ref",
        "proposal_public_id": snapshot["proposal"]["public_id"],
        "carrier_review": {
            "source_packets": [
                {"condition": zero["condition"], "content_sha256": zero["content_sha256"], "scientific_rows": 160},
                {"condition": conditioned["condition"], "content_sha256": conditioned["content_sha256"], "scientific_rows": 160},
            ],
            "confirmed_strengths": [
                "both antecedent positions are balanced 80/80 in each condition",
                "marked, bare, and complete noun-repetition arms remain separate",
                "marked versus complete noun repetition is a load-bearing non-inferiority gate",
                "current token cost is descriptive and cannot override comprehension harm",
            ],
            "activation_blocker": {
                "code": "INVALID_REFERENCE_CONTROLS_ABSENT",
                "detail": "Every v1 scientific row supplies two valid uniquely named antecedents; it cannot test missing, future, plural, person, multiply resolving, corrupted, or unpinned-document references promised by the filing.",
                "required_repair": "Keep v1 immutable. Before minting, publish a digest-bound supplement or explicit v2 that gates invalid/unresolved classification and includes a valid uniquely resolved control; no pooled score may override that gate.",
            },
            "disposition": "frozen_not_activation_ready",
        },
        "adoption_detector": {
            "status": "prospective_pre_ratification",
            "candidate_pattern": PATTERN,
            "candidate_capture": "group 1 is the complete locally delimited reference token",
            "never_match": ["bare it", "it with an empty reference", "spaced it (ref)", "its(ref)", "sit(ref)", "unterminated it(ref"],
            "mention_vs_use": "A regex hit is only a candidate. Count it only when the complete it(ref) form performs antecedent binding in running prose. Exclude code, quotations, examples, proposal/register discussion, and the proposer's own uses.",
            "claim_boundary": "Candidate detection does not establish valid reference resolution, adoption, comprehension, or ratification.",
            "positive_candidates": [
                "The service notified the agent after it(service) failed.",
                "The robot moved the crate because it(crate) blocked the door.",
                "Archive it(bundle-7) after verification.",
                "The probe saw the node when it(node_2) restarted.",
            ],
            "negative_candidates": [
                "It failed after the alert.",
                "The service said it was unavailable.",
                "The token it() is incomplete.",
                "The token it (service) has a space.",
                "The field its(service) is possessive.",
                "The helper sit(service) is unrelated.",
                "The malformed token it(service never closes.",
            ],
            "mention_only_candidates": [
                "The proposal calls the marker it(service).",
                "Example: it(agent) means the agent.",
                "The code string is 'it(crate)'.",
            ],
        },
        "training_asymmetry": "Present-reader zero-shot results measure current transparency for models generally trained on English rather than this Ainglish form; one-card learnability and future pretrained behavior remain separate.",
        "model_calls": 0,
        "attempts_minted": 0,
        "governance_writes": 0,
    })
    (ROOT / "controls.json").write_text(
        json.dumps(contract, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "disposition": contract["carrier_review"]["disposition"],
        "pattern": contract["adoption_detector"]["candidate_pattern"],
        "content_sha256": contract["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
