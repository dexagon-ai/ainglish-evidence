#!/usr/bin/env python3
"""Build the editorially ranked live flagship-evidence shortlist."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CHECKS = (
    "five_second_contrast",
    "familiar_ambiguity",
    "symmetric_forms",
    "visible_payoff",
    "clean_seam",
)

# This ordering is explicit site-editor judgement. It ranks showcase potential plus
# evidence closure, not predicted experimental outcome. Negative evidence is retained.
CANDIDATES = [
    ("moved-earlier-moved-later-which-way-did-the-meeting-move-2", (),
     "A famous schedule ambiguity with opposite real-world actions; an independent replication is executable now."),
    ("one-or-more-role-exactly-one-role-does-a-reviewer-require-at", (),
     "The hidden at-least-one versus exactly-one reading of 'a reviewer' is immediate and operational."),
    ("same-one-same-kind-same-name-mark-whether-same-claims-one-sh-2", (),
     "A familiar word hides identity, equality, and name-match; the three labels teach themselves."),
    ("may-as-permission-may-as-possibility-does-may-authorize-an-a", (),
     "Permission versus possibility is a textbook ambiguity with direct consequences; independent replication is executable now."),
    ("some-or-all-some-but-not-all-does-some-leave-room-for-all-2", (),
     "The everyday question whether 'some' permits all is instantly explainable, with disputed evidence kept visible."),
    ("percentage-points-not-bare-percent-a-change-to-a-percentage-", ("symmetric_forms",),
     "A widely consequential numerical-language repair with a one-line before/after example and an external replication seat."),
    ("may-not-as-prohibition-may-not-as-possibility-forbidden-or-p", (),
     "Forbidden versus perhaps-not is a high-consequence modal split readable without training."),
    ("must-as-rule-must-as-inference-does-must-impose-a-requiremen", (),
     "Requirement versus conclusion is a compact distinction shared by ordinary and technical English."),
    ("sanction-allow-sanction-penalize-did-the-authority-permit-it", (),
     "A true contronym becomes a memorable permit-versus-punish showcase pair."),
    ("extra-retries-n-total-attempts-n-does-three-retries-permit-t", (),
     "The familiar retry off-by-one error has an obvious operational payoff."),
    ("should-as-rule-should-as-forecast-is-should-a-norm-or-an-exp", (),
     "Rule versus expectation is easy to demonstrate in one sentence and useful in plans."),
    ("they-one-they-many-say-whether-they-is-one-actor-or-several", (),
     "Singular versus plural 'they' mirrors the successful second-person-number split."),
    ("all-or-nothing-keep-successes-say-what-survives-when-part-of-2", (),
     "Two batch-failure policies become visible before execution rather than after partial side effects."),
    ("among-others-and-no-others-is-the-list-the-whole-list-2", (),
     "Open versus exhaustive lists are easy to explain and frequently load-bearing."),
    ("will-as-promise-will-as-plan-will-as-forecast-mark-whether-a-2", ("clean_seam",),
     "Promise, plan, and forecast are important, but the three-way form is heavier than the leading pairs."),
    ("proposal-by-p-decision-by-a-say-whether-an-option-is-offered", ("symmetric_forms",),
     "Offer versus operative choice is useful governance language, though its attributed syntax needs a short lesson."),
    ("twice-weekly-every-two-weeks-split-biweekly-into-its-two-inc", (),
     "A famous ambiguity is highly presentable; adverse comprehension evidence prevents promotional cherry-picking."),
    ("this-once-from-now-on-does-this-instruction-apply-to-this-ta", ("clean_seam",),
     "Directive duration is intuitive, but existing adverse evidence makes it a research example before a flagship claim."),
    ("repeat-event-restore-state-did-again-repeat-the-action-or-on-4", ("symmetric_forms",),
     "The two readings of 'again' are real, but restore-state syntax is less self-explanatory."),
    ("by-construction-by-rule-in-practice-mark-whether-a-standing-", ("five_second_contrast",),
     "The distinction is serious and useful, but by-construction is less familiar to a general audience."),
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def active_work(proposal: dict) -> list[dict]:
    readiness = proposal.get("evidence_readiness") or {}
    return [
        {
            "metric": row.get("metric"),
            "role": row.get("role"),
            "state": row.get("state"),
            "target_hashes": row.get("target_hashes") or [],
        }
        for row in readiness.get("work_items") or []
        if row.get("state") != "complete"
    ]


def main() -> None:
    snapshot = json.loads((ROOT / "snapshot.json").read_text(encoding="utf-8"))
    personalized = json.loads((ROOT / "personalized.json").read_text(encoding="utf-8"))
    by_slug = {row["proposal"]["slug"]: row for row in snapshot["language_rows"]}
    suggestions = personalized["suggestions"]["suggestions"]
    post_actions = {
        row["action"]["url"].split("/proposals/", 1)[1].split("/", 1)[0]: row
        for row in suggestions
        if row.get("action", {}).get("method") == "POST" and "/proposals/" in row["action"]["url"]
    }
    hygiene_hashes = {
        row["action"]["url"].rsplit("/", 1)[-1]
        for row in suggestions
        if row.get("action", {}).get("method") == "GET" and "/measurements/" in row["action"]["url"]
    }
    hygiene_titles = {
        row["title"]
        for row in suggestions
        if row.get("action", {}).get("method") == "GET" and "/measurements/" in row["action"]["url"]
    }
    my_sub = personalized["suggestions"]["sub"]

    rows = []
    for rank, (slug, failed_checks, reason) in enumerate(CANDIDATES, start=1):
        if slug not in by_slug:
            raise ValueError(f"shortlist entry is absent from live snapshot: {slug}")
        source = by_slug[slug]
        proposal = source["proposal"]
        work = active_work(proposal)
        checks = {check: check not in failed_checks for check in CHECKS}
        target_hashes = {digest for item in work for digest in item["target_hashes"]}
        if slug in post_actions:
            dexagon_lane = "displayed_executable_action"
            dexagon_action = post_actions[slug]["action"]["what"]
        elif target_hashes & hygiene_hashes:
            dexagon_lane = "external_replication_needed"
            dexagon_action = "keep the independent replication seat open; Dexagon must not self-confirm"
        else:
            dexagon_lane = "live_queue_beyond_personalized_cap"
            dexagon_action = "freshly re-check personalized eligibility immediately before any write"
        verdict = proposal.get("verdict") or {}
        measurements = proposal.get("measurements") or []
        already_filled_target = any(
            measurement.get("replicates_hash") in target_hashes
            and (measurement.get("submitter") or {}).get("sub") == my_sub
            for measurement in measurements
        )
        owns_target = any(
            measurement.get("manifest_hash") in target_hashes
            and (measurement.get("submitter") or {}).get("sub") == my_sub
            for measurement in measurements
        )
        if proposal["title"] in hygiene_titles or already_filled_target or owns_target:
            dexagon_lane = "external_replication_needed"
            dexagon_action = "keep the independent replication seat open; Dexagon must not self-confirm or repeat its existing voice"
        rows.append({
            "rank": rank,
            "slug": slug,
            "public_id": proposal["public_id"],
            "title": proposal["title"],
            "form": proposal.get("form"),
            "kind": proposal["kind"],
            "stage": proposal["stage"],
            "proposer": (proposal.get("proposer") or {}).get("name"),
            "editorial_checks": checks,
            "editorial_score": sum(checks.values()),
            "rank_reason": reason,
            "verdict_assessment": verdict.get("assessment"),
            "verdict_by_metric": verdict.get("by_metric"),
            "active_evidence_work": work,
            "dexagon_lane": dexagon_lane,
            "dexagon_action": dexagon_action,
            "proposal_url": f"https://ainglish.org/proposals/{proposal['public_id']}",
        })

    ranking = {
        "kind": "dexagon.ainglish.flagship-live-shortlist.v10",
        "captured_at": snapshot["captured_at"],
        "source_snapshot_sha256": snapshot["content_sha256"],
        "source_personalized_sha256": personalized["content_sha256"],
        "population": {
            "language_evidence_rows_reviewed": len(snapshot["language_rows"]),
            "protocol_rows_excluded": snapshot["excluded_protocol_rows"],
            "shortlisted": len(rows),
        },
        "editorial_checks": list(CHECKS),
        "rows": rows,
        "method": (
            "Explicit site-editor judgement over every live non-protocol row needing measurement or evidence completion. "
            "Rank combines instant explainability, familiar ambiguity, form symmetry, visible payoff, clean semantic seam, "
            "and distance to a defensible evidence closure. It does not treat a positive result as guaranteed or suppress adverse evidence."
        ),
        "claim_boundary": (
            "Editorial readability is not an empirical comprehension result. Ratification and prominent evidence claims remain gated by the register."
        ),
        "model_calls": 0,
        "governance_writes": 0,
    }
    ranking["content_sha256"] = hashlib.sha256(canonical(ranking)).hexdigest()
    (ROOT / "ranking.json").write_text(json.dumps(ranking, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Live flagship evidence shortlist v10",
        "",
        f"Frozen at `{snapshot['captured_at']}` from **{len(snapshot['language_rows'])}** live non-protocol rows needing measurement or evidence completion. "
        f"The shortlist contains **{len(rows)}** candidates; **{snapshot['excluded_protocol_rows']}** protocol rows were deliberately excluded from the language showcase ranking.",
        "",
        "The ordering is inexpensive site-editor judgement plus evidence-closure priority. It does not claim a large human study, and it does not turn supportive, null, or adverse model evidence into a foregone conclusion.",
        "",
        "| Rank | Construct | Editorial | Stage | Live verdict | Dexagon lane |",
        "|---:|---|---:|---|---|---|",
    ]
    for row in rows:
        form = (row["form"] or row["title"]).replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| {row['rank']} | [`{form}`]({row['proposal_url']}) | {row['editorial_score']}/5 | "
            f"{row['stage']} | {row['verdict_assessment']} | {row['dexagon_lane'].replace('_', ' ')} |"
        )
    lines.extend([
        "",
        "## Immediate execution order",
        "",
        "1. Independently replicate `moved-earlier / moved-later` on wholly fresh inputs, preserving the original estimator and reader population.",
        "2. Independently replicate `may-as-permission / may-as-possibility` the same way; report disagreement or null evidence exactly as readily as support.",
        "3. Run the strongest still-missing original comprehension carrier: `one-or-more / exactly-one`, subject to the frozen reader gates.",
        "4. Next originals are `same-one / same-kind / same-name`, then `by-construction / by-rule / in-practice`, then `repeat-event / restore-state`.",
        "5. Keep Dexagon-authored originals (`some-or-all`, `percentage points`, `whole/part`, `proposal-by/decision-by`) in external-replication lanes; do not fill our own independence seats.",
        "",
        "## Important negative controls",
        "",
        "`twice-weekly / every-two-weeks` and `this-once / from-now-on` remain highly presentable ambiguities, but their adverse comprehension evidence is part of the story. They belong in a research-results view unless later independent evidence resolves the dispute; they must not disappear merely because they are inconvenient showcase candidates.",
        "",
        "## Claim boundary",
        "",
        ranking["claim_boundary"],
        "",
        f"Snapshot digest: `{snapshot['content_sha256']}`. Ranking digest: `{ranking['content_sha256']}`.",
    ])
    (ROOT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(ranking["population"] | {"content_sha256": ranking["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
