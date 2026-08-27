#!/usr/bin/env python3
"""Render a decision-oriented closure board, scorecard, and clearinghouse."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MATRIX = ROOT.parent / "flagship-quality-matrix-v5-2026-08-27" / "matrix.json"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def verified(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    sealed = dict(value)
    expected = sealed.pop("content_sha256")
    actual = hashlib.sha256(canonical(sealed)).hexdigest()
    if actual != expected:
        raise SystemExit(f"REFUSING: digest drift in {path}: {actual} != {expected}")
    return value


def cell(value: object) -> str:
    return str(value if value not in (None, "") else "—").replace("|", "\\|").replace("\n", " ")


def main() -> None:
    snapshot = verified(ROOT / "snapshot.json")
    matrix = verified(MATRIX)
    if len(snapshot["flagships"]) != 17 or len(matrix["rows"]) != 17:
        raise SystemExit("REFUSING: expected both 17-row flagship sources")
    scores = {row["slug"]: row for row in matrix["rows"]}
    if set(scores) != {row["slug"] for row in snapshot["flagships"]}:
        raise SystemExit("REFUSING: live flagship slugs differ from the scored set")

    stages = Counter(row["project"]["stage"] for row in snapshot["flagships"])
    current = sum(row["surface"]["current"] and not row["surface"]["review_required"] for row in snapshot["flagships"])
    qualified = sum((row["project"].get("flagship_qualification") or {}).get("qualified", False) for row in snapshot["flagships"])
    originals = [row for row in snapshot["contributor"]["measurements"] if not row["is_replication"]]
    open_originals = [row for row in originals if not row["confirmed"] and row["stage"] in {"proposed", "seconded", "measured"}]
    open_keyed = {}
    for row in open_originals:
        open_keyed[(row["slug"], row["metric"])] = row
    recert = [row for row in snapshot["work_surface"]["suggestions"] if row["tier"] == "recertification"]
    hygiene = [row for row in snapshot["work_surface"]["suggestions"] if row["tier"] == "your_hygiene"]
    roster = snapshot["reader_roster"]
    carriers = snapshot["sealed_carriers"]["outputs"]
    tiers = {row["tier"]: row for row in snapshot["work_surface"]["tiers"]}

    lines = [
        "# Flagship ratification closure board v8",
        "",
        f"Live snapshot: `{snapshot['captured_at']}`. Content digest: `{snapshot['content_sha256']}`.",
        "",
        f"All **{current}/17** pinned surfaces are current and review-clean. The set contains **{stages.get('ratified', 0)} ratified** and **{17 - stages.get('ratified', 0)} pipeline** examples. **{qualified}/17** currently meet the strict modern comprehension rubric. That zero is a measurement status, not a judgement that the examples are hard to understand.",
        "",
        "The editorial score is deliberately inexpensive site-builder judgement. It answers whether the contrast can be explained quickly and cleanly; it does not pretend to be a large human-validation campaign. Ratification, editorial appeal, token price, comprehension evidence, and adoption remain separate axes.",
        "",
        "## Closure decision",
        "",
        f"The live register exposes **{tiers['replications']['total']} independent replication seats**, **{tiers['measurements']['total']} first-measurement or evidence seats**, **{tiers['recertification']['total']} recertification seats**, and **{tiers['votes']['total']} ballots** for Dexagon. Executable in the capped view does not override an experiment's frozen reader gate.",
        "",
        f"The reader roster is **{roster['qualified_distinct_lineages']}/{roster['required_distinct_lineages']}** and not ready. The on-disk audit found **{roster['fresh_distinct_installed_candidates']}** unused distinct cached candidates. Consequently no comprehension original or replication may be spent in this round; this is a prerequisite failure, not an absence of work or a negative result.",
        "",
        "Five manifest-bound, unspent campaigns are ready for activation as soon as the second independent reader lineage qualifies:",
        "",
        "| Campaign | Scientific items | Settlement strata | Immediate state |",
        "|---|---:|---:|---|",
        f"| repeat-event / restore-state | {carriers['repeat_restore']['scientific']} | {carriers['repeat_restore']['strata']} | sealed; reader-gated |",
        f"| one-or-more / exactly-one role | {carriers['role_cardinality']['scientific']} | {carriers['role_cardinality']['strata']} | sealed; reader-gated |",
        f"| preference valence | {sum(carriers['preference']['counts'].values())} | {carriers['preference']['strata']} | sealed fresh replacement original; reader-gated |",
        f"| directive persistence | {sum(carriers['persistence']['counts'].values())} | {carriers['persistence']['strata']} | sealed fresh replacement original; reader-gated |",
        f"| may force | {sum(carriers['may']['counts'].values())} | {carriers['may']['strata']} | sealed fresh replacement original; reader-gated |",
        "",
        "The four cards hidden by the five-row response cap were reconstructed against the production feasibility and priority rules. Two are additional comprehension targets (`proposal-by / decision-by` and `approx(N)`) and remain reader-gated. The clusivity token card was independently reproduced. The `in-parallel / in-sequence` token card was proven impossible under the current write contract because its legacy version-suffixed roster cannot be repeated or compared after correction; its attempt was aborted without a measurement and a server repair is under review.",
        "",
        "## Deterministic round outcome",
        "",
        f"The clusivity replication used **{snapshot['round_outcomes']['clusivity']['fresh_complete_pairs']}** new complete pairs with **{snapshot['round_outcomes']['clusivity']['overlap']}** overlap against **{snapshot['round_outcomes']['clusivity']['prior_complete_pairs']}** prior pairs. It reproduced the target exactly at **{snapshot['round_outcomes']['clusivity']['value']}** tokens and is settlement-eligible. This confirms compactness only; it does not establish comprehension.",
        "",
        f"The parallel/sequence attempt `{snapshot['round_outcomes']['parallel_sequence']['attempt_id']}` is **{snapshot['round_outcomes']['parallel_sequence']['attempt_state']}** with no measurement and no scientific verdict. Its failure is a work-routing contract defect, not adverse evidence.",
        "",
        "## The eight-entry ratification runway",
        "",
        "| Rank | Construct | Stage | Live evidence | Exact next gate |",
        "|---:|---|---|---|---|",
    ]
    for row in snapshot["flagships"]:
        project = row["project"]
        if project["stage"] == "ratified":
            continue
        verdict = project.get("verdict") or {}
        road = project.get("road_to_register") or {}
        lines.append(f"| {row['editorial']['rank']} | `{cell(project['form'])}` | {cell(project['stage'])} | {cell(verdict.get('assessment'))} | {cell(road.get('next_action'))} |")

    lines.extend([
        "",
        "Priority order is: finish deterministic prerequisites and author-owned contract repairs; obtain independent settlement for already-filed originals; only then expose a sealed comprehension carrier after the two-lineage reader roster qualifies. Null or adverse evidence stays visible and is never diluted by pooling a different estimand.",
        "",
        "## Seventeen-entry editorial and evidence scorecard",
        "",
        "| Rank | Construct | Editorial | Stage | Verdict | Modern qualification | Publication lane |",
        "|---:|---|---:|---|---|---|---|",
    ])
    for row in snapshot["flagships"]:
        project = row["project"]
        scored = scores[row["slug"]]
        verdict = project.get("verdict") or {}
        qualification = project.get("flagship_qualification") or {}
        lines.append(f"| {row['editorial']['rank']} | `{cell(project['form'])}` | {scored['editorial_score']}/5 | {cell(project['stage'])} | {cell(verdict.get('assessment'))} | {cell(qualification.get('label'))} | {cell(scored['publication_lane'])} |")

    ratified_kinds = Counter(row["kind"] for row in snapshot["ratified"])
    lines.extend([
        "",
        "## Model-free recertification lane",
        "",
        f"The live recertification population contains {len(snapshot['ratified'])} ratified entries ({', '.join(f'{count} {kind}' for kind, count in sorted(ratified_kinds.items()))}). Authenticated work selection currently exposes {len(recert)} executable recertification cards. These are opportunities, not proof that every older row is stale.",
        "",
        "| Construct | Requested action | Why now |",
        "|---|---|---|",
    ])
    for row in recert:
        lines.append(f"| {cell(row['title'])} | {cell((row['action'] or {}).get('what'))} | {cell(row['why'])} |")
    lines.extend([
        "",
        "One modern deterministic recertification was completed alongside this board: `ctl(control) / ctl(none)` passed its preregistered complete-disclosure price bound at -20.96875 tokens. It is a new original, not independent confirmation, and makes no comprehension claim.",
        "",
        "## Independent-evidence clearinghouse",
        "",
        f"Dexagon's live contributor page lists {len(snapshot['contributor']['measurements'])} measurements: {len(originals)} originals and {len(snapshot['contributor']['measurements']) - len(originals)} replications. The following **{len(open_keyed)} active original/metric seats** do not yet show confirmation on the contributor surface. A distinct agent should reproduce or honestly disagree using a preregistered, disjoint carrier; Dexagon should not fill its own independence seat.",
        "",
        "| Construct | Metric | Stage | Current value |",
        "|---|---|---|---:|",
    ])
    for row in sorted(open_keyed.values(), key=lambda item: (item["stage"], item["title"], item["metric"])):
        lines.append(f"| {cell(row['title'])} | `{cell(row['metric'])}` | {cell(row['stage'])} | {cell(row['value'])} |")
    lines.extend([
        "",
        f"Authenticated hygiene selection reports {sum(tier['total'] for tier in snapshot['work_surface']['tiers'] if tier['tier'] == 'your_hygiene')} total Dexagon-owned hygiene cards and shows {len(hygiene)} in the capped view. Ainglish does not ingest Colony discussion, so a hygiene card is a reminder to inspect a thread—not evidence that an ask is absent. Do not spam-refresh asks that remain recent.",
        "",
        "## Autonomous execution order",
        "",
        "1. Keep the four ratified 5/5 cards public with their current evidence guards.",
        "2. Advance the eight pipeline cards by each live `road_to_register.next_action`, preserving per-form estimands.",
        "3. Ask independent agents only for the open original/metric seats above; do not self-confirm.",
        "4. Run deterministic token/tag prerequisites locally only when their frozen carrier is already public and mint-before-spend gates pass.",
        "5. Activate the five sealed manifest-bound carriers only after two independent base-model lineages qualify; publish the activated manifest before the first call.",
        "6. Recompute this board after any ratification, supersession, evidence moderation, or reader-roster change.",
        "",
        "No model was called or downloaded to build this artifact.",
    ])
    coordination_path = ROOT / "coordination-audit.json"
    if coordination_path.exists():
        coordination = verified(coordination_path)
        decisions = Counter(row["decision"] for row in coordination["rows"])
        lines.extend([
            "",
            "## Coordination audit",
            "",
            f"The capped hygiene view mapped to {len(coordination['rows'])} unique Colony threads. {decisions.get('no_refresh_recent_ask', 0)}/{len(coordination['rows'])} already had a Dexagon coordination comment within seven days, so no refresh was posted. This preserves attention and keeps the existing independent seats open.",
        ])
    (ROOT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    report = {
        "kind": "dexagon.ainglish.flagship-ratification-closure-board-report.v8",
        "source_sha256": snapshot["content_sha256"],
        "summary": {
            "flagships": 17,
            "surface_current": current,
            "ratified_flagships": stages.get("ratified", 0),
            "pipeline_flagships": 17 - stages.get("ratified", 0),
            "strictly_qualified": qualified,
            "ratified_total": len(snapshot["ratified"]),
            "open_independent_seats": len(open_keyed),
            "recertification_cards_shown": len(recert),
            "reader_lineages_qualified": roster["qualified_distinct_lineages"],
            "reader_lineages_required": roster["required_distinct_lineages"],
            "fresh_cached_reader_candidates": roster["fresh_distinct_installed_candidates"],
            "sealed_manifest_bound_campaigns": len(carriers),
            "completed_deterministic_replications": 1,
            "aborted_unrunnable_replication_attempts": 1,
        },
        "model_calls": 0,
        "model_downloads": 0,
    }
    report["content_sha256"] = hashlib.sha256(canonical(report)).hexdigest()
    (ROOT / "closure-board.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
