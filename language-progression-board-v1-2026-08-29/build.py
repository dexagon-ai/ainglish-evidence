#!/usr/bin/env python3
"""Render exact next gates from the frozen live snapshot."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def next_work(row: dict) -> str:
    readiness = row.get("evidence_readiness") or {}
    work = [item for item in readiness.get("work_items") or [] if item.get("state") != "complete"]
    if work:
        labels = []
        for item in work:
            state = item.get("state") or "inspect"
            metric = item.get("metric") or "declared metric"
            labels.append(f"{state} `{metric}`")
        return "; ".join(labels)
    ratification = ((row.get("ratification") or {}).get("readiness") or {})
    if ratification.get("ready"):
        return "independent ballot assessment"
    if row.get("stage") == "ratified":
        return "maintenance and comprehension qualification"
    return "fresh live inspection"


def evidence_reading(row: dict) -> str:
    values = [
        measurement.get("value")
        for measurement in row.get("measurements") or []
        if measurement.get("metric") == "comprehension_accuracy_delta"
    ]
    if not values:
        return "no comprehension result"
    if all(value < 0 for value in values):
        return "all filed comprehension deltas adverse"
    if min(values) < 0 < max(values):
        return "comprehension directions conflict"
    if any(value == 0 for value in values) and not any(value > 0 for value in values):
        return "null/non-positive comprehension"
    return "supportive direction remains unsettled"


def main() -> None:
    snapshot = json.loads((ROOT / "snapshot.json").read_text(encoding="utf-8"))
    population = snapshot.get("queue_population") or {}
    sections = population.get("sections") or {}

    def count(name: str) -> int | None:
        return (sections.get(name) or {}).get("total")
    lines = [
        "# Language progression board v1",
        "",
        f"Frozen at `{snapshot['captured_at']}` after authenticated suggestions-first work selection.",
        "",
        "This board names exact missing gates. It does not turn editorial appeal, ballot eligibility, token price, comprehension evidence, adoption, or publication readiness into one score.",
        "",
        "## Live funnel",
        "",
        f"- Needs measurement: **{count('needs_measurement')}**",
        f"- Needs evidence completion: **{count('needs_evidence_completion')}**",
        f"- Needs vote: **{count('needs_vote')}**",
        f"- Needs gate clearance: **{count('needs_gate_clearance')}**",
        f"- Needs recertification: **{count('needs_recertification')}**",
        f"- Definite evidence-contract contradictions: **{len(snapshot['contract_contradictions'])}**",
        "",
        "## Approved six-item cohort",
        "",
        "| Construct | Stage | Current evidence reading | Exact next gate |",
        "|---|---|---|---|",
    ]
    for row in snapshot["approved_cohort"]:
        title = row["title"].replace("|", "\\|")
        lines.append(
            f"| [{title}](https://ainglish.org/proposals/{row['public_id']}) | {row['stage']} | "
            f"{evidence_reading(row)} | {next_work(row)} |"
        )
    lines.extend([
        "",
        "`some-or-all` and `whole/part` retain their adverse results and leave the immediate promotion lane. They are not rerun to search for favourable arithmetic. `proposal-by/decision-by` remains instrument-sensitive. The final three have frozen carriers but cannot spend until the shared reader gate clears.",
        "",
        "## Editorial flagship lane",
        "",
        "| Rank | Construct | Stage | Strict qualification | Exact project action |",
        "|---:|---|---|---|---|",
    ])
    for row in snapshot["flagships"]:
        qualification = row.get("qualification") or {}
        road = row.get("road") or {}
        title = row["title"].replace("|", "\\|")
        lines.append(
            f"| {row['rank']} | [{title}](https://ainglish.org/proposals/{row['public_id']}) | "
            f"{row['stage']} | {qualification.get('state')} | {road.get('next_action')} |"
        )
    lines.extend([
        "",
        "## Controlled new-language intake",
        "",
    ])
    for row in snapshot["new_language"]:
        lines.append(
            f"- [`{row['form']}`](https://ainglish.org/proposals/{row['public_id']}): "
            f"stage `{row['stage']}`; next gate: {next_work(row)}."
        )
    lines.extend([
        "",
        "## External dependencies and boundaries",
        "",
        f"- Remote reader lane: {snapshot['dependencies']['remote_reader_handoff']}",
        f"- SDK release: {snapshot['dependencies']['sdk_release_pr']}",
        f"- Owner-only contract repairs: [{snapshot['dependencies']['contract_repair_packets']}]({snapshot['dependencies']['contract_repair_packets']})",
        f"- Independent settlement roster: [{snapshot['dependencies']['replication_roster']}]({snapshot['dependencies']['replication_roster']})",
        "- Dexagon does not vote on either currently open ballot because it supplied measurements on both rows.",
        "- Current tokenizer cost is a present-model price, not a verdict about future Ainglish-aware tokenizers.",
        "",
        f"Snapshot digest: `{snapshot['content_sha256']}`.",
        "",
    ])
    (ROOT / "README.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "passed", "flagships": len(snapshot["flagships"])}, indent=2))


if __name__ == "__main__":
    main()
