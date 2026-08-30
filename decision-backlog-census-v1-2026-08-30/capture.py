#!/usr/bin/env python3
"""Freeze and explain the live dispute and declared-evidence populations.

This is a read-only register audit. It deliberately separates disagreements attached to
progressing proposals from continuing ratified maintenance and historical records.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402


PROGRESSION = {"proposed", "seconded", "measured"}
MAINTENANCE = {"ratified"}


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def scope(stage: str) -> str:
    if stage in PROGRESSION:
        return "progression"
    if stage in MAINTENANCE:
        return "maintenance"
    return "history"


def is_backfilled(measurement: dict) -> bool:
    attempt = measurement.get("attempt") or {}
    if isinstance(attempt.get("backfilled"), bool):
        return attempt["backfilled"]
    estimand = ((attempt.get("pin") or {}).get("estimand") or "")
    return "no preregistration existed" in estimand


def write_readme(snapshot: dict) -> None:
    dispute = snapshot["dispute_population"]
    completion = snapshot["evidence_completion_population"]
    lines = [
        "# Decision-backlog census v1 — 2026-08-30",
        "",
        f"Frozen at `{snapshot['captured_at']}` from the live public queue and measurement records. "
        "This is a read-only census: zero model calls and zero governance writes.",
        "",
        "## The headline distinction",
        "",
        f"The register exposed **{dispute['proposal_count']} proposals** containing "
        f"**{dispute['original_count']} disputed originals**. Only "
        f"**{dispute['by_scope'].get('progression', 0)} proposals** are active progression work. "
        f"The other **{dispute['by_scope'].get('maintenance', 0)}** are continuing ratified maintenance "
        f"and **{dispute['by_scope'].get('history', 0)}** are historical records. A disagreement remains "
        "public in every scope, but maintenance and history must not inflate the number of proposals waiting to advance.",
        "",
        "| Scope | Proposals | Human meaning |",
        "|---|---:|---|",
        f"| Progression | {dispute['by_scope'].get('progression', 0)} | A settlement run can change the current proposal path. |",
        f"| Ratified maintenance | {dispute['by_scope'].get('maintenance', 0)} | Standing language remains testable; regression rules stay armed. |",
        f"| History | {dispute['by_scope'].get('history', 0)} | The result is citable history, not unfinished proposal work. |",
        "",
        "## Dispute composition",
        "",
        "| Stage | Proposals |",
        "|---|---:|",
    ]
    lines += [f"| `{key}` | {value} |" for key, value in dispute["by_stage"].items()]
    lines += ["", "| Metric | Disputed originals |", "|---|---:|"]
    lines += [f"| `{key}` | {value} |" for key, value in dispute["by_metric"].items()]
    lines += [
        "",
        f"Of the disputed originals, **{dispute['backfilled_originals']}** predate attempt preregistration "
        f"and **{dispute['preregistered_originals']}** have a prospective attempt record. That is an audit "
        "property, not an automatic validity verdict: settlement eligibility and evidence moderation remain separate fields.",
        "",
        "Agreement work is concentrated as follows: "
        + ", ".join(f"{count} original{'s' if count != 1 else ''} need {needed}" for needed, count in dispute["agreements_needed_distribution"].items())
        + ".",
        "",
        "## Declared evidence completion",
        "",
        f"The exclusive queue exposed **{completion['proposal_count']} measured proposals** whose formal ballot gate "
        "is clear but whose public evidence contract still names unfinished work. This is author-declared scientific "
        "completion, not a second hidden ratification gate.",
        "",
        "| Construct | Next metric | Work state |",
        "|---|---|---|",
    ]
    for row in completion["rows"]:
        lines.append(f"| [{row['title']}](https://ainglish.org/proposals/{row['public_id']}) | `{row['metric']}` | `{row['state']}` |")
    lines += [
        "",
        "## Interpretation policy",
        "",
        "- Settlement work preserves the original estimand and uses genuinely different complete inputs. A further disagreement is a valid result.",
        "- Current token and model results describe systems trained primarily on ordinary English. That asymmetry accompanies efficiency claims; it does not reverse an observed adverse result.",
        "- Comprehension work remains blocked until its named reader qualification and independence conditions are met. Idle compute alone is not a scientific gate pass.",
        "- Shelving is not inferred from age. Until a ratified shelving protocol exists, the lifecycle record remains authoritative.",
        "",
        f"Snapshot SHA-256: `{snapshot['content_sha256']}`.",
    ]
    (ROOT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    output = ROOT / "snapshot.json"
    if output.exists():
        raise SystemExit("REFUSING: snapshot.json already exists")
    client = ainglish_client()
    queue = client.queue()

    dispute_rows = []
    metric_counts: Counter[str] = Counter()
    stage_counts: Counter[str] = Counter()
    scope_counts: Counter[str] = Counter()
    agreements_needed: Counter[int] = Counter()
    backfilled = 0
    preregistered = 0
    for item in queue["needs_dispute_settlement"]:
        item_scope = scope(item["stage"])
        stage_counts[item["stage"]] += 1
        scope_counts[item_scope] += 1
        originals = []
        for target in item["evidence_work"]["target_hashes"]:
            measurement = client.measurement(target)
            if measurement["settlement_state"] != "disputed" or measurement["is_replication"]:
                raise RuntimeError(f"{target}: queue target is not a disputed original")
            backfill = is_backfilled(measurement)
            backfilled += int(backfill)
            preregistered += int(not backfill)
            metric_counts[measurement["metric"]] += 1
            # The original claim itself occupies one side of the majority. Match the register's
            # ReplicationSettlement::agreementsNeeded rule exactly.
            needed = max(0, max(1, int(measurement["disagreement_count"])) - int(measurement["replication_count"]))
            agreements_needed[needed] += 1
            originals.append({
                "manifest_hash": target,
                "metric": measurement["metric"],
                "stance": measurement.get("stance"),
                "value": measurement.get("value"),
                "agreement_count": measurement["replication_count"],
                "disagreement_count": measurement["disagreement_count"],
                "agreements_needed": needed,
                "attempt_provenance": "backfilled" if backfill else "preregistered",
                "evidence_state": measurement["evidence_state"],
                "resolution_bound": measurement.get("resolution_bound"),
                "url": f"https://ainglish.org{measurement['url']}",
            })
        dispute_rows.append({
            "slug": item["slug"], "public_id": item["public_id"], "title": item["title"],
            "kind": item["kind"], "stage": item["stage"], "scope": item_scope,
            "proposal_url": f"https://ainglish.org{item['proposal_record']}", "originals": originals,
        })

    completion_rows = []
    for item in queue["needs_evidence_completion"]:
        work = item["evidence_work"] or {}
        completion_rows.append({
            "slug": item["slug"], "public_id": item["public_id"], "title": item["title"],
            "kind": item["kind"], "stage": item["stage"], "metric": work.get("metric"),
            "role": work.get("role"), "state": work.get("state"),
            "target_hashes": work.get("target_hashes") or [],
            "proposal_url": f"https://ainglish.org{item['proposal_record']}",
        })

    dispute_rows.sort(key=lambda row: (row["scope"], row["stage"], row["title"].casefold()))
    completion_rows.sort(key=lambda row: (row["title"].casefold(), row["slug"]))
    snapshot = {
        "kind": "dexagon.ainglish.decision-backlog-census.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "sources": ["/api/v1/queue", "/api/v1/measurements/{manifest_hash}"],
        "queue_population": queue.get("population"),
        "dispute_population": {
            "proposal_count": len(dispute_rows),
            "original_count": sum(len(row["originals"]) for row in dispute_rows),
            "by_scope": dict(sorted(scope_counts.items())), "by_stage": dict(sorted(stage_counts.items())),
            "by_metric": dict(sorted(metric_counts.items())),
            "agreements_needed_distribution": {str(key): agreements_needed[key] for key in sorted(agreements_needed)},
            "backfilled_originals": backfilled, "preregistered_originals": preregistered, "rows": dispute_rows,
        },
        "evidence_completion_population": {
            "proposal_count": len(completion_rows),
            "by_metric": dict(sorted(Counter(row["metric"] for row in completion_rows).items())),
            "by_state": dict(sorted(Counter(row["state"] for row in completion_rows).items())),
            "rows": completion_rows,
        },
        "claim_boundaries": [
            "A disputed original remains visible in every lifecycle scope.",
            "Only progressing disputes are proposal-progression work; ratified disputes are maintenance and terminal disputes are history.",
            "Current-system training and tokenizer asymmetry contextualises but does not reverse observed evidence.",
            "Age is an observation, not a lifecycle transition or shelving decision.",
        ],
        "model_calls": 0, "model_downloads": 0, "governance_writes": 0,
    }
    snapshot["content_sha256"] = hashlib.sha256(canonical(snapshot)).hexdigest()
    output.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_readme(snapshot)
    print(json.dumps({
        "captured_at": snapshot["captured_at"], "disputed_proposals": len(dispute_rows),
        "disputed_originals": snapshot["dispute_population"]["original_count"],
        "disputes_by_scope": snapshot["dispute_population"]["by_scope"],
        "evidence_completion": len(completion_rows), "content_sha256": snapshot["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
