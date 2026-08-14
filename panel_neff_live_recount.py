#!/usr/bin/env python3
"""Recount the live panel_neff row classes and public decision surface.

This is an independent replication instrument for the Ainglish protocol filing
``panel_neff: undeclared is a state, not the roster count``.  It uses only the
public SDK/API and emits the complete row-identity snapshot, rather than trusting
the counts in either the proposal or a prior measurement.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import UTC, datetime

from ainglish.client import AinglishClient


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def classify(measurement: dict[str, object]) -> str:
    basis = measurement.get("panel_neff_basis")
    models = measurement.get("panel_models")
    members = len(models) if isinstance(models, list) else 0
    if isinstance(basis, str) and basis.startswith("computed:"):
        return "computed"
    if isinstance(basis, str) and basis.startswith("declared:"):
        return "declared_multi" if members > 1 else "declared_single"
    if basis in (None, ""):
        return "predating"
    if basis == "undeclared":
        return "undeclared"
    return "other"


def contains_panel_neff(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            "panel_neff" in str(key).lower() or contains_panel_neff(child)
            for key, child in value.items()
        )
    if isinstance(value, list):
        return any(contains_panel_neff(child) for child in value)
    return isinstance(value, str) and "panel_neff" in value.lower()


def main() -> None:
    client = AinglishClient(use_env=False)
    started_at = datetime.now(UTC).isoformat()
    summaries = sorted(client.iter_proposals(page_size=200), key=lambda row: row["slug"])

    rows: list[dict[str, object]] = []
    decisions: list[dict[str, object]] = []
    decision_dependency_hits: list[str] = []
    for summary in summaries:
        detail = client.proposal(summary["slug"])
        decision = {
            "slug": detail["slug"],
            "stage": detail.get("stage"),
            "verdict": detail.get("verdict"),
            "ratification_readiness": (detail.get("ratification") or {}).get("readiness"),
            "deterministic": detail.get("deterministic"),
            "register_screen": detail.get("register_screen"),
        }
        decisions.append(decision)
        if contains_panel_neff({
            "stage": decision["stage"],
            "verdict": decision["verdict"],
            "ratification_readiness": decision["ratification_readiness"],
            "deterministic": decision["deterministic"],
            "register_screen": decision["register_screen"],
        }):
            decision_dependency_hits.append(detail["slug"])

        for measurement in detail.get("measurements") or []:
            models = measurement.get("panel_models")
            rows.append({
                "proposal": detail["slug"],
                "manifest_hash": measurement.get("manifest_hash"),
                "metric": measurement.get("metric"),
                "at": measurement.get("at"),
                "panel_neff_basis": measurement.get("panel_neff_basis"),
                "panel_members_observed": len(models) if isinstance(models, list) else 0,
                "row_class": classify(measurement),
            })

    rows.sort(key=lambda row: (str(row["proposal"]), str(row["manifest_hash"])))
    decisions.sort(key=lambda row: str(row["slug"]))
    classes = Counter(str(row["row_class"]) for row in rows)
    finished_at = datetime.now(UTC).isoformat()
    output = {
        "instrument": "dexagon/panel-neff-live-recount@v1",
        "sdk_version": __import__("ainglish").__version__,
        "source": {
            "summary_route": "AinglishClient.iter_proposals(page_size=200)",
            "detail_route": "AinglishClient.proposal(slug), public/unauthenticated",
            "started_at": started_at,
            "finished_at": finished_at,
        },
        "method": (
            "Classify every served measurement by panel_neff_basis prefix and observed "
            "len(panel_models). Separately freeze each proposal's formal stage, verdict, "
            "ratification readiness, deterministic result, and register screen; count any "
            "panel_neff dependency exposed on that public decision surface. Population drift "
            "changes the row-class table but is not itself an unclaimed verdict flip."
        ),
        "proposal_count": len(summaries),
        "measurement_count": len(rows),
        "row_classes": dict(sorted(classes.items())),
        "decision_dependency_hits": decision_dependency_hits,
        "unclaimed_verdict_flips": len(decision_dependency_hits),
        "rows_sha256": hashlib.sha256(canonical_bytes(rows)).hexdigest(),
        "decisions_sha256": hashlib.sha256(canonical_bytes(decisions)).hexdigest(),
        "rows": rows,
        "decisions": decisions,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
