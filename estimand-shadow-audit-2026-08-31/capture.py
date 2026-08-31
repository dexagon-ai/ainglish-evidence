#!/usr/bin/env python3
"""Capture declaration coverage on every currently disputed original."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402

OUT = ROOT / "snapshot.json"
PLACEHOLDER_ESTIMANDS = (
    "backfilled from a filed measurement row",
    "minted at filing time",
    "backfilled",
)
DIMENSION_KEYS = {
    "contrast": {"contrast", "comparator", "control", "baseline"},
    "population": {"population", "frame", "sampling_frame", "generator", "corpus"},
    "aggregation": {"aggregation", "reducer", "least_favourable_rule", "headline_rule"},
}


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def walk(value: Any, path: tuple[str, ...] = ()):
    if isinstance(value, dict):
        for key, child in value.items():
            here = path + (str(key),)
            yield here, child
            yield from walk(child, here)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, path + (str(index),))


def declarations(manifest: dict[str, Any] | None, estimand: str, measurement: dict[str, Any]) -> dict[str, Any]:
    paths = list(walk(manifest or {}))
    found: dict[str, list[dict[str, Any]]] = {}
    for dimension, keys in DIMENSION_KEYS.items():
        found[dimension] = [
            {"path": ".".join(path), "value": value}
            for path, value in paths if path and path[-1].lower() in keys
        ]

    # Existing manifests frequently state the reducer in a deterministic method
    # sentence rather than under a named field. Record that as prose-visible, not
    # as structured equality evidence.
    method = str((manifest or {}).get("method") or "")
    aggregation_prose = sorted(set(
        match.group(0).lower().replace(" ", "_")
        for match in re.finditer(
            r"\b(?:mean|median|minimum|maximum|floor|worst tokenizer|least favourable|least-favourable)\b",
            method,
            re.IGNORECASE,
        )
    ))
    explicit_estimand = bool(estimand.strip()) and not any(
        estimand.lower().startswith(prefix) for prefix in PLACEHOLDER_ESTIMANDS
    )
    models = list((manifest or {}).get("models") or measurement.get("panel_models") or [])
    tokenizer = measurement.get("tokenizer_provenance")
    input_paths = [
        {"path": ".".join(path), "sha256": digest(value), "items": len(value) if isinstance(value, list) else None}
        for path, value in paths
        if path and path[-1].lower() in {"test_set", "items", "pairs", "prompts"}
        and isinstance(value, (list, dict))
    ]
    return {
        "free_text_estimand_declared": explicit_estimand,
        "contrast": {"structured": bool(found["contrast"]), "declarations": found["contrast"]},
        "population": {"structured": bool(found["population"]), "declarations": found["population"]},
        "aggregation": {
            "structured": bool(found["aggregation"]),
            "declarations": found["aggregation"],
            "prose_markers": aggregation_prose,
        },
        "instrument": {
            "declared": bool(models or tokenizer),
            "models": models,
            "tokenizer_provenance": tokenizer,
        },
        "input_realisation": {"declared": bool(input_paths), "declarations": input_paths},
    }


def row_record(client: Any, measurement: dict[str, Any]) -> dict[str, Any]:
    attempt = measurement.get("attempt") or {}
    pin = attempt.get("pin") or {}
    storage = attempt.get("manifest_storage") or "missing"
    manifest = None
    manifest_error = None
    if attempt.get("attempt_id") and storage != "commitment_only":
        try:
            manifest = client.attempt_manifest(attempt["attempt_id"])
        except Exception as exc:  # preserved as typed audit evidence
            manifest_error = f"{type(exc).__name__}: {exc}"
    estimand = str(pin.get("estimand") or "")
    return {
        "manifest_hash": measurement.get("manifest_hash"),
        "replicates_hash": measurement.get("replicates_hash"),
        "metric": measurement.get("metric"),
        "formula_version": measurement.get("formula_version"),
        "value": measurement.get("value"),
        "value_lo": measurement.get("value_lo"),
        "value_hi": measurement.get("value_hi"),
        "submitter": (measurement.get("submitter") or {}).get("name"),
        "reproduced_ok": measurement.get("reproduced_ok"),
        "settlement_eligible": measurement.get("settlement_eligible"),
        "counts_toward_verdict": measurement.get("counts_toward_verdict"),
        "resolution_bound": measurement.get("resolution_bound"),
        "manifest_storage": storage,
        "manifest_available": manifest is not None,
        "manifest_error": manifest_error,
        "preregistered": bool(attempt) and not bool(attempt.get("backfilled")),
        "estimand": estimand,
        "declarations": declarations(manifest, estimand, measurement),
    }


def relation(original: dict[str, Any], replication: dict[str, Any]) -> dict[str, Any]:
    if not original["manifest_available"] or not replication["manifest_available"]:
        return {
            "status": "underdetermined",
            "reason": "one or both canonical manifests are unavailable",
        }
    differences = []
    for dimension in ("contrast", "population", "aggregation"):
        left = original["declarations"][dimension]["declarations"]
        right = replication["declarations"][dimension]["declarations"]
        if left and right and canonical(left) != canonical(right):
            differences.append(dimension)
    if original["metric"] != replication["metric"]:
        differences.append("metric")
    return {
        "status": "declared_difference" if differences else "no_declared_difference_found",
        "different_dimensions": differences,
        "interpretation": (
            "Report-only. Absence of a declared difference is not proof of comparability; "
            "instrument and fresh-input differences can be intentional."
        ),
    }


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"REFUSING: {OUT.name} already exists")
    client = ainglish_client()
    queue = client.queue()
    groups = []
    seen_originals: set[str] = set()
    all_rows = []
    for item in queue.get("needs_dispute_settlement") or []:
        proposal = client.proposal(item["slug"])
        measurements = proposal.get("measurements") or []
        by_hash = {row.get("manifest_hash"): row for row in measurements}
        for dispute in (item.get("evidence_work") or {}).get("disputes") or []:
            target = dispute["manifest_hash"]
            if target in seen_originals or target not in by_hash:
                continue
            seen_originals.add(target)
            original = row_record(client, by_hash[target])
            replications = [
                row_record(client, row) for row in measurements
                if row.get("replicates_hash") == target
                and row.get("settlement_eligible") is True
                and row.get("counts_toward_verdict") is True
            ]
            all_rows.extend([original, *replications])
            groups.append({
                "slug": item["slug"], "public_id": item.get("public_id"), "title": item["title"],
                "original": original, "replications": replications,
                "relations": [relation(original, row) for row in replications],
            })

    summary = {
        "queue_dispute_items": len(queue.get("needs_dispute_settlement") or []),
        "disputed_originals": len(groups),
        "settlement_rows_audited": len(all_rows),
        "manifest_storage": dict(sorted(Counter(row["manifest_storage"] for row in all_rows).items())),
        "canonical_manifest_available": sum(row["manifest_available"] for row in all_rows),
        "preregistered": sum(row["preregistered"] for row in all_rows),
        "free_text_estimand_declared": sum(row["declarations"]["free_text_estimand_declared"] for row in all_rows),
        "structured_contrast": sum(row["declarations"]["contrast"]["structured"] for row in all_rows),
        "structured_population": sum(row["declarations"]["population"]["structured"] for row in all_rows),
        "structured_aggregation": sum(row["declarations"]["aggregation"]["structured"] for row in all_rows),
        "aggregation_visible_in_prose": sum(bool(row["declarations"]["aggregation"]["prose_markers"]) for row in all_rows),
        "instrument_declared": sum(row["declarations"]["instrument"]["declared"] for row in all_rows),
        "input_realisation_declared": sum(row["declarations"]["input_realisation"]["declared"] for row in all_rows),
        "pair_relations": dict(sorted(Counter(
            relation["status"] for group in groups for relation in group["relations"]
        ).items())),
    }
    payload = {
        "kind": "dexagon.ainglish-estimand-shadow-audit.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "authenticated Ainglish queue plus public proposal, attempt, and stored-manifest reads",
        "method_note": (
            "Presence audit only. It does not infer semantic equivalence, treat instrument changes as failures, "
            "or alter settlement. Structured means a named manifest field, while prose markers are reported separately."
        ),
        "summary": summary,
        "groups": groups,
    }
    payload["content_sha256"] = digest(payload)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
