#!/usr/bin/env python3
"""Freeze a complete, decision-oriented audit of the active Ainglish backlog."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent
sys.path.insert(0, str(PROJECT / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402


ROUTES = {
    "needs_second": ("attention", "Decide whether the idea is worth measuring; a second is not an adoption vote."),
    "needs_measurement": ("evidence", "Run the named first measurement under a frozen, re-runnable contract."),
    "needs_evidence_completion": ("evidence", "Complete the proposal's declared evidence contract before recommending a ballot."),
    "needs_dispute_settlement": ("evidence decision", "Run or reconstruct the named settlement path; agreement and disagreement are both valid outcomes."),
    "needs_vote": ("public decision", "Read the full record and cast a reasoned public ballot."),
    "needs_gate_clearance": ("repair", "Clear the named deterministic or record-integrity defect before progression."),
    "needs_recertification": ("maintenance", "Re-test ratified language; confirmed regression can reverse ratification."),
}


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def scalar_action(action: object) -> str | None:
    if isinstance(action, str):
        return action
    if isinstance(action, dict):
        return action.get("what") or action.get("next_action") or action.get("label")
    return None


def render(snapshot: dict) -> str:
    counts = snapshot["active_backlog"]["by_queue_section"]
    lines = [
        "# Active proposal disposition audit — 2026-09-04",
        "",
        f"Frozen at `{snapshot['captured_at']}` from the live progression, dispute-triage, and release-preview APIs. "
        "This is a read-only audit: no model calls and no governance writes.",
        "",
        "## Executive finding",
        "",
        f"All **{snapshot['active_backlog']['total']} active proposals** have an explicit next route. "
        "Most are not waiting for a subjective editorial decision: they are waiting for evidence work. "
        f"The largest current groups are **{counts.get('needs_dispute_settlement', 0)} dispute settlements**, "
        f"**{counts.get('needs_measurement', 0)} first measurements**, and "
        f"**{counts.get('needs_evidence_completion', 0)} declared evidence completions**.",
        "",
        "A proposal should only move to a negative terminal outcome for the reason actually established: "
        "confirmed adverse claim-carrier evidence can reject it; a public ballot can fail it; author withdrawal, "
        "attention lapse, supersession, and post-ratification deprecation are separate outcomes. Present token cost "
        "is evidence, but it does not by itself decide a comprehension claim, especially while current tokenizers "
        "and models have an English-training advantage over new Ainglish forms.",
        "",
        "## Where the active backlog sits",
        "",
        "| Queue | Proposals | Decision class | Exact completion condition |",
        "|---|---:|---|---|",
    ]
    for section, count in counts.items():
        decision_class, rule = ROUTES.get(section, ("other", "Follow the canonical proposal record."))
        lines.append(f"| `{section}` | {count} | {decision_class} | {rule} |")

    dispute = snapshot["dispute_population"]
    lines += [
        "",
        "## Dispute routes",
        "",
        f"The live triage contains **{dispute['targets']} measurement targets**. "
        f"**{dispute['by_route'].get('ready_fresh_replication', 0)}** has a directly copyable modern contract; "
        f"**{dispute['by_route'].get('legacy_replication_or_replacement', 0)}** permits a fresh-input legacy replication "
        "but prefers a modern successor; and "
        f"**{dispute['by_route'].get('insufficient_retained_material', 0)}** needs a public record-only contract decision rather than a fabricated rerun.",
        "",
        "## Every active proposal",
        "",
        "| Construct | Stage | Current route | Named next action |",
        "|---|---|---|---|",
    ]
    for row in snapshot["active_backlog"]["rows"]:
        title = row["title"].replace("|", "\\|")
        action = (row.get("next_action") or "Read the canonical record.").replace("|", "\\|")
        lines.append(
            f"| [{title}](https://ainglish.org/proposals/{row['public_id']}) | "
            f"`{row['stage']}` | `{row['queue_section']}` | {action} |"
        )

    release = snapshot["next_release"]
    lines += [
        "",
        "## Publication boundary",
        "",
        f"The next-release preview contains **{release.get('new_ratified_count', 0)} newly ratified entries**; "
        f"**{release.get('release_data_ready_count', 0)}** have release data ready. "
        f"The normal seven-day cadence floor is `{release.get('cadence_floor_at')}`. "
        "This audit does not stage or publish a release.",
        "",
        "## Reproducibility",
        "",
        "The machine-readable `snapshot.json` preserves every active row, its canonical queue section, its "
        "server-derived next action, the full dispute summary, and the next-release summary. Re-run `capture.py` "
        "into a new dated directory for a later census; this frozen snapshot refuses overwrite.",
        "",
        f"Snapshot SHA-256: `{snapshot['content_sha256']}`.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    target = ROOT / "snapshot.json"
    if target.exists():
        raise SystemExit("REFUSING: snapshot.json already exists")

    client = ainglish_client()
    progression = client.progression()
    disputes = client.dispute_triage()
    release = client.release_preview()

    rows = []
    for plan in progression["plans"]:
        work = plan.get("evidence_work") or {}
        execution = plan.get("evidence_execution_plan") or {}
        rows.append({
            "public_id": plan.get("public_id"),
            "slug": plan.get("slug"),
            "title": plan.get("title"),
            "kind": plan.get("kind"),
            "stage": plan.get("stage"),
            "queue_section": plan.get("queue_section"),
            "decision_class": ROUTES.get(plan.get("queue_section"), ("other", ""))[0],
            "next_action": scalar_action(plan.get("current_action")),
            "metric": work.get("metric"),
            "evidence_role": work.get("role"),
            "evidence_state": work.get("state"),
            "target_hashes": work.get("target_hashes") or [],
            "execution_route": execution.get("route") or execution.get("operation"),
            "proposal_record": plan.get("proposal_record"),
        })
    rows.sort(key=lambda row: (row["queue_section"], row["title"].casefold(), row["slug"]))

    dispute_routes = Counter()
    dispute_resolution = Counter()
    for row in disputes.get("targets") or []:
        route = row.get("triage_route") or {}
        dispute_routes[route.get("key", "unknown")] += 1
        dispute_resolution[row.get("resolution_class", "unknown")] += 1

    release_summary = release.get("summary") or {}
    cadence = release.get("cadence") or {}
    snapshot = {
        "kind": "dexagon.ainglish.active-disposition-audit.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "sources": ["/api/v1/progression", "/api/v1/disputes/triage", "/api/v1/releases/preview"],
        "active_backlog": {
            "total": progression["total"],
            "by_queue_section": dict(sorted(Counter(row["queue_section"] for row in rows).items())),
            "by_stage": dict(sorted(Counter(row["stage"] for row in rows).items())),
            "by_decision_class": dict(sorted(Counter(row["decision_class"] for row in rows).items())),
            "rows": rows,
        },
        "dispute_population": {
            "targets": len(disputes.get("targets") or []),
            "by_route": dict(sorted(dispute_routes.items())),
            "by_resolution_class": dict(sorted(dispute_resolution.items())),
            "summary": disputes.get("summary"),
        },
        "next_release": {
            "new_ratified_count": release.get("count"),
            "release_data_ready_count": release_summary.get("release_data_ready"),
            "showcase_ready_count": release_summary.get("showcase_ready"),
            "showcase_review_count": release_summary.get("showcase_review"),
            "cadence_floor_at": cadence.get("earliest_routine_at"),
        },
        "terminal_route_policy": {
            "rejected": "confirmed adverse claim-carrier evidence",
            "vote_failed": "public ballot did not pass",
            "withdrawn": "author withdrew the current proposal",
            "lapsed": "attention deadline elapsed under the register rule",
            "superseded": "a successor revision replaced this record",
            "deprecated": "post-ratification regression or governance reversal",
        },
        "claim_boundaries": [
            "Queue sections are mutually exclusive server-derived work routes, not subjective quality scores.",
            "Token cost is not a proxy for comprehension and does not by itself reject a comprehension claim.",
            "Current-system English training and tokenizer asymmetry contextualises efficiency results but never erases them.",
            "A disagreement is a valid settlement result and must remain public.",
            "This audit does not stage a release.",
        ],
        "model_calls": 0,
        "model_downloads": 0,
        "governance_writes": 0,
    }
    snapshot["content_sha256"] = hashlib.sha256(canonical(snapshot)).hexdigest()
    target.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "README.md").write_text(render(snapshot), encoding="utf-8")
    print(json.dumps({
        "captured_at": snapshot["captured_at"],
        "active": snapshot["active_backlog"]["total"],
        "by_queue_section": snapshot["active_backlog"]["by_queue_section"],
        "dispute_routes": snapshot["dispute_population"]["by_route"],
        "content_sha256": snapshot["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
