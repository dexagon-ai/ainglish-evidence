#!/usr/bin/env python3
"""Fail closed if the review-only atlas acquires an asserted semantic edge."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LABELS = {
    "duplicate",
    "successor_or_refinement",
    "complementary_same_axis",
    "possible_conflict",
    "orthogonal_shared_vocabulary",
    "insufficient",
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def verify_digest(document: dict, label: str) -> str:
    sealed = dict(document)
    expected = sealed.pop("content_sha256", None)
    actual = hashlib.sha256(canonical(sealed)).hexdigest()
    if expected != actual:
        raise SystemExit(f"REFUSING: {label} digest mismatch ({actual} != {expected})")
    return expected


def main() -> None:
    candidates = json.loads((ROOT / "candidates.json").read_text(encoding="utf-8"))
    readings = json.loads((ROOT / "classifier-results.json").read_text(encoding="utf-8"))
    atlas = json.loads((ROOT / "atlas.json").read_text(encoding="utf-8"))
    candidate_digest = verify_digest(candidates, "candidates")
    reading_digest = verify_digest(readings, "classifier results")
    atlas_digest = verify_digest(atlas, "atlas")
    if readings.get("candidate_packet_sha256") != candidate_digest:
        raise SystemExit("REFUSING: classifier packet pin mismatch")
    if atlas.get("candidate_packet_sha256") != candidate_digest or atlas.get("classifier_results_sha256") != reading_digest:
        raise SystemExit("REFUSING: atlas input pin mismatch")
    expected_ids = [row["pair_id"] for row in candidates["candidates"]]
    reading_ids = [row["pair_id"] for row in readings["results"]]
    atlas_ids = [row["pair_id"] for row in atlas["rows"]]
    if len(expected_ids) != len(set(expected_ids)) or reading_ids != expected_ids or atlas_ids != expected_ids:
        raise SystemExit("REFUSING: pair population/order mismatch")
    for layer, rows in (("candidate", candidates["candidates"]), ("classifier", readings["results"]), ("atlas", atlas["rows"])):
        for row in rows:
            if row.get("review_required") is not True or row.get("asserted_relation") is not None:
                raise SystemExit(f"REFUSING: {layer} row {row['pair_id']} asserts an unreviewed edge")
    for row in readings["results"]:
        if row.get("agreed_label") is not None and row["agreed_label"] not in LABELS:
            raise SystemExit(f"REFUSING: unknown agreed label in {row['pair_id']}")
        for reading in row["readings"]:
            if reading.get("status") == "ok" and reading.get("label") not in LABELS:
                raise SystemExit(f"REFUSING: unknown classifier label in {row['pair_id']}")
    print(json.dumps({"pairs": len(expected_ids), "candidate_sha256": candidate_digest, "classifier_sha256": reading_digest, "atlas_sha256": atlas_digest, "all_review_required": True, "asserted_relations": 0}, indent=2))


if __name__ == "__main__":
    main()
