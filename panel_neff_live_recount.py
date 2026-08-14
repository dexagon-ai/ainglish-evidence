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


def panel_neff_paths(value: object, prefix: str = "") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if "panel_neff" in str(key).lower():
                hits.append(path)
            hits.extend(panel_neff_paths(child, path))
        return hits
    if isinstance(value, list):
        for index, child in enumerate(value):
            hits.extend(panel_neff_paths(child, f"{prefix}[{index}]"))
        return hits
    if isinstance(value, str) and "panel_neff" in value.lower():
        hits.append(prefix)
    return hits


def main() -> None:
    client = AinglishClient(use_env=False)
    started_at = datetime.now(UTC).isoformat()
    summaries = sorted(client.iter_proposals(page_size=200), key=lambda row: row["slug"])

    served_rows: list[dict[str, object]] = []
    decisions: list[dict[str, object]] = []
    decision_dependency_hits: list[str] = []
    for summary in summaries:
        detail = client.proposal(summary["slug"])
        full_decision = {
            "slug": detail["slug"],
            "stage": detail.get("stage"),
            "verdict": detail.get("verdict"),
            "ratification_readiness": (detail.get("ratification") or {}).get("readiness"),
            "deterministic": detail.get("deterministic"),
            "register_screen": detail.get("register_screen"),
        }
        dependency_paths = panel_neff_paths(full_decision)
        deterministic = detail.get("deterministic") or {}
        protocol_screen = deterministic.get("protocol_screen") or {}
        register_screen = detail.get("register_screen") or {}
        verdict = detail.get("verdict") or {}
        readiness = (detail.get("ratification") or {}).get("readiness") or {}
        decision = {
            "slug": detail["slug"],
            "stage": detail.get("stage"),
            "verdict_assessment": verdict.get("assessment"),
            "verdict_confirmed_count": verdict.get("confirmed_count"),
            "verdict_effective_count": verdict.get("effective_count"),
            "verdict_unresolved_count": verdict.get("unresolved_count"),
            "ratification_ready": readiness.get("ready"),
            "ratification_status": readiness.get("status"),
            "ratification_blocker": readiness.get("blocker"),
            "deterministic_declared": deterministic.get("declared"),
            "deterministic_protocol": deterministic.get("protocol"),
            "deterministic_ratifiable": deterministic.get("ratifiable"),
            "protocol_well_formed": protocol_screen.get("well_formed"),
            "register_screen_declared": register_screen.get("declared"),
            "register_screen_blocking_count": register_screen.get("blocking_count"),
            "panel_neff_dependency_paths": dependency_paths,
        }
        decisions.append(decision)
        if dependency_paths:
            decision_dependency_hits.append(detail["slug"])

        for measurement in detail.get("measurements") or []:
            models = measurement.get("panel_models")
            served_rows.append({
                "proposal": detail["slug"],
                "manifest_hash": measurement.get("manifest_hash"),
                "metric": measurement.get("metric"),
                "at": measurement.get("at"),
                "panel_neff_basis": measurement.get("panel_neff_basis"),
                "panel_members_observed": len(models) if isinstance(models, list) else 0,
                "row_class": classify(measurement),
            })

    served_rows.sort(key=lambda row: (
        str(row["proposal"]), str(row["manifest_hash"]), str(row["at"])
    ))
    grouped: dict[tuple[str, str], list[dict[str, object]]] = {}
    for row in served_rows:
        identity = (str(row["proposal"]), str(row["manifest_hash"]))
        grouped.setdefault(identity, []).append(row)

    rows: list[dict[str, object]] = []
    duplicate_references: list[dict[str, object]] = []
    for identity, references in sorted(grouped.items()):
        first = dict(references[0])
        first["served_reference_count"] = len(references)
        first["served_at_values"] = sorted({str(row["at"]) for row in references})
        first.pop("at", None)
        rows.append(first)
        if len(references) > 1:
            duplicate_references.append({
                "proposal": identity[0],
                "manifest_hash": identity[1],
                "references": references,
            })

    decisions.sort(key=lambda row: str(row["slug"]))
    classes = Counter(str(row["row_class"]) for row in rows)
    finished_at = datetime.now(UTC).isoformat()
    output = {
        "instrument": "dexagon/panel-neff-live-recount@v4",
        "sdk_version": __import__("ainglish").__version__,
        "source": {
            "summary_route": "AinglishClient.iter_proposals(page_size=200)",
            "detail_route": "AinglishClient.proposal(slug), public/unauthenticated",
            "started_at": started_at,
            "finished_at": finished_at,
        },
        "method": (
            "Classify every served measurement by panel_neff_basis prefix and observed "
            "len(panel_models), identifying a measurement by (proposal slug, manifest_hash) "
            "and publishing duplicate served references rather than counting them twice. "
            "Separately freeze each proposal's formal stage, verdict, "
            "ratification readiness, deterministic result, and register screen; count any "
            "panel_neff dependency exposed on that public decision surface. Population drift "
            "changes the row-class table but is not itself an unclaimed verdict flip."
        ),
        "proposal_count": len(summaries),
        "served_measurement_references": len(served_rows),
        "measurement_count": len(rows),
        "measurement_identity": "(proposal slug, manifest_hash); duplicate served references count once",
        "duplicate_measurement_references": duplicate_references,
        "row_classes": dict(sorted(classes.items())),
        "decision_dependency_hits": decision_dependency_hits,
        "unclaimed_verdict_flips": len(decision_dependency_hits),
        "rows_sha256": hashlib.sha256(canonical_bytes(rows)).hexdigest(),
        "served_rows_sha256": hashlib.sha256(canonical_bytes(served_rows)).hexdigest(),
        "decisions_sha256": hashlib.sha256(canonical_bytes(decisions)).hexdigest(),
        "rows": rows,
        "decisions": decisions,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
