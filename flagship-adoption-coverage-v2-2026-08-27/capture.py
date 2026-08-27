#!/usr/bin/env python3
"""Capture and fail closed on live adoption coverage for ratified flagships."""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from ainglish.client import AinglishClient


ROOT = Path(__file__).resolve().parent
HEX64 = set("0123456789abcdef")


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def parse_datetime(value: object, label: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise AssertionError(f"{label} is absent")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise AssertionError(f"{label} has no timezone")
    return parsed


def parse_date(value: object, label: str) -> date:
    if not isinstance(value, str) or not value:
        raise AssertionError(f"{label} is absent")
    return date.fromisoformat(value[:10])


def is_sha256(value: object) -> bool:
    return isinstance(value, str) and value.startswith("sha256:") and len(value) == 71 \
        and set(value[7:]) <= HEX64


def audit_entry(entry: dict[str, Any], evaluated_at: datetime) -> dict[str, Any]:
    project = entry.get("project")
    if not isinstance(project, dict):
        raise AssertionError("ratified flagship lost its live project")
    adoption = project.get("adoption")
    methodology = adoption.get("methodology") if isinstance(adoption, dict) else None
    coverage = methodology.get("coverage") if isinstance(methodology, dict) else None
    if not isinstance(coverage, dict):
        raise AssertionError(f"{project.get('public_id')} has no first-class adoption coverage receipt")

    ratified_at = parse_datetime(coverage.get("ratified_at"), "coverage.ratified_at")
    last_observation_at = parse_datetime(coverage.get("last_observation_at"), "coverage.last_observation_at")
    valid_until = parse_datetime(coverage.get("valid_until"), "coverage.valid_until")
    observed_until = parse_date(coverage.get("observed_until"), "coverage.observed_until")
    corpus = methodology.get("corpus")
    cadence = methodology.get("scanner_cadence")
    checks = {
        "first_class_receipt": True,
        "status_current_post_ratification": coverage.get("status") == "current_post_ratification",
        "post_ratification_true": coverage.get("post_ratification") is True,
        "observation_recorded_after_ratification": last_observation_at >= ratified_at,
        "window_reaches_ratification": observed_until >= ratified_at.date(),
        "receipt_current_at_capture": valid_until >= evaluated_at,
        "detector_is_mention_vs_use_v2": methodology.get("detector_version") == "adoption-mention-vs-use-v2",
        "corpus_digest_bound": isinstance(corpus, dict) and is_sha256(corpus.get("digest")),
        "positive_scan_count": isinstance(methodology.get("scan_count"), int) and methodology["scan_count"] > 0,
        "cadence_declared": isinstance(cadence, dict)
            and isinstance(cadence.get("stale_after_seconds"), int)
            and cadence["stale_after_seconds"] > 0,
    }
    safe = all(checks.values())
    return {
        "rank": entry.get("editorial", {}).get("rank"),
        "public_id": project.get("public_id"),
        "slug": project.get("slug") or entry.get("pinned_slug"),
        "title": project.get("title"),
        "adoption_status": adoption.get("status"),
        "recent_usage": adoption.get("recent_usage"),
        "coverage": coverage,
        "detector_version": methodology.get("detector_version"),
        "corpus": corpus,
        "scan_count": methodology.get("scan_count"),
        "checks": checks,
        "safe_served_adoption_claim": safe,
    }


def main() -> None:
    client = AinglishClient(use_env=False)
    catalog = client.flagships()
    evaluated_at = datetime.now(timezone.utc).replace(microsecond=0)
    entries = catalog.get("entries")
    if not isinstance(entries, list):
        raise AssertionError("flagship catalog lost entries")
    ratified = [entry for entry in entries if entry.get("project", {}).get("stage") == "ratified"]
    if len(ratified) != 9:
        raise AssertionError(f"expected exactly 9 ratified flagships, found {len(ratified)}")
    rows = [audit_entry(entry, evaluated_at) for entry in ratified]
    unsafe = [row["public_id"] for row in rows if not row["safe_served_adoption_claim"]]
    payload = {
        "kind": "dexagon.ainglish.flagship-adoption-coverage.v2",
        "evaluated_at": evaluated_at.isoformat(),
        "source": "https://ainglish.org/api/v1/flagships",
        "source_content_sha256": catalog.get("content_sha256"),
        "method": {
            "scope": "Every live flagship whose lifecycle stage was ratified at capture time.",
            "claim_rule": "A served sustained or not_yet_adopted claim is safe only under a current first-class post-ratification coverage receipt.",
            "zero_rule": "Zero usage is an observed zero only under the same current coverage gate; missing or stale coverage is unscanned.",
            "refresh_decision": "No redundant observation was filed while every receipt remained current; the scheduled scanner remains responsible for the next reading.",
        },
        "summary": {
            "ratified_flagships": len(rows),
            "safe_current_receipts": len(rows) - len(unsafe),
            "unsafe_served_adoption_claims": len(unsafe),
            "adoption_statuses": dict(sorted(Counter(row["adoption_status"] for row in rows).items())),
            "earliest_valid_until": min(row["coverage"]["valid_until"] for row in rows),
        },
        "unsafe_public_ids": unsafe,
        "rows": rows,
        "network_reads": 1,
        "network_writes": 0,
        "governance_writes": 0,
    }
    payload["content_sha256"] = hashlib.sha256(canonical_bytes(payload)).hexdigest()
    (ROOT / "audit.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")

    lines = [
        "# Ratified-flagship adoption coverage", "",
        f"Captured `{payload['evaluated_at']}` from the live flagship catalogue.", "",
        "This is a fail-closed coverage audit, not a new scan. It keeps observed zero distinct",
        "from missing observation and does not refile redundant evidence while the server-owned",
        "post-ratification receipts remain current.", "",
        "## Result", "",
        f"- ratified flagships: {payload['summary']['ratified_flagships']}",
        f"- safe current receipts: {payload['summary']['safe_current_receipts']}",
        f"- unsafe served adoption claims: {payload['summary']['unsafe_served_adoption_claims']}",
        f"- adoption states: `{json.dumps(payload['summary']['adoption_statuses'], sort_keys=True)}`",
        f"- earliest receipt expiry: `{payload['summary']['earliest_valid_until']}`",
        f"- audit digest: `{payload['content_sha256']}`", "",
        "## Decision", "",
        "No manual observation is warranted now. Let the scheduled scanner refresh the readings;",
        "fail the public adoption claim closed if any receipt reaches expiry first.", "",
        "## Reproduce", "", "```bash",
        "PYTHONPATH=/path/to/ainglish/src python capture.py", "```", "",
    ]
    (ROOT / "README.md").write_text("\n".join(lines))
    print(json.dumps(payload["summary"], indent=2))


if __name__ == "__main__":
    main()
