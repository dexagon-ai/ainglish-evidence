#!/usr/bin/env python3
"""Build a 17-row editorial/evidence/publication matrix from the frozen dossier."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DOSSIER = ROOT.parent / "flagship-qualification-dossier-v2-2026-08-27" / "dossier.json"
CHECKS = ("five_second_contrast", "familiar_ambiguity", "symmetric_forms", "visible_payoff", "clean_seam")

# These are explicit site-editor judgements, not survey results. Rank 14 overlaps list completeness;
# rank 17 has asymmetric syntax because restore-state requires a projected state argument.
FAILS = {14: {"clean_seam"}, 17: {"symmetric_forms"}}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def lane(row: dict, score: int) -> str:
    if row["rank"] <= 4 and row["stage"] == "ratified":
        return "site-leading-guarded"
    if row["qualification_state"] == "candidate_instrument_review":
        return "ratified-evidence-review"
    if row["stage"] == "ratified":
        return "ratified-gallery-guarded"
    if row["rank"] in {12, 13, 14} or score < 5:
        return "research-hold"
    return "pipeline-preview"


def main() -> None:
    dossier = json.loads(DOSSIER.read_text(encoding="utf-8"))
    rows = []
    for source in dossier["rows"]:
        checks = {check: check not in FAILS.get(source["rank"], set()) for check in CHECKS}
        score = sum(checks.values())
        rows.append({
            "rank": source["rank"], "slug": source["slug"], "public_id": source["public_id"],
            "form": source["form"], "stage": source["stage"], "surface_current": source["surface_current"],
            "editorial_checks": checks, "editorial_score": score,
            "editorial_basis": "site-builder judgement; no large human-validation campaign claimed",
            "qualification_state": source["qualification_state"],
            "modern_carrier_frozen": source["modern_carrier_frozen"],
            "adoption_coverage_status": source["adoption"]["coverage_status"],
            "publication_lane": lane(source, score),
            "safe_caption": source["public_claim"], "claim_guard": source["claim_guard"],
        })
    matrix = {
        "kind": "dexagon.ainglish.flagship-quality-matrix.v5",
        "captured_at": dossier["captured_at"], "source_dossier_sha256": dossier["content_sha256"],
        "checks": list(CHECKS), "rows": rows,
        "summary": {
            "rows": len(rows), "editorial_5_of_5": sum(row["editorial_score"] == 5 for row in rows),
            "site_leading_guarded": sum(row["publication_lane"] == "site-leading-guarded" for row in rows),
            "modern_carriers_frozen": sum(row["modern_carrier_frozen"] for row in rows),
            "modern_qualified": sum(row["qualification_state"] == "qualified" for row in rows),
        },
        "claim_boundary": "A five-second editorial score does not establish comprehension; only the modern evidence rubric can do that.",
        "model_calls": 0, "governance_writes": 0,
    }
    matrix["content_sha256"] = hashlib.sha256(canonical(matrix)).hexdigest()
    (ROOT / "matrix.json").write_text(json.dumps(matrix, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(matrix["summary"], indent=2))


if __name__ == "__main__":
    main()
