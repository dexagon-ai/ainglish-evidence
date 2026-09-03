#!/usr/bin/env python3
"""Classify a frozen dispute census without making governance or model calls."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    snapshot = json.loads((ROOT / "snapshot.json").read_text(encoding="utf-8"))
    me = snapshot["principal"]["sub"]
    output = []
    for row in snapshot["rows"]:
        routed = []
        for target in row["targets"]:
            own_target = (target.get("submitter") or {}).get("sub") == me
            already_spoke = any(
                item.get("is_replication") and item.get("replicates_hash") == target["manifest_hash"]
                for item in row["my_measurements"]
            )
            declared = isinstance(target.get("estimand_contract"), dict)
            identity = isinstance(target.get("comparison_identity"), dict)
            metric = target.get("metric")
            if own_target or already_spoke:
                route = "independent_principal_required"
            elif not target.get("manifest_served") or not declared:
                route = "original_author_contract_repair"
            elif metric == "token_delta" and not identity:
                route = "original_author_comparison_identity_repair"
            elif metric in {"comprehension_accuracy_delta", "interpretation_entropy_delta", "tag_fidelity"}:
                route = "qualified_reader_gate_required"
            elif metric == "token_delta":
                route = "dexagon_deterministic_replication_candidate"
            else:
                route = "instrument_specific_review"
            routed.append({**target, "route": route})
        output.append({**{k: row[k] for k in ("slug", "public_id", "title", "stage", "thread", "metric")},
                       "targets": routed})
    counts = Counter(target["route"] for row in output for target in row["targets"])
    result = {
        "kind": "dexagon.ainglish.dispute-triage.v1",
        "source_sha256": snapshot["content_sha256"],
        "reader_gate": "closed_pending_two_distinct_base_model_lineages_on_one_common_holdout",
        "sdk_constraint": "0.2.51 requires a structured estimand declaration for every new token run",
        "routes": dict(sorted(counts.items())),
        "rows": output,
        "interpretation": {
            "author_repair": "Do not mint a modern replication against an undeclared legacy target: one-sided declaration is held and cannot settle.",
            "independence": "A principal that authored the original or already supplied its replication cannot add another settlement voice.",
            "reader_gate": "Do not spend scientific reader calls until two distinct lineages qualify on one common construct-free holdout.",
            "deterministic": "Only modern, identity-pinned token targets are immediately executable by Dexagon, after a fresh live re-read.",
        },
        "model_calls": 0,
        "governance_writes": 0,
    }
    result["content_sha256"] = hashlib.sha256(canonical(result)).hexdigest()
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    target = ROOT / "triage.json"
    if target.exists() and target.read_text(encoding="utf-8") != rendered:
        raise SystemExit("REFUSING: triage drift")
    if not target.exists():
        target.write_text(rendered, encoding="utf-8")
    print(json.dumps({"rows": len(output), "targets": sum(counts.values()),
                      "routes": dict(sorted(counts.items())),
                      "content_sha256": result["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
