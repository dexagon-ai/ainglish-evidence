#!/usr/bin/env python3
"""Build a public editorial readiness snapshot from the live Ainglish API."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path

from ainglish.client import AinglishClient


ROOT = Path(__file__).resolve().parent

EDITORIAL = [
    {
        "slug": "we-including-you-we-excluding-you-clusivity-mark-whether-we--4",
        "readiness": "site_ready_with_claim_guard",
        "human_intuition": "strong",
        "website_use": "lead flagship example",
        "safe_caption": "we-including-you includes the reader; we-excluding-you does not.",
        "evidence_posture": "Ratified. Multiple confirmed token originals exist, but the token record is contested and the old comprehension rows are instrument-invalid.",
        "do_not_say": "Do not call human comprehension experimentally proven; present the distinction itself and qualify the token claim."
    },
    {
        "slug": "you-one-you-all-say-whether-you-addresses-one-recipient-or-t",
        "readiness": "site_ready_with_claim_guard",
        "human_intuition": "strong",
        "website_use": "lead or supporting flagship example",
        "safe_caption": "you-one addresses one recipient; you-all addresses the whole group.",
        "evidence_posture": "Ratified with one confirmed, uncontested token original.",
        "do_not_say": "Token confirmation is not a comprehension study."
    },
    {
        "slug": "fact-not-known-choice-not-made-distinguish-missing-evidence-",
        "readiness": "site_ready_with_claim_guard",
        "human_intuition": "strong",
        "website_use": "prominent workflow example",
        "safe_caption": "fact-not-known means evidence is missing; choice-not-made means the decision is still pending.",
        "evidence_posture": "Ratified with one exactly confirmed, uncontested token original.",
        "do_not_say": "Do not imply the marker proves that an agent searched adequately or that a decision process is sound."
    },
    {
        "slug": "no-delegation-one-hop-delegation-allowed-state-whether-a-tas",
        "readiness": "site_ready_with_claim_guard",
        "human_intuition": "strong",
        "website_use": "prominent agent-work example",
        "safe_caption": "no-delegation forbids handoff; one-hop-delegation-allowed permits direct delegates but no further handoff.",
        "evidence_posture": "Ratified. Two token originals are confirmed, including a fresh exact 1.0-disjoint replication; historical token rows also contain a separate dispute.",
        "do_not_say": "Do not claim compliance or comprehension from token counts."
    },
    {
        "slug": "each-alone-as-one-distributive-vs-collective-does-the-plural",
        "readiness": "candidate_with_conflicting_evidence",
        "human_intuition": "strong",
        "website_use": "examples page with evidence caveat, not lead carousel",
        "safe_caption": "each-alone means every member acts separately; as-one means the group acts collectively.",
        "evidence_posture": "Ratified. One +47.37 comprehension original is confirmed, but a separate valid -23.33 comprehension original is awaiting settlement and the token original is disputed.",
        "do_not_say": "Do not present a single settled comprehension effect until the adverse original is independently resolved."
    },
    {
        "slug": "by-unknown-by-withheld-typed-doer-omission-why-mistakes-were-3",
        "readiness": "hold_evidence_conflict",
        "human_intuition": "strong",
        "website_use": "explain the research process, not a proven flagship",
        "safe_caption": "by-unknown says the author does not know the actor; by-withheld says the author knows but does not disclose.",
        "evidence_posture": "Ratified with confirmed token savings. The +39.06 comprehension original is disputed by a fresh eligible -62.5 replication whose careful-English arm scored 24/24.",
        "do_not_say": "Do not claim a comprehension advantage."
    },
    {
        "slug": "start-by-complete-by-say-which-task-event-a-deadline-constra",
        "readiness": "hold_evidence_conflict",
        "human_intuition": "strong",
        "website_use": "semantic example only with an unmeasured label",
        "safe_caption": "start-by constrains when work begins; complete-by constrains when it finishes.",
        "evidence_posture": "Ratified but currently assessed unmeasured; both visible token originals are disputed.",
        "do_not_say": "Do not claim measured benefit or settled compression."
    },
    {
        "slug": "or-both-not-both-english-or-never-says-whether-both-is-allow",
        "readiness": "hold_measured_inconclusive",
        "human_intuition": "strong",
        "website_use": "show as an intuitive idea whose evidence is inconclusive",
        "safe_caption": "or-both allows both alternatives; not-both forbids choosing both.",
        "evidence_posture": "Ratified but measured-inconclusive; the current verdict's token value is +0.5 and opposes the claimed efficiency direction.",
        "do_not_say": "Do not imply token efficiency or an overall measured win."
    },
    {
        "slug": "true-as-worded-false-as-worded-unambiguous-answers-to-negati",
        "readiness": "hold_measured_inconclusive",
        "human_intuition": "medium",
        "website_use": "supporting example only",
        "safe_caption": "true-as-worded and false-as-worded answer the sentence exactly as phrased, including negation.",
        "evidence_posture": "Ratified but measured-inconclusive; the confirmed token result is classified neutral.",
        "do_not_say": "Do not call the overall proposal experimentally supported."
    },
    {
        "slug": "moved-earlier-moved-later-which-way-did-the-meeting-move",
        "readiness": "pipeline_high_priority",
        "human_intuition": "strong",
        "website_use": "future flagship candidate",
        "safe_caption": "moved-earlier and moved-later make the direction of a schedule change explicit.",
        "evidence_posture": "Seconded into the measurement queue; no claim-carrier result yet.",
        "do_not_say": "Do not present it as ratified or measured."
    },
    {
        "slug": "among-others-and-no-others-is-the-list-the-whole-list",
        "readiness": "pipeline_high_priority",
        "human_intuition": "strong",
        "website_use": "future flagship candidate",
        "safe_caption": "among-others leaves a list open; and-no-others says the list is complete.",
        "evidence_posture": "Proposed at one second of three; attachment scope is the primary recorded weakness.",
        "do_not_say": "Do not present it as seconded, ratified, or measured."
    },
    {
        "slug": "some-or-all-some-but-not-all-does-some-leave-room-for-all-2",
        "readiness": "pipeline_instrument_blocked",
        "human_intuition": "strong",
        "website_use": "future flagship candidate after evidence repair",
        "safe_caption": "some-or-all leaves room for every member; some-but-not-all excludes the all-members case.",
        "evidence_posture": "The comprehension claim carrier is still missing. Reader qualification v4 failed its untouched holdout 33/36 against a 34/36 floor, so no scientific attempt was minted.",
        "do_not_say": "Do not present a measured comprehension result or conceal the instrument gate."
    },
]


def measurement_summary(row: dict) -> dict:
    keys = (
        "manifest_hash", "metric", "value", "value_lo", "value_hi", "is_replication",
        "replicates_hash", "reproduced_ok", "settlement_eligible", "input_disjointness",
        "replication_count", "disagreement_count", "settlement_state", "confirmed",
        "evidence_state", "counts_toward_verdict",
    )
    return {key: row.get(key) for key in keys}


def main() -> None:
    client = AinglishClient(use_env=False)
    proposals = list(client.iter_proposals(page_size=200))
    stage_counts = Counter(row.get("stage") for row in proposals)
    rows = []
    for editorial in EDITORIAL:
        detail = client.proposal(editorial["slug"])
        rows.append({
            **editorial,
            "public_id": detail.get("public_id"),
            "title": detail.get("title"),
            "stage": detail.get("stage"),
            "form": detail.get("form"),
            "url": f"https://ainglish.org/proposals/{detail.get('public_id')}",
            "verdict": detail.get("verdict"),
            "evidence_contract": detail.get("evidence_contract"),
            "evidence_readiness": detail.get("evidence_readiness"),
            "measurements": [measurement_summary(row) for row in detail.get("measurements", [])],
        })
    generated = datetime.now(timezone.utc).isoformat()
    document = {
        "kind": "dexagon.ainglish.flagship-readiness-register.v1",
        "generated_at": generated,
        "source": "https://ainglish.org/api/v1",
        "register_rows": len(proposals),
        "stage_counts": dict(sorted(stage_counts.items())),
        "method": {
            "scope": "Editorial shortlist of intuitive human-facing constructs, not a replacement for Ainglish lifecycle or evidence verdicts.",
            "site_ready_rule": "A construct may be showcased as an example when its semantic split is immediately explainable and its caption states no stronger empirical claim than the live evidence supports.",
            "evidence_rule": "Ratification, confirmation, comprehension, token efficiency, and adoption are separate claims; conflicts and invalid instruments remain visible.",
            "human_validation": "No large human-review campaign is required by this register. Editorial intuitiveness is an explicit judgement; empirical claims come only from registered evidence."
        },
        "summary": dict(Counter(row["readiness"] for row in rows)),
        "entries": rows,
    }
    (ROOT / "register.json").write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n")

    lines = [
        "# Ainglish flagship-readiness register",
        "",
        f"Live snapshot: `{generated}`. Register rows: `{len(proposals)}`.",
        "",
        "This is an editorial aid, not a new governance status. It keeps intuitive surface quality",
        "separate from the exact empirical claim the register currently supports.",
        "",
        "| Construct | Stage | Editorial readiness | Evidence-safe website use |",
        "|---|---|---|---|",
    ]
    for row in rows:
        title = row["title"].replace("|", "\\|")
        caption = row["safe_caption"].replace("|", "\\|")
        lines.append(
            f"| [{title}]({row['url']}) | {row['stage']} | `{row['readiness']}` | {caption} |"
        )
    lines += [
        "",
        "## Current recommendation",
        "",
        "Use clusivity, you-one/you-all, fact-not-known/choice-not-made, and delegation policy",
        "as the first website set, with their claim guards. Keep each-alone/as-one visible but",
        "caveated. Do not promote by-unknown/by-withheld, start-by/complete-by, or or-both/not-both",
        "as measured wins while their live conflicts remain. Treat moved-earlier/moved-later and",
        "among-others/and-no-others as the two highest-priority pipeline candidates.",
        "",
        "The complete per-measurement receipts and `do_not_say` constraints are in `register.json`.",
    ]
    (ROOT / "README.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({
        "generated_at": generated,
        "register_rows": len(proposals),
        "stage_counts": dict(stage_counts),
        "shortlist_entries": len(rows),
        "summary": document["summary"],
    }, indent=2))


if __name__ == "__main__":
    main()
