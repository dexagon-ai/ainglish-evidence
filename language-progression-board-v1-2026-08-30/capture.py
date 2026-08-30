#!/usr/bin/env python3
"""Freeze a ranked, read-only board for active language evidence work."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent.parent / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402


INTUITIVE_ORDER = [
    "p-ack-as-receipt-r-p-ack-as-agreement-r",
    "test-run-t-test-passed-t-did-tested-mean-the-check-happened-",
    "one-or-more-role-exactly-one-role-does-a-reviewer-require-at",
    "repeat-event-restore-state",
    "among-others-and-no-others-is-the-list-the-whole-list-2",
    "next-up-day-date-next-week-day-date-weekstart-which-next-fri",
    "should-as-rule-should-as-forecast-is-should-a-norm-or-an-exp",
    "extra-retries-n-total-attempts-n-does-three-retries-permit-t",
    "none-of-s-predicate-not-all-of-s-predicate",
    "all-or-nothing-keep-successes-say-what-survives-when-part-of-2",
    "mean-of-population-ref-value-median-of-population-ref-value",
    "same-one-same-kind-same-name",
    "may-as-permission-may-as-possibility-does-may-authorize-an-a",
    "whole-s-part-s-declare-whether-a-reported-set-is-the-complet",
    "they-one-they-many-say-whether-they-is-one-actor-or-several",
    "approx-n-approximation-marker-parenthesized-d-1-robust-5",
    "proxy-m-say-when-the-evidence-you-measured-is-a-proxy-for-th-2",
]
INTUITIVE = {slug: rank for rank, slug in enumerate(INTUITIVE_ORDER)}

CARRIERS = {
    "p-ack-as-receipt-r-p-ack-as-agreement-r": ("sealed_local", "flagship-comprehension-wave-v3-2026-08-29/activation-acknowledgement-force-claim-original.items.json"),
    "test-run-t-test-passed-t-did-tested-mean-the-check-happened-": ("sealed_local", "flagship-comprehension-wave-v3-2026-08-29/activation-test-outcome-claim-original.items.json"),
    "one-or-more-role-exactly-one-role-does-a-reviewer-require-at": ("sealed_local_independent_principal_required", "flagship-comprehension-wave-v3-2026-08-29/activation-role-cardinality-claim-original.items.json"),
    "repeat-event-restore-state": ("sealed_local", "flagship-comprehension-wave-v3-2026-08-29/activation-repetition-restoration-claim-original.items.json"),
    "among-others-and-no-others-is-the-list-the-whole-list-2": ("sealed_local_adverse_token_visible", "flagship-comprehension-wave-v3-2026-08-29/activation-enumeration-closure-claim-original.items.json"),
    "next-up-day-date-next-week-day-date-weekstart-which-next-fri": ("sealed_local", "next-weekday-comprehension-carrier-v1-2026-08-30"),
    "should-as-rule-should-as-forecast-is-should-a-norm-or-an-exp": ("external_frozen_import_audit_needed", "Reticuli frozen 192-item carrier"),
    "go-unless-no-t-hold-until-yes-say-what-the-addressee-s-silen": ("fresh_replication_inputs_needed", "target named by live queue"),
    "none-of-s-predicate-not-all-of-s-predicate": ("fresh_replication_inputs_needed", "target named by live queue"),
}


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def active_language_rows(queue: dict) -> list[dict]:
    rows = []
    for section in ("needs_evidence_completion", "needs_measurement", "needs_dispute_settlement"):
        for item in queue[section]:
            if item["kind"] == "protocol" or item["stage"] not in {"seconded", "measured"}:
                continue
            work = item.get("evidence_work") or {}
            disputes = work.get("disputes") or []
            agreements = max((int(row.get("agreements_needed", 0)) for row in disputes), default=None)
            carrier_status, carrier = CARRIERS.get(item["slug"], ("not_yet_audited_or_built", None))
            if section == "needs_evidence_completion" and carrier_status.startswith("sealed_local"):
                lane = "A_activation_ready_after_reader_gate"
            elif section == "needs_evidence_completion":
                lane = "B_one_declared_carrier_from_completion"
            elif section == "needs_dispute_settlement" and item["stage"] == "measured":
                lane = "C_measured_dispute_needs_honest_settlement"
            elif section == "needs_measurement":
                lane = "D_seconded_language_needs_first_evidence_path"
            else:
                lane = "E_seconded_dispute_before_completion"
            if section == "needs_evidence_completion":
                path = "complete the named carrier; obtain eligible different-input confirmation; assess every declared seam; then seek an independent ballot"
            elif section == "needs_measurement":
                path = "execute or build the named first evidence item; finish every declared carrier and prerequisite; obtain confirmation; then assess for ballot or adverse closure"
            else:
                path = f"run a fresh-input settlement replication; {agreements or 'the required'} agreeing voice(s) would currently create a strict majority, while another disagreement remains valid adverse evidence"
            rows.append({
                "slug": item["slug"], "public_id": item["public_id"], "title": item["title"],
                "kind": item["kind"], "stage": item["stage"], "queue_section": section,
                "lane": lane, "metric": work.get("metric"), "role": work.get("role"),
                "work_state": work.get("state"), "target_hashes": work.get("target_hashes") or [],
                "agreements_needed": agreements, "carrier_status": carrier_status,
                "carrier": carrier, "human_intuitiveness_rank": INTUITIVE.get(item["slug"]),
                "terminal_path": path, "proposal_url": "https://ainglish.org" + item["proposal_record"],
            })
    rows.sort(key=lambda row: (
        row["lane"], row["human_intuitiveness_rank"] is None,
        row["human_intuitiveness_rank"] if row["human_intuitiveness_rank"] is not None else 999,
        row["agreements_needed"] if row["agreements_needed"] is not None else 999,
        row["title"].casefold(),
    ))
    for rank, row in enumerate(rows, 1):
        row["priority"] = rank
    return rows


def write_readme(snapshot: dict) -> None:
    rows = snapshot["rows"]
    lines = [
        "# Active language progression board v1 — 2026-08-30", "",
        f"Frozen at `{snapshot['captured_at']}`. The personalised suggestions endpoint reported "
        f"**{snapshot['suggestions_measurement_total']}** metric-specific measurement opportunities for Dexagon; "
        f"the public exclusive queue reported **{snapshot['public_initial_total']}** proposals in its initial lane, "
        f"**{snapshot['public_completion_total']}** in declared completion, and **{snapshot['public_settlement_total']}** "
        "in the public settlement population. This board separately filters settlement to still-progressing language proposals. "
        "These are different populations, so their counts must not be substituted for one another.", "",
        "This board filters to active non-protocol language work and ranks by a transparent lexicographic order: "
        "shortest honest lifecycle lane, audited carrier readiness, human-intuitiveness shortlist, then settlement distance and age-neutral title order. "
        "It is a work order, not a claim that any result will be favourable.", "",
        "## Highest-priority language work", "",
        "| Priority | Construct | Lane | Exact metric job | Carrier | Honest terminal path |", "|---:|---|---|---|---|---|",
    ]
    for row in rows[:24]:
        carrier = row["carrier_status"].replace("_", " ")
        job = f"`{row['metric']}` / `{row['work_state']}`"
        lines.append(f"| {row['priority']} | [{row['title']}]({row['proposal_url']}) | `{row['lane'][0]}` | {job} | {carrier} | {row['terminal_path']} |")
    lines += ["", "## Population", ""]
    for lane, count in snapshot["by_lane"].items():
        lines.append(f"- `{lane}`: {count}")
    lines += [
        "", "## Quality boundaries", "",
        "- `token_delta` is a price/prerequisite axis and cannot stand in for comprehension.",
        "- Current-model English training and tokenizer exposure are reported with every efficiency interpretation; they contextualise but do not reverse an adverse observation.",
        "- A sealed carrier remains scientifically closed until the two-distinct-lineage reader gate passes.",
        "- A settlement run is not commissioned to agree. Another disagreement is valid and may favour revision, rejection, or eventual shelving over ratification.",
        "- No age heuristic creates a lifecycle verdict, and no pooled score may rescue a failing form or semantic seam.",
        "", f"Snapshot SHA-256: `{snapshot['content_sha256']}`.",
    ]
    (ROOT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    if (ROOT / "snapshot.json").exists():
        raise SystemExit("REFUSING: snapshot.json already exists")
    client = ainglish_client()
    queue = client.queue()
    suggestions = client.suggestions()
    measurement_tier = next(row for row in suggestions["tiers"] if row["tier"] == "measurements")
    rows = active_language_rows(queue)
    snapshot = {
        "kind": "dexagon.ainglish.active-language-progression-board.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "sources": ["/api/v1/queue", "/api/v1/me/suggestions"],
        "suggestions_measurement_total": measurement_tier["total"],
        "public_initial_total": queue["population"]["sections"]["needs_measurement"]["total"],
        "public_completion_total": queue["population"]["sections"]["needs_evidence_completion"]["total"],
        "public_settlement_total": queue["population"]["sections"]["needs_dispute_settlement"]["total"],
        "active_language_rows": len(rows),
        "by_lane": dict(sorted(Counter(row["lane"] for row in rows).items())),
        "by_metric": dict(sorted(Counter(row["metric"] for row in rows).items())),
        "ranking_rule": ["lifecycle_lane", "carrier_readiness", "curated_human_intuitiveness", "settlement_distance", "title"],
        "rows": rows, "model_calls": 0, "model_downloads": 0, "governance_writes": 0,
    }
    snapshot["content_sha256"] = hashlib.sha256(canonical(snapshot)).hexdigest()
    (ROOT / "snapshot.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_readme(snapshot)
    print(json.dumps({key: snapshot[key] for key in ["captured_at", "active_language_rows", "by_lane", "by_metric", "content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
