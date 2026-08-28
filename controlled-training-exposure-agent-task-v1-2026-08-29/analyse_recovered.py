#!/usr/bin/env python3
"""Mechanically bridge invalid-repair encoding to the frozen benchmark scorer."""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import statistics
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
FROZEN_ANALYSIS = ROOT / "analyse.py"


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def load_module():
    spec = importlib.util.spec_from_file_location("frozen_exposure_analysis", FROZEN_ANALYSIS)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import frozen analyse.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def usage_total(decision: dict[str, Any] | None) -> int | None:
    if decision is None:
        return 0
    values = (decision.get("input_tokens"), decision.get("output_tokens"))
    if not all(isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0 for value in values):
        return None
    return int(sum(values))


def raw_token_summaries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, str], list[int | None]] = defaultdict(list)
    for row in rows:
        first = usage_total(row.get("first"))
        repair = usage_total(row.get("repair"))
        total = None if first is None or repair is None else first + repair
        groups[(row["condition"], row["track"], row["arm"], row["exposure_class"])].append(total)
    output = []
    for (condition, track, arm, exposure), values in sorted(groups.items()):
        complete = [value for value in values if value is not None]
        output.append({
            "condition": condition, "track": track, "arm": arm, "exposure_class": exposure,
            "coverage": len(complete), "denominator": len(values),
            "mean_complete_raw_interaction_tokens": round(statistics.fmean(complete), 4) if complete else None,
            "median_complete_raw_interaction_tokens": round(statistics.median(complete), 4) if complete else None,
            "meaning": "Includes every stored first and repair call, including invalid repair continuations.",
        })
    return output


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: analyse_recovered.py results/responses.jsonl")
    source_path = Path(sys.argv[1]).resolve()
    target = ROOT / "analysis.json"
    if target.exists():
        raise SystemExit("REFUSING: analysis.json already exists")
    rows = [json.loads(line) for line in source_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    recovered = []
    cases = []
    for row in rows:
        view = json.loads(json.dumps(row))
        repair = view.get("repair")
        if repair is not None and repair.get("decision") != "act":
            if view.get("first", {}).get("decision") != "clarify" or repair.get("decision") != "invalid":
                raise SystemExit(f"REFUSING: unexpected non-action repair at {view.get('condition')} {view.get('cell_id')}")
            cases.append({
                "condition": view["condition"], "cell_id": view["cell_id"], "item_id": view["item_id"],
                "track": view["track"], "arm": view["arm"], "stored_repair_decision": "invalid",
                "repair_input_tokens": repair.get("input_tokens"), "repair_output_tokens": repair.get("output_tokens"),
                "repair_error": view.get("repair_error"),
            })
            view["repair"] = None
        recovered.append(view)
    if len(cases) != 24 or Counter(case["condition"] for case in cases) != {"base": 12, "adapter": 12}:
        raise SystemExit(f"REFUSING: expected matched 12+12 recovery cases, got {Counter(case['condition'] for case in cases)}")
    base_cells = {case["cell_id"] for case in cases if case["condition"] == "base"}
    adapter_cells = {case["cell_id"] for case in cases if case["condition"] == "adapter"}
    if base_cells != adapter_cells:
        raise SystemExit("REFUSING: invalid-repair locations are not matched across conditions")

    module = load_module()
    with tempfile.NamedTemporaryFile("wb", suffix=".jsonl", delete=False) as handle:
        temporary = Path(handle.name)
        for row in recovered:
            handle.write(canonical(row))
    try:
        previous = sys.argv
        sys.argv = [str(FROZEN_ANALYSIS), str(temporary)]
        with contextlib.redirect_stdout(io.StringIO()):
            module.main()
        sys.argv = previous
    finally:
        temporary.unlink(missing_ok=True)
    analysis = json.loads(target.read_text(encoding="utf-8"))
    analysis.pop("content_sha256", None)
    analysis["schema"] = "ainglish.controlled-training-exposure-analysis.v1.1-recovered"
    analysis["responses_sha256"] = hashlib.sha256(source_path.read_bytes()).hexdigest()
    analysis["analysis_recovery"] = {
        "reason": "Frozen runner retained invalid repair objects; frozen benchmark scorer accepts only act or null repairs.",
        "mapping": "For scoring only, stored invalid repair -> null repair. Raw responses remain unchanged.",
        "case_count": len(cases),
        "by_condition": dict(Counter(case["condition"] for case in cases)),
        "matched_cell_locations": sorted(base_cells),
        "cases": cases,
        "success_effect": "none possible: every mapped repair was already non-action and therefore unsuccessful",
        "standard_token_fields_valid": False,
        "standard_token_warning": "Frozen scorer token summaries omit mapped invalid-repair calls; do not use them for token claims.",
        "raw_interaction_token_summaries": raw_token_summaries(rows),
        "post_result_addition": True,
    }
    analysis["claim_limits"].append(
        "The frozen scorer's token contrasts omit 24 invalid repair continuations; use only analysis_recovery.raw_interaction_token_summaries for complete descriptive token totals."
    )
    analysis["content_sha256"] = hashlib.sha256(canonical(analysis)).hexdigest()
    target.write_text(json.dumps(analysis, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    primary = [row for row in analysis["adapter_minus_base"] if row["arm"] == "ainglish"]
    print(json.dumps({
        "ok": True, "observations": analysis["observations"], "recovered_invalid_repairs": len(cases),
        "matched_locations": len(base_cells), "primary_success_contrasts": primary,
        "standard_token_fields_valid": False, "content_sha256": analysis["content_sha256"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
