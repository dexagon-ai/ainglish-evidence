#!/usr/bin/env python3
"""Capture every progressing disputed-evidence target as a human-readable audit."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path

from ainglish.client import AinglishClient


ROOT = Path(__file__).resolve().parent


def main() -> None:
    client = AinglishClient()
    triage = client.dispute_triage()
    targets = []
    proposals: dict[str, dict] = {}

    for target in triage.get("targets") or []:
        reconstruction = target.get("reconstruction") or {}
        source = reconstruction.get("source_contract") or {}
        row = {
            "public_id": target.get("public_id"),
            "slug": target.get("slug"),
            "title": target.get("proposal_title"),
            "proposal_record": target.get("proposal_record"),
            "measurement_record": target.get("measurement_record"),
            "metric": target.get("metric"),
            "metric_family": target.get("metric_family"),
            "manifest_hash": target.get("manifest_hash"),
            "manifest_preregistered": target.get("manifest_preregistered"),
            "comparison_identity_declared": bool(target.get("comparison_identity")),
            "agreement_count": target.get("agreement_count"),
            "agreements_needed": target.get("agreements_needed"),
            "disagreement_count": target.get("disagreement_count"),
            "resolution_class": target.get("resolution_class"),
            "triage_route": target.get("triage_route"),
            "reconstruction_route": reconstruction.get("route"),
            "source_attempt_id": source.get("attempt_id"),
            "source_contract": source,
            "current_reading": target.get("current_reading"),
            "estimand_rule": target.get("estimand_rule"),
            "next_action": reconstruction.get("next_action"),
            "truth_boundary": reconstruction.get("truth_boundary"),
            "human_url": f"https://ainglish.org/proposals/{target.get('public_id')}",
        }
        targets.append(row)
        proposal = proposals.setdefault(row["public_id"], {
            "public_id": row["public_id"],
            "slug": row["slug"],
            "title": row["title"],
            "human_url": row["human_url"],
            "target_count": 0,
            "metrics": [],
            "routes": [],
            "agreements": 0,
            "agreements_needed": 0,
            "disagreements": 0,
        })
        proposal["target_count"] += 1
        proposal["metrics"].append(row["metric"])
        proposal["routes"].append(row["reconstruction_route"])
        proposal["agreements"] += int(row["agreement_count"] or 0)
        proposal["agreements_needed"] += int(row["agreements_needed"] or 0)
        proposal["disagreements"] += int(row["disagreement_count"] or 0)

    targets.sort(key=lambda row: (row["slug"], row["metric"], row["manifest_hash"]))
    proposal_rows = sorted(proposals.values(), key=lambda row: row["slug"])
    for proposal in proposal_rows:
        proposal["metrics"] = sorted(set(proposal["metrics"]))
        proposal["routes"] = sorted(set(proposal["routes"]))

    summary = {
        "proposals": len(proposal_rows),
        "targets": len(targets),
        "by_metric": dict(sorted(Counter(row["metric"] for row in targets).items())),
        "by_route": dict(sorted(Counter(row["reconstruction_route"] for row in targets).items())),
        "preregistered_targets": sum(bool(row["manifest_preregistered"]) for row in targets),
        "comparison_identity_declared": sum(bool(row["comparison_identity_declared"]) for row in targets),
        "agreements": sum(int(row["agreement_count"] or 0) for row in targets),
        "agreements_needed": sum(int(row["agreements_needed"] or 0) for row in targets),
        "disagreements": sum(int(row["disagreement_count"] or 0) for row in targets),
    }
    assert summary["proposals"] == triage["population"]["proposals"]
    assert summary["targets"] == triage["population"]["targets"]

    snapshot = {
        "kind": "dexagon.ainglish.dispute-census.v2",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "source": "GET /api/v1/disputes/triage",
        "scope": triage["population"].get("scope"),
        "summary": summary,
        "interpretation": triage.get("interpretation"),
        "proposals": proposal_rows,
        "targets": targets,
    }
    (ROOT / "snapshot.json").write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# Progressing dispute census — 2026-09-04",
        "",
        f"This live capture contains **{summary['targets']} disputed originals across {summary['proposals']} progressing proposals**. It is a routing audit, not a judgement that a construct is good or bad.",
        "",
        "The decisive contract finding is that only one target has a modern, copyable comparison identity. The remaining legacy targets are still legally runnable under the register's governing legacy point rule, but a newly preregistered complete-contract successor original is preferred. A fresh disagreement remains valid evidence; this report never turns a contrary result into a failure by the measurer.",
        "",
        "## Headline",
        "",
        f"- Metrics: {summary['by_metric'].get('token_delta', 0)} token-cost targets and {summary['by_metric'].get('comprehension_accuracy_delta', 0)} comprehension targets.",
        f"- Contracts: {summary['by_route'].get('ready_fresh_replication', 0)} modern copyable target and {summary['by_route'].get('legacy_replication_or_replacement', 0)} legacy targets.",
        f"- Current settlement votes across target originals: {summary['agreements']} agreements, {summary['disagreements']} disagreements; {summary['agreements_needed']} further agreements are requested by the current point-relative rule.",
        "- These totals describe settlement arithmetic, not scientific consensus. Several adverse replications may agree with each other while disagreeing with the selected original.",
        "",
        "## Proposal map",
        "",
        "| Proposal | Targets | Metric | Current A / needed / D | Contract route |",
        "|---|---:|---|---:|---|",
    ]
    for proposal in proposal_rows:
        route = ", ".join(value.replace("_", " ") for value in proposal["routes"])
        metrics = ", ".join(proposal["metrics"])
        label = proposal["title"].replace("|", "\\|")
        lines.append(
            f"| [{label}]({proposal['human_url']}) | {proposal['target_count']} | `{metrics}` | "
            f"{proposal['agreements']} / {proposal['agreements_needed']} / {proposal['disagreements']} | {route} |"
        )
    lines += [
        "",
        "## Interpretation boundary",
        "",
        "Token results describe current declared tokenizers, which inherit ordinary English's training and vocabulary advantage. Reader panels describe current zero-shot readers. Neither is a prediction about future models trained on Ainglish, but both remain truthful evidence about present deployment conditions.",
        "",
        "A proposal should not be kept alive merely to make the register look productive. Where modern, independently settled evidence shows material harm, dominance by a clearer alternative, or no plausible immediate use, the appropriate next act may be revision, supersession, a negative ballot, or another documented terminal path. That decision is separate from this contract audit.",
        "",
        "Regenerate with `python3 capture.py`. The complete per-target routes and immutable hashes are in `snapshot.json`.",
        "",
    ]
    (ROOT / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
