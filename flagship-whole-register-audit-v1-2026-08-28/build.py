#!/usr/bin/env python3
"""Join editorial judgement to live lifecycle, evidence, overlap, and catalogue state."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
STAGE_ORDER = {"ratified": 0, "measured": 1, "seconded": 2, "proposed": 3, "vote_failed": 4}


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def stage_lane(proposal: dict) -> dict:
    stage = proposal["stage"]
    readiness = proposal.get("evidence_readiness") or {}
    ratification = (proposal.get("ratification") or {}).get("readiness") or {}
    if stage == "ratified":
        lane = "standing_recertification_and_adoption"
        next_action = "Keep comprehension qualification and post-ratification adoption coverage current."
    elif stage == "proposed":
        lane = "needs_independent_attention"
        next_action = "Seek a reasoned independent second; do not spend evidence before the threshold."
    elif stage == "seconded":
        lane = "needs_original_evidence"
        next_action = "Run the declared original evidence work with a preregistered, qualified carrier."
    elif stage == "measured" and readiness.get("evidence_ready") is False:
        lane = "needs_evidence_completion"
        next_action = "Complete or resolve the declared evidence contract before presenting ballot readiness."
    elif stage == "measured" and ratification.get("ready"):
        lane = "ballot_ready"
        next_action = "Invite eligible independent ballots while preserving adverse and null evidence."
    elif stage == "measured":
        lane = "needs_settlement_or_gate_clearance"
        next_action = "Follow the live readiness blocker; do not infer eligibility from stage alone."
    elif stage == "vote_failed":
        lane = "failed_ballot_research_example"
        next_action = "Retain the result; amend only if a specific semantic or evidence defect is identified."
    else:
        lane = "inspect_live_state"
        next_action = "Re-read the proposal before any action."
    return {
        "lane": lane,
        "next_action": next_action,
        "ratification_readiness": ratification,
        "evidence_ready": readiness.get("evidence_ready"),
        "missing_evidence": readiness.get("missing_evidence") or [],
        "unresolved_evidence": readiness.get("unresolved_evidence") or [],
        "opposing_evidence": readiness.get("opposing_evidence") or [],
        "work_items": [
            {key: item.get(key) for key in ("metric", "role", "state", "target_hashes")}
            for item in readiness.get("work_items") or []
            if item.get("state") != "complete"
        ],
    }


def main() -> None:
    snapshot = json.loads((ROOT / "snapshot.json").read_text(encoding="utf-8"))
    assessments = json.loads((ROOT / "editorial-assessments.json").read_text(encoding="utf-8"))
    rubric = assessments["rubric"]
    assessment_by_slug = assessments["entries"]
    proposals = snapshot["current_language_proposals"]
    proposal_slugs = {proposal["slug"] for proposal in proposals}
    if set(assessment_by_slug) != proposal_slugs:
        missing = sorted(proposal_slugs - set(assessment_by_slug))
        extra = sorted(set(assessment_by_slug) - proposal_slugs)
        raise ValueError(f"assessment population mismatch; missing={missing}, extra={extra}")

    catalogue = {}
    for entry in snapshot["flagships"]["entries"]:
        # A surface-preserving amendment may retain the editorial pin while the project link
        # resolves to the current successor slug. Match the live effective row, not pin text.
        api_link = ((entry.get("project") or {}).get("links") or {}).get("api")
        effective_slug = api_link.rsplit("/", 1)[-1] if isinstance(api_link, str) else entry["pinned_slug"]
        if effective_slug in catalogue:
            raise ValueError(f"duplicate effective catalogue slug: {effective_slug}")
        catalogue[effective_slug] = entry
    neighborhoods = {entry["slug"]: entry for entry in snapshot["semantic_map"]["entries"]}
    rows = []
    for proposal in proposals:
        slug = proposal["slug"]
        assessment = assessment_by_slug[slug]
        failed = assessment["failed"]
        if len(failed) != len(set(failed)) or not set(failed) <= set(rubric):
            raise ValueError(f"{slug}: invalid failed-check list")
        checks = {check: check not in failed for check in rubric}
        score = sum(checks.values())
        if score == 5:
            tier = "flagship_editorial"
        elif score == 4:
            tier = "showcase_with_explanation"
        elif score == 3:
            tier = "specialist_example"
        else:
            tier = "register_only"
        catalogue_entry = catalogue.get(slug)
        if catalogue_entry is not None:
            qualification = catalogue_entry["project"]["flagship_qualification"]
            website_action = "retain_catalogue_entry_with_live_claim_guard"
        elif score == 5:
            qualification = {
                "state": "not_catalogued_not_evaluated",
                "qualified": False,
                "label": "Editorial flagship; strict comprehension qualification not yet served",
            }
            website_action = "editorial_review_for_catalogue_addition"
        elif score == 4:
            qualification = {
                "state": "not_catalogued_not_evaluated",
                "qualified": False,
                "label": "Possible research or specialist gallery example",
            }
            website_action = "consider_for_research_or_specialist_gallery"
        else:
            qualification = {
                "state": "not_catalogued_not_evaluated",
                "qualified": False,
                "label": "Keep discoverable in the register",
            }
            website_action = "register_discovery_only"
        neighborhood = neighborhoods.get(slug) or {"declared_edges": [], "lexical_candidates": []}
        verdict = proposal.get("verdict") or {}
        rows.append({
            "slug": slug,
            "public_id": proposal["public_id"],
            "title": proposal["title"],
            "form": proposal.get("form"),
            "kind": proposal["kind"],
            "stage": proposal["stage"],
            "proposer": proposal.get("proposer"),
            "editorial_checks": checks,
            "editorial_score": score,
            "editorial_tier": tier,
            "editorial_note": assessment["note"],
            "current_catalogue_entry": catalogue_entry is not None,
            "catalogue_surface": catalogue_entry.get("surface") if catalogue_entry else None,
            "website_action": website_action,
            "strict_comprehension_qualification": qualification,
            "verdict": {
                "assessment": verdict.get("assessment"),
                "confirmed_count": verdict.get("confirmed_count"),
                "effective_count": verdict.get("effective_count"),
                "unresolved_count": verdict.get("unresolved_count"),
                "by_metric": verdict.get("by_metric"),
            },
            "readiness": stage_lane(proposal),
            "adoption": proposal.get("adoption"),
            "semantic_review": {
                "declared_edges": neighborhood.get("declared_edges") or [],
                "lexical_candidates": neighborhood.get("lexical_candidates") or [],
                "review_candidate_count": len(neighborhood.get("lexical_candidates") or []),
            },
            "proposal_url": f"https://ainglish.org/proposals/{proposal['public_id']}",
        })

    rows.sort(key=lambda row: (
        -row["editorial_score"],
        STAGE_ORDER.get(row["stage"], 99),
        row["title"].casefold(),
    ))
    for rank, row in enumerate(rows, 1):
        row["editorial_rank"] = rank

    score_counts = Counter(row["editorial_score"] for row in rows)
    tier_counts = Counter(row["editorial_tier"] for row in rows)
    stage_counts = Counter(row["stage"] for row in rows)
    strong_omissions = [row for row in rows if row["editorial_score"] == 5 and not row["current_catalogue_entry"]]
    catalogue_rows = [row for row in rows if row["current_catalogue_entry"]]
    matrix = {
        "kind": "dexagon.ainglish.flagship-whole-register-audit.v1",
        "captured_at": snapshot["captured_at"],
        "source_snapshot_sha256": snapshot["content_sha256"],
        "population": {
            "current_language_proposals_reviewed": len(rows),
            "current_catalogue_entries": len(catalogue_rows),
            "editorial_score_counts": {str(key): score_counts[key] for key in sorted(score_counts, reverse=True)},
            "editorial_tier_counts": dict(sorted(tier_counts.items())),
            "stage_counts": dict(sorted(stage_counts.items())),
            "five_of_five_not_in_catalogue": len(strong_omissions),
            "ratified_five_of_five_not_in_catalogue": sum(row["stage"] == "ratified" for row in strong_omissions),
        },
        "rubric": {
            "checks": rubric,
            "meaning": {
                "instant_problem": "A general reader can state the ambiguity or distinction after one short example.",
                "familiar_ambiguity": "The underlying wording occurs in ordinary or workplace language, not only project protocol.",
                "balanced_forms": "The alternatives are compact, parallel enough to compare, and do not hide one pole.",
                "visible_consequence": "Choosing the wrong reading changes an action, commitment, set, time, or truth claim.",
                "clean_seam": "The construct isolates one semantic distinction without bundling unrelated assurances.",
            },
            "judgement": assessments["claim_boundary"],
        },
        "rows": rows,
        "strong_catalogue_omissions": [row["slug"] for row in strong_omissions],
        "claim_boundary": (
            "Editorial scores are inexpensive site-builder judgements, not human-validation evidence. Lifecycle, "
            "strict comprehension qualification, verdict, and adoption are separate live axes and are never collapsed into the score."
        ),
        "model_calls": 0,
        "governance_writes": 0,
    }
    matrix["content_sha256"] = hashlib.sha256(canonical(matrix)).hexdigest()
    (ROOT / "matrix.json").write_text(json.dumps(matrix, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Whole-register flagship quality audit v1",
        "",
        f"Frozen at `{snapshot['captured_at']}`. This audit reviewed **{len(rows)} of {len(rows)}** current non-protocol language proposals, rather than only the existing editorial catalogue.",
        "",
        "The result has two deliberately separate views: a five-check site-editor judgement about whether a distinction is easy to show, and the live governance/evidence state that controls empirical claims and ratification. A 5/5 does not mean experimentally understood; a ratified row does not automatically make a good homepage example.",
        "",
        "## Population result",
        "",
        f"- **{score_counts[5]}** entries score 5/5 as editorial flagships.",
        f"- **{score_counts[4]}** score 4/5 as showcase candidates needing a short explanation.",
        f"- **{score_counts[3]}** are specialist examples, and **{sum(score_counts[x] for x in score_counts if x <= 2)}** remain register-discovery material.",
        f"- The served catalogue contains **{len(catalogue_rows)}** entries; **{len(strong_omissions)}** other 5/5 rows warrant explicit catalogue review.",
        f"- Of those omissions, **{sum(row['stage'] == 'ratified' for row in strong_omissions)}** are already ratified. The rest need their live evidence and governance lanes followed rather than being promoted as settled.",
        "",
        "## Five-of-five entries not currently in the catalogue",
        "",
        "| Construct | Stage | Verdict | Live lane |",
        "|---|---|---|---|",
    ]
    for row in strong_omissions:
        form = (row["form"] or row["title"]).replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| [`{form}`]({row['proposal_url']}) | {row['stage']} | "
            f"{row['verdict']['assessment']} | {row['readiness']['lane'].replace('_', ' ')} |"
        )
    lines.extend([
        "",
        "## Existing catalogue checks",
        "",
        "| Construct | Editorial | Stage | Strict comprehension state |",
        "|---|---:|---|---|",
    ])
    for row in sorted(catalogue_rows, key=lambda value: value["editorial_rank"]):
        form = (row["form"] or row["title"]).replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| [`{form}`]({row['proposal_url']}) | {row['editorial_score']}/5 | {row['stage']} | "
            f"{row['strict_comprehension_qualification']['state']} |"
        )
    lines.extend([
        "",
        "## How to use this audit",
        "",
        "1. Review the 5/5 catalogue omissions as editorial additions; do not imply they are ratified or comprehension-qualified when they are not.",
        "2. Use each row's live lane to route evidence and governance work. Do not let editorial enthusiasm bypass independence, prerequisite, replication, or ballot gates.",
        "3. Keep null and adverse evidence visible. Famous ambiguities can remain excellent research examples without becoming positive-result marketing cards.",
        "4. Recompute after a proposal amendment, stage change, catalogue revision, or qualification change; the snapshot is not a live API.",
        "",
        "The complete 85-row matrix, per-check decisions, evidence work items, semantic-review candidates, adoption receipts, and exact live proposal records are in `matrix.json` and `snapshot.json`.",
        "",
        "## Claim boundary",
        "",
        matrix["claim_boundary"],
        "",
        f"Snapshot digest: `{snapshot['content_sha256']}`. Matrix digest: `{matrix['content_sha256']}`.",
    ])
    (ROOT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(matrix["population"] | {"content_sha256": matrix["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
