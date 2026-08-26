#!/usr/bin/env python3
"""Derive the terminal v8 roster decision from the two immutable holdout results."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from build_development_plans import canonical, checked


ROOT = Path(__file__).resolve().parent


def main() -> None:
    index = checked(ROOT / "holdout-index.json")
    decisions = []
    for short in ("phi", "qwen"):
        plan = checked(ROOT / f"holdout-{short}-plan.json")
        result = checked(ROOT / f"holdout-{short}-result.json")
        observed = result["semantic"]["observed"]
        gate = plan["semantic_stage"]["gate"]
        qualified = (
            result["format"]["passed"]
            and observed["valid_json_cells"] == gate["valid_json_cells_required"]
            and observed["schema_exact_cells"] == gate["schema_exact_cells_required"]
            and observed["correct_cells"] >= gate["correct_cells_required"]
            and all(value >= gate["correct_per_axis_required"] for value in observed["correct_by_axis"].values())
            and observed["thinking_bytes"] == 0
            and observed["fault_cells"] == 0
        )
        if result["v8_holdout_eligible"] != qualified:
            raise SystemExit("REFUSING: result qualification projection drift")
        decisions.append({
            "lineage": plan["candidate"]["lineage"],
            "model": plan["candidate"]["source_model"],
            "model_digest": plan["candidate"]["source_manifest_sha256"],
            "plan_sha256": plan["content_sha256"],
            "result_sha256": result["content_sha256"],
            "observed": observed,
            "qualified": qualified,
        })
    qualified = [row for row in decisions if row["qualified"]]
    roster_ready = len(qualified) >= index["selection_rule"]["minimum_qualified_lineages"]
    document = {
        "kind": "ainglish.panel.reader-qualification-selected-result.v8",
        "evidentiary_status": "instrument qualification only; never proposal evidence",
        "holdout_sha256": index["holdout"]["content_sha256"],
        "selection_rule": index["selection_rule"],
        "qualification": decisions,
        "roster_ready": roster_ready,
        "fixed_roster": qualified if roster_ready else [],
        "no_roster_action": index["no_roster_action"],
    }
    document["content_sha256"] = hashlib.sha256(canonical(document)).hexdigest()
    target = ROOT / "selected-result.json"
    if target.exists():
        if checked(target) != document:
            raise SystemExit("REFUSING: selected result drift")
    else:
        target.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(document, indent=2))


if __name__ == "__main__":
    main()

