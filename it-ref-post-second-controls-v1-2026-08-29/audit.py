#!/usr/bin/env python3
"""Audit the full-surface detector and fail-closed carrier disposition."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    contract = json.loads((ROOT / "controls.json").read_text(encoding="utf-8"))
    unsigned = dict(contract)
    expected = unsigned.pop("content_sha256", None)
    if hashlib.sha256(canonical(unsigned)).hexdigest() != expected:
        raise SystemExit("REFUSING: controls digest drift")
    review = contract["carrier_review"]
    if review["disposition"] != "frozen_not_activation_ready" or review["activation_blocker"]["code"] != "INVALID_REFERENCE_CONTROLS_ABSENT":
        raise SystemExit("REFUSING: carrier activation boundary drift")
    detector = contract["adoption_detector"]
    pattern = re.compile(detector["candidate_pattern"])
    positive = {value: pattern.findall(value) for value in detector["positive_candidates"]}
    negative = {value: pattern.findall(value) for value in detector["negative_candidates"]}
    mention = {value: pattern.findall(value) for value in detector["mention_only_candidates"]}
    if any(len(hits) != 1 or not hits[0] for hits in positive.values()):
        raise SystemExit(f"REFUSING: a complete delimited use was missed: {positive}")
    if any(hits for hits in negative.values()):
        raise SystemExit(f"REFUSING: a malformed or bare surface matched: {negative}")
    if any(len(hits) != 1 for hits in mention.values()):
        raise SystemExit("REFUSING: mention fixtures must remain regex candidates for semantic filtering")
    bare_stress = " ".join(["it"] * 1000)
    if pattern.search(bare_stress):
        raise SystemExit("REFUSING: bare it entered the adoption candidate population")
    audit = {
        "kind": "dexagon.ainglish.it-ref-post-second-controls-audit.v1",
        "status": "passed",
        "complete_delimited_positive_candidates": len(positive),
        "bare_or_malformed_negative_candidates": len(negative),
        "mention_only_candidates_reserved_for_semantic_filter": len(mention),
        "bare_it_stress_occurrences": 1000,
        "bare_it_candidates": 0,
        "carrier_activation_blocked": True,
        "model_calls": 0,
        "attempts_minted": 0,
        "governance_writes": 0,
    }
    audit["content_sha256"] = hashlib.sha256(canonical(audit)).hexdigest()
    (ROOT / "audit.json").write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
