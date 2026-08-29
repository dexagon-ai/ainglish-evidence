#!/usr/bin/env python3
"""Verify cap, membership, live evidence anchors, and non-withdrawal boundaries."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main() -> None:
    snapshot = json.loads((ROOT / "snapshot.json").read_text(encoding="utf-8"))
    decisions = json.loads((ROOT / "decisions.json").read_text(encoding="utf-8"))
    live = {row["slug"]: row for row in snapshot["rows"]}
    exits = {row["slug"] for row in decisions["exits"]}
    members = set(decisions["continuing"]) | {row["slug"] for row in decisions["admissions"]}
    assert len(members) == decisions["cohort_cap"] == decisions["cohort_size_after"] == 6
    assert exits.isdisjoint(members)
    assert set(live) == exits | members
    assert all(row["register_effect"] == "none" for row in decisions["exits"])
    assert live["some-or-all-some-but-not-all-does-some-leave-room-for-all-2"]["stage"] == "measured"
    assert live["whole-s-part-s-declare-whether-a-reported-set-is-the-complet"]["stage"] == "measured"
    assert live["it-ref"]["stage"] == "proposed"
    assert live["none-of-s-predicate-not-all-of-s-predicate"]["stage"] == "proposed"
    some_values = {row["manifest_hash"]: row["value"] for row in live["some-or-all-some-but-not-all-does-some-leave-room-for-all-2"]["measurements"] if row["metric"] == "comprehension_accuracy_delta"}
    assert 0.39 in some_values.values() and -48.15 in some_values.values()
    whole_values = {row["manifest_hash"]: row["value"] for row in live["whole-s-part-s-declare-whether-a-reported-set-is-the-complet"]["measurements"] if row["metric"] == "comprehension_accuracy_delta"}
    assert -19.44 in whole_values.values() and -24.7738 in whole_values.values()
    assert decisions["new_proposals_filed_by_this_transition"] == 0
    print(json.dumps({"status": "passed", "cohort_size": 6, "exits": sorted(exits), "members": sorted(members)}, indent=2))


if __name__ == "__main__":
    main()
