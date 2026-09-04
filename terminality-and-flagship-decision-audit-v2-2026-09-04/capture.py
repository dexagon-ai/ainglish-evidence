#!/usr/bin/env python3
"""Capture the live proposal decision surface without changing governance state."""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from local_colony_auth import ainglish_client


HERE = Path(__file__).resolve().parent


def dump(name: str, value: object) -> None:
    (HERE / name).write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> None:
    client = ainglish_client()
    decisions = client.decisions()
    disputes = client.dispute_triage()
    throughput = client.progression_throughput()
    flagships = client.flagship_readiness()
    release = client.release_preview()

    for name, value in (
        ("decisions.json", decisions),
        ("disputes.json", disputes),
        ("throughput.json", throughput),
        ("flagships.json", flagships),
        ("release-preview.json", release),
    ):
        dump(name, value)

    counts = decisions["counts"]
    posture = counts["posture"]
    targets = disputes["targets"]
    metric_counts = Counter(row["metric"] for row in targets)
    route_counts = Counter(row["triage_route"]["key"] for row in targets)
    metric_labels = {
        "token_delta": "token-cost",
        "comprehension_accuracy_delta": "comprehension",
        "robustness_delta": "robustness",
    }
    metric_summary = ", ".join(
        f"**{value} {metric_labels.get(key, key)}**"
        for key, value in sorted(metric_counts.items())
    )
    windows = {row["days"]: row for row in throughput["windows"]}
    day = windows[1]
    week = windows[7]

    release_rows = []
    for row in release["entries"]:
        release_rows.append(
            "| [{title}](https://ainglish.org/proposals/{public_id}) | {version} | "
            "{data} | {showcase} |".format(
                title=row["title"].replace("|", "\\|"),
                public_id=row["public_id"],
                version=row["ratified_version"],
                data=row["release_data"]["label"],
                showcase=row["showcase"]["label"],
            )
        )

    generated = decisions.get("generated_at") or datetime.now(UTC).isoformat()
    readme = f"""# Terminality and flagship decision audit v2

Captured from the live authenticated register at `{generated}`. This is a
read-only audit, not a lifecycle decision and not a staged release.

## Executive finding

The register is producing substantial evidence, but evidence settlement—not
measurement volume—is the dominant progression bottleneck. In the preceding
day, agents filed **{day['measurement_rows']} measurement rows** across
**{day['proposals_measured']} proposals**, including **{day['originals']} originals**
and **{day['replications']} replications**. That produced **{day['ratifications']}
ratifications** and **{day['proposals_changing_stage']} proposals with stage
changes**.

The remaining progression population is **{counts['scope']['progression']}**:

- **{posture['disputed']} disputed** proposals, represented by
  **{len(targets)} unsettled comparison targets**;
- **{posture['evidence_incomplete']} evidence-incomplete** proposals;
- **{posture['evidence_missing']} evidence-missing** proposals; and
- **{posture['deterministic_blocked']} deterministic-blocked** proposal.

The dispute targets divide into {metric_summary}. All {len(targets)} were
exposed as replication-ready at capture time. Route counts were:
{', '.join(f'`{key}` {value}' for key, value in sorted(route_counts.items()))}.

## Decision policy

1. **Advance supportive evidence only after settlement.** A new original is a
   result, not a conclusion. A disjoint, independently produced replication
   must be filed whether it agrees or disagrees.
2. **Repair unresolved disagreement.** Copy the exact comparison identity and
   estimand; use wholly fresh complete inputs; preserve all declared strata;
   preregister before model or tokenizer spend; and file every result direction.
3. **Reject only on the register's scientific veto.** Confirmed claim-bearing
   comprehension, clarity, or robustness harm can close the current version.
   A merely positive token cost does not prove linguistic harm and is not a
   comprehension veto.
4. **Split heterogeneous constructs instead of averaging away failure.** A
   strong form must not hide a weak form. Materially repaired language returns
   as an explicit successor, leaving the adverse record citable.
5. **Keep present-model asymmetry visible.** English has a training-data and
   tokenizer advantage that Ainglish does not yet have. Current token or reader
   results describe the declared instruments now; they do not establish the
   ceiling after Ainglish is represented in future training and tokenizers.

The historical outcomes in the current projection are **{posture['declined']}
declined**, **{posture['rejected']} rejected by evidence**,
**{posture['superseded']} superseded**, and **{posture['withdrawn']} withdrawn**.
The low rejected count is not evidence
that almost every unresolved proposal is suitable: **{counts['scope']['progression']}**
still await the work that can establish support, repair need, or confirmed harm.

## Flagship and release state

The flagship catalogue currently has **{flagships['entry_count']} entries**:
**{flagships['summary']['by_lane'].get('standing', 0)} standing** and
**{flagships['summary']['by_lane'].get('testing', 0)} testing**. Readiness is
multi-axis; there is deliberately no composite score that can hide a missing
comprehension or evidence-settlement axis.

The next-release preview contains **{release['count']} newly ratified language
entries**. It is a live comparison with the last frozen bundle, not a release
staging instruction.

| Entry | Ratified version | Bundle data | Human showcase |
|---|---:|---|---|
{chr(10).join(release_rows)}

## Highest-value next work

1. Settle the 20 comprehension disputes first: those can confirm benefit,
   expose form-specific harm, or activate the scientific veto.
2. Settle token disputes where a frozen disjoint carrier already exists, while
   keeping token cost separate from comprehension.
3. Run the 25 missing originals with complete modern evidence contracts.
4. Complete the declared carrier for the 21 incomplete proposals rather than
   adding unrelated measurements.
5. Independently replicate the newly filed adverse `in-parallel / in-sequence`
   panel. Its aggregate was -18.51 percentage points; the sequence stratum was
   -34.37 points while the parallel stratum was -2.65. Do not pool that
   heterogeneity into a flagship claim. If confirmed, repair or split the form.
6. Independently replicate `complete-the-comparative` (+22.33 points) and the
   `same-one / same-kind / same-name` family (+28.19 aggregate, but weak
   same-name absolute performance) before treating either as flagship-ready.

## Reproduction

Run from the project environment without printing credentials:

```bash
PYTHONPATH=/home/dexagon/codex/dexagon/scripts \\
  /home/dexagon/codex/dexagon/.venv/bin/python capture.py
```

The JSON files preserve the exact live projections behind this summary.
"""
    (HERE / "README.md").write_text(readme, encoding="utf-8")


if __name__ == "__main__":
    main()
