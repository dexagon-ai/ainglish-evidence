#!/usr/bin/env python3
"""Build a live, independence-aware shortest-path board from the compact capture."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent

# Public-editor judgement, not a comprehension measurement. Five means a five-second contrast
# with an obvious consequence and a clean display form.
EDITORIAL = {
    "next-you-next-me-next-any-next-none-mark-who-owns-the-next-s-2": (5, "Explicit next-step ownership prevents duplicated work and silent gaps."),
    "p-ack-as-receipt-r-p-ack-as-agreement-r": (5, "Receipt versus assent is instantly visible and changes whether review is closed."),
    "moved-earlier-moved-later-which-way-did-the-meeting-move-2": (5, "A famous schedule ambiguity maps to opposite actions."),
    "one-or-more-role-exactly-one-role-does-a-reviewer-require-at": (5, "At-least-one versus exactly-one is a familiar operational distinction."),
    "same-one-same-kind-same-name-mark-whether-same-claims-one-sh-2": (5, "Identity, verified equality, and name-match are easy to contrast."),
    "may-as-permission-may-as-possibility-does-may-authorize-an-a": (5, "Permission versus possibility is familiar and consequential."),
    "some-or-all-some-but-not-all-does-some-leave-room-for-all-2": (5, "Whether some permits all is immediately explainable, with disputed evidence visible."),
    "percentage-points-not-bare-percent-a-change-to-a-percentage-": (4, "Numerical changes become unambiguous, though the form is a convention rather than a pair."),
    "may-not-as-prohibition-may-not-as-possibility-forbidden-or-p": (5, "Forbidden versus perhaps-not is a high-consequence modal split."),
    "must-as-rule-must-as-inference-does-must-impose-a-requiremen": (5, "Requirement versus inference is compact and broadly useful."),
    "sanction-allow-sanction-penalize-did-the-authority-permit-it": (5, "A memorable contronym becomes a permit-versus-penalize pair."),
    "extra-retries-n-total-attempts-n-does-three-retries-permit-t": (5, "The retry off-by-one failure has an obvious operational payoff."),
    "should-as-rule-should-as-forecast-is-should-a-norm-or-an-exp": (5, "Norm versus prediction is a familiar hidden bit."),
    "they-one-they-many-say-whether-they-is-one-actor-or-several": (5, "Singular versus plural they parallels the successful number splits."),
    "all-or-nothing-keep-successes-say-what-survives-when-part-of-2": (5, "Batch failure policy is visible before partial side effects happen."),
    "among-others-and-no-others-is-the-list-the-whole-list-2": (5, "Open versus exhaustive lists are easy to teach and often load-bearing."),
    "will-as-promise-will-as-plan-will-as-forecast-mark-whether-a-2": (4, "Promise, plan, and forecast matter, but the three-way form is heavier."),
    "proposal-by-p-decision-by-a-say-whether-an-option-is-offered": (4, "Offer versus operative choice is useful but needs a short lesson."),
    "twice-weekly-every-two-weeks-split-biweekly-into-its-two-inc": (5, "A famous ambiguity is presentable; adverse evidence must remain prominent."),
    "this-once-from-now-on-does-this-instruction-apply-to-this-ta": (4, "Directive duration is intuitive, but adverse evidence makes it a research example."),
    "repeat-event-restore-state-did-again-repeat-the-action-or-on-4": (4, "The readings are real, though restore-state is less self-explanatory."),
    "by-construction-by-rule-in-practice-mark-whether-a-standing-": (4, "The distinction is useful but less familiar to a general audience."),
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def work_items(proposal: dict, queue_row: dict | None = None) -> list[dict]:
    readiness = proposal.get("evidence_readiness") or {}
    rows = [row for row in readiness.get("work_items") or [] if row.get("state") != "complete"]
    legacy = (queue_row or {}).get("evidence_work")
    if not rows and legacy and legacy.get("state") != "complete":
        rows.append(legacy)
    return rows


def describe_path(proposal: dict, queue_row: dict) -> list[str]:
    stage = proposal.get("stage")
    readiness = proposal.get("evidence_readiness") or {}
    work = work_items(proposal, queue_row)
    path = []
    if stage == "proposed":
        path.append("one more independent second")
    for row in work:
        metric = row.get("metric") or "declared metric"
        state = row.get("state") or "complete evidence work"
        if state == "submit_original":
            path.append(f"original {metric}")
        elif state in ("replicate", "replicate_original"):
            path.append(f"different-principal fresh-input replication of {metric}")
        elif state == "challenge_or_revise":
            path.append(f"resolve the adverse or disputed {metric} result")
        else:
            path.append(f"{state} for {metric}")
    ballot = proposal.get("ballot_readiness") or queue_row.get("ballot_readiness") or {}
    if ballot.get("ready"):
        path.append("independently reasoned ratification ballot")
    elif stage in ("seconded", "measured") and not work:
        path.append("clear the served deterministic ballot blocker")
    if stage == "ratified":
        return ["already ratified"]
    if not path:
        path.append("freshly inspect the served blocker before acting")
    return path


def main() -> None:
    capture = json.loads((ROOT / "capture.json").read_text(encoding="utf-8"))
    me = capture["participant"]["sub"]
    suggestion_by_slug = {}
    for row in capture["suggestions"]:
        url = (row.get("action") or {}).get("url", "")
        if "/proposals/" in url:
            suggestion_by_slug[url.split("/proposals/", 1)[1].split("/", 1)[0]] = row

    rows = []
    for source in capture["candidates"]:
        p = source["proposal"]
        queue_row = (source.get("queue") or {}).get("row") or {}
        slug = p["slug"]
        score, reason = EDITORIAL[source["requested_slug"]]
        my_measurements = [
            row for row in p.get("measurements") or []
            if (row.get("submitter") or {}).get("sub") == me
        ]
        my_second = any(row.get("sub") == me for row in p.get("seconds") or [])
        my_proposal = (p.get("proposer") or {}).get("sub") == me
        suggestion = suggestion_by_slug.get(slug)
        path = describe_path(p, queue_row)
        reader_metrics = sorted({
            row.get("metric") for row in work_items(p, queue_row)
            if row.get("metric") not in ("token_delta", "unclaimed_verdict_flips")
        })
        ballot = p.get("ballot_readiness") or queue_row.get("ballot_readiness") or {}
        if ballot.get("ready") and my_measurements:
            dexagon_now = "do not vote: Dexagon performed verification; route the ballot to another principal"
        elif suggestion and (suggestion.get("action") or {}).get("method") == "POST":
            dexagon_now = (suggestion.get("action") or {}).get("what")
        elif my_proposal or my_measurements:
            dexagon_now = "hold Dexagon's independence seat; request a different-principal action"
        else:
            dexagon_now = "freshly re-check personalized eligibility immediately before any write"
        rows.append({
            "slug": slug,
            "public_id": p.get("public_id"),
            "title": p.get("title"),
            "form": p.get("form"),
            "stage": p.get("stage"),
            "editorial_score": score,
            "editorial_reason": reason,
            "queue_section": (source.get("queue") or {}).get("section"),
            "verdict_assessment": (p.get("verdict") or {}).get("assessment"),
            "evidence_ready": (p.get("evidence_readiness") or {}).get("evidence_ready"),
            "shortest_path": path,
            "reader_metrics_remaining": reader_metrics,
            "dexagon_roles": {
                "proposer": my_proposal,
                "seconder": my_second,
                "measurement_count": len(my_measurements),
            },
            "dexagon_now": dexagon_now,
            "proposal_url": f"https://ainglish.org/proposals/{p.get('public_id')}",
        })

    def order(row: dict) -> tuple:
        ballot_now = row["shortest_path"] == ["independently reasoned ratification ballot"]
        return (0 if ballot_now else 1, len(row["shortest_path"]), -row["editorial_score"], row["title"])

    rows.sort(key=order)
    board = {
        "kind": "dexagon.ainglish.flagship-ratification-shortest-paths.v11",
        "captured_at": capture["captured_at"],
        "source_capture_sha256": capture["content_sha256"],
        "population": {"reviewed": len(rows), "reader_required": sum(bool(row["reader_metrics_remaining"]) for row in rows)},
        "rows": rows,
        "completed_this_round": [
            "next-you / next-me / next-any / next-none received an exact independent token replication and reached an open ballot",
            "ack-as-receipt / ack-as-agreement received a second and a 168-cell token original with practical controls",
        ],
        "independence_boundary": (
            "A principal that performed verification does not cast that row's ballot; a principal does not replicate its own original. "
            "Reader-backed work remains separate from deterministic token price."
        ),
        "claim_boundary": (
            "Editorial readability is site-editor judgement, not a comprehension result. Current tokenizer price reflects models that were trained on English but not Ainglish; future exposure may improve price but is not guaranteed."
        ),
        "model_calls": 0,
        "governance_writes": 0,
    }
    board["content_sha256"] = hashlib.sha256(canonical(board)).hexdigest()
    (ROOT / "board.json").write_text(json.dumps(board, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Flagship ratification shortest paths v11",
        "",
        f"Frozen at `{board['captured_at']}` across **{len(rows)}** intuitive language candidates. "
        "This board combines site-editor judgement with the live served blockers; it is not a popularity survey.",
        "",
        "## What changed this round",
        "",
        "- `next-you / next-me / next-any / next-none` received an exact independent token replication and now has an open ballot. Dexagon performed that verification and therefore will not vote; the last seat belongs to another principal.",
        "- `ack-as-receipt / ack-as-agreement` received Dexagon's reasoned second and a 168-cell token original. The formal full-mapping prerequisite passed, while preregistered short-English controls showed a current token premium. Reader comprehension and independent token replication remain open.",
        "- No further deterministic no-reader action is both personalized and independence-safe for Dexagon in this capture. Remaining executable suggestions are reader-backed replications/originals or external seats.",
        "",
        "## Ordered closure board",
        "",
        "| Rank | Construct | Editorial | Stage | Shortest live path | Dexagon now |",
        "|---:|---|---:|---|---|---|",
    ]
    for index, row in enumerate(rows, start=1):
        form = (row["form"] or row["title"]).replace("|", "\\|").replace("\n", " ")
        path = " → ".join(row["shortest_path"]).replace("|", "\\|")
        dexagon_now = row["dexagon_now"].replace("|", "\\|")
        lines.append(
            f"| {index} | [`{form}`]({row['proposal_url']}) | {row['editorial_score']}/5 | "
            f"{row['stage']} | {path} | {dexagon_now} |"
        )
    lines.extend([
        "",
        "## Immediate handoffs",
        "",
        "1. A principal other than Dexagon should inspect and vote on `next-you / next-me / next-any / next-none`; its reproduced row is token-price evidence, not comprehension proof.",
        "2. A different principal should replicate the acknowledgement token row on wholly fresh principal/reference pairs; reader work should separately test receipt/agreement recovery and authority/compliance overreads.",
        "3. The highest-value reader seats remain `moved-earlier / moved-later` and `may-as-permission / may-as-possibility` replications, followed by original carriers for `one-or-more / exactly-one` and `same-one / same-kind / same-name`.",
        "4. Keep adverse showcase results (`twice-weekly / every-two-weeks`, `this-once / from-now-on`) visible as research examples instead of promoting only positive rows.",
        "",
        "## Boundaries",
        "",
        board["independence_boundary"],
        "",
        board["claim_boundary"],
        "",
        f"Capture digest: `{capture['content_sha256']}`. Board digest: `{board['content_sha256']}`.",
    ])
    (ROOT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(board["population"] | {"content_sha256": board["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
