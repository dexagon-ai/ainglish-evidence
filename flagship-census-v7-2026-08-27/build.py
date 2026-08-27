#!/usr/bin/env python3
"""Build a non-collapsing readiness ledger from the frozen live flagship snapshot."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CHECKS = ("five_second_contrast", "familiar_ambiguity", "symmetric_forms", "visible_payoff", "clean_seam")
# Explicit editorial judgements retained from v5: whole/part has a list-completeness seam and
# repeat/restore needs asymmetric syntax. These are not empirical human-comprehension results.
EDITORIAL_FAILS = {14: {"clean_seam"}, 17: {"symmetric_forms"}}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def verify(value: dict) -> None:
    sealed = dict(value)
    expected = sealed.pop("content_sha256")
    actual = hashlib.sha256(canonical(sealed)).hexdigest()
    if actual != expected:
        raise SystemExit(f"REFUSING: snapshot digest drift: {actual} != {expected}")


def publication_lane(rank: int, project: dict, score: int) -> str:
    qualification = project["flagship_qualification"]["state"]
    editorial_state = project["road_to_register"]["lane"]
    if project["stage"] == "ratified" and qualification == "qualified" and score == 5:
        return "flagship-qualified"
    if rank <= 4 and project["stage"] == "ratified" and score == 5:
        return "site-leading-with-comprehension-guard"
    if project["stage"] == "ratified" and qualification == "candidate_instrument_review":
        return "ratified-instrument-review"
    if project["stage"] == "ratified":
        return "ratified-gallery-with-evidence-guard"
    if editorial_state == "testing" and score == 5:
        return "pipeline-priority"
    return "research-hold"


def cell(value: object) -> str:
    if value is None or value == "":
        return "—"
    return str(value).replace("|", "\\|").replace("\n", " ")


def main() -> None:
    snapshot = json.loads((ROOT / "snapshot.json").read_text(encoding="utf-8"))
    verify(snapshot)
    if len(snapshot["entries"]) != snapshot["selection"]["entry_count"]:
        raise SystemExit("REFUSING: catalog count disagrees with its selection receipt")
    suggestion_by_slug = {}
    for item in snapshot["work_surface"]["suggestions"]:
        suggestion_by_slug.setdefault(item.get("slug"), []).append({
            key: item.get(key) for key in (
                "tier", "stage", "why", "replicates_hash", "confirmation_capable",
                "executable_now", "action",
            )
        })

    rows = []
    for entry in snapshot["entries"]:
        editorial, project = entry["editorial"], entry["project"]
        rank = editorial["rank"]
        checks = {name: name not in EDITORIAL_FAILS.get(rank, set()) for name in CHECKS}
        score = sum(checks.values())
        evidence = project["evidence_readiness"]
        qualification = project["flagship_qualification"]
        adoption = project["adoption"]
        road = project["road_to_register"]
        row = {
            "rank": rank,
            "slug": entry["pinned_slug"],
            "public_id": project["public_id"],
            "form": project["form"],
            "problem": editorial["problem"],
            "safe_caption": editorial["safe_caption"],
            "before": editorial["before"],
            "after": editorial["after"],
            "consequence": editorial["consequence"],
            "claim_guard": editorial["do_not_say"],
            "surface_current": entry["surface"]["current"] and not entry["surface"]["review_required"],
            "editorial_checks": checks,
            "editorial_score": score,
            "editorial_basis": "site-builder judgement; no large human-validation campaign claimed",
            "stage": project["stage"],
            "ratified_version": project.get("ratified_version"),
            "verdict_assessment": (project.get("verdict") or {}).get("assessment"),
            "evidence_contract_declared": evidence["declared"],
            "evidence_ready": evidence["evidence_ready"],
            "missing_evidence": evidence["missing_evidence"],
            "opposing_evidence": evidence["opposing_evidence"],
            "qualification_state": qualification["state"],
            "qualification_label": qualification["label"],
            "instrument_gaps": qualification["instrument_gaps"],
            "adoption_status": adoption["status"],
            "recent_usage": adoption["recent_usage"],
            "adoption_coverage": adoption["methodology"]["coverage"]["status"],
            "road_lane": road["lane"],
            "next_action": road["next_action"],
            "next_metric": road["next_metric"],
            "work_state": road["work_state"],
            "personalized_actions": suggestion_by_slug.get(entry["pinned_slug"], []),
            "publication_lane": publication_lane(rank, project, score),
        }
        rows.append(row)

    lanes = Counter(row["publication_lane"] for row in rows)
    ledger = {
        "kind": "dexagon.ainglish.flagship-readiness-ledger.v7",
        "captured_at": snapshot["captured_at"],
        "source_snapshot_sha256": snapshot["content_sha256"],
        "catalog_content_sha256": snapshot["catalog_content_sha256"],
        "editorial_checks": list(CHECKS),
        "rows": rows,
        "summary": {
            "entries": len(rows),
            "surface_current": sum(row["surface_current"] for row in rows),
            "ratified": sum(row["stage"] == "ratified" for row in rows),
            "pipeline": sum(row["stage"] != "ratified" for row in rows),
            "editorial_5_of_5": sum(row["editorial_score"] == 5 for row in rows),
            "strictly_qualified": sum(row["qualification_state"] == "qualified" for row in rows),
            "lanes": dict(sorted(lanes.items())),
        },
        "claim_boundary": snapshot["selection"]["human_validation"],
        "model_calls": 0,
        "model_downloads": 0,
        "governance_writes": 0,
    }
    ledger["content_sha256"] = hashlib.sha256(canonical(ledger)).hexdigest()
    (ROOT / "ledger.json").write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Flagship candidate census v7",
        "",
        f"Frozen at `{ledger['captured_at']}`. Ledger digest: `{ledger['content_sha256']}`.",
        "",
        f"All **{ledger['summary']['surface_current']}/{len(rows)}** editorial surfaces are current. "
        f"There are **{ledger['summary']['ratified']} ratified** and **{ledger['summary']['pipeline']} pipeline** candidates; "
        f"**{ledger['summary']['strictly_qualified']}** currently clear the strict modern comprehension rubric.",
        "",
        "The five editorial checks are inexpensive site-builder judgements, not a human study. They answer whether the contrast can be shown clearly; the qualification receipt separately answers whether modern comprehension evidence supports an empirical claim.",
        "",
        "| Rank | Construct | Editorial | Stage | Qualification | Adoption | Exact next action | Publication lane |",
        "|---:|---|---:|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['rank']} | `{cell(row['form'])}` | {row['editorial_score']}/5 | "
            f"{cell(row['stage'])} | {cell(row['qualification_label'])} | {cell(row['adoption_status'])} | "
            f"{cell(row['next_action'])} | {cell(row['publication_lane'])} |"
        )
    lines.extend([
        "",
        "## Immediate evidence order",
        "",
        "1. Preserve the four leading ratified contrasts as guarded semantic examples; do not call them comprehension-proven.",
        "2. Prefer live personalized replication cards for pipeline candidates: they add an independent settlement voice rather than another author-owned original.",
        "3. Run new original comprehension carriers only when the proposal explicitly lacks that carrier and the frozen reader/instrument gates pass.",
        "4. Keep adverse, inconclusive, and cross-model-divergent rows visible; they are quality findings, not material to average away.",
        "5. Rebuild this ledger after any supersession, measurement, ratification, evidence moderation, or adoption-coverage change.",
        "",
        "No model was called or downloaded to build this census.",
    ])
    (ROOT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(ledger["summary"], indent=2))


if __name__ == "__main__":
    main()
