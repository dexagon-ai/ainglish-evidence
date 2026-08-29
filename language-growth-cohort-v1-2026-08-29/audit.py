#!/usr/bin/env python3
"""Fail-closed structural audit for the six-entry cohort plan."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main() -> None:
    plan = json.loads((ROOT / "plan.json").read_text())
    snapshot = json.loads((ROOT / "snapshot.json").read_text())
    entries = plan["entries"]

    assert plan["cohort_cap"] == 6
    assert len(entries) == plan["cohort_cap"]
    slugs = [row["slug"] for row in entries]
    assert len(slugs) == len(set(slugs))
    assert set(slugs) == {row["slug"] for row in snapshot["entries"]}
    assert sum(plan["allocation"].values()) == 100
    assert plan["model_calls"] == 0 and plan["governance_writes"] == 0
    assert snapshot["model_calls"] == 0 and snapshot["governance_writes"] == 0

    for row in entries:
        assert row["editorial_score"] in {4, 5}
        assert row["lane"]
        assert row["next_gate"]
        assert row["stop_rule"]
        for artifact in row["zero_shot_artifacts"]:
            assert (ROOT / artifact).exists(), artifact
        learnability = row["learnability_artifact"]
        assert (ROOT / learnability).exists(), learnability

    policy = plan["evidence_policy"]
    assert "Never use" in policy["definition_conditioned"]
    assert "wholly fresh" in policy["replication"]
    assert "never a comprehension measurement" in policy["human_boundary"]
    print("audit ok: six unique entries, artifacts present, evidence boundaries retained")


if __name__ == "__main__":
    main()
