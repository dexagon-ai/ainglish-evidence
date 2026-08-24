#!/usr/bin/env python3
"""Audit whether served adoption claims cover the current ratified surface."""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path

from ainglish.client import AinglishClient


ROOT = Path(__file__).resolve().parent
DEFAULT_STALE_AFTER = 7 * 86_400


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def parse_date(value: object) -> date | None:
    if not isinstance(value, str) or not value:
        return None
    return date.fromisoformat(value[:10])


def coverage(entry: dict, evaluated_at: datetime) -> dict:
    if entry.get("kind") == "protocol":
        return {"status": "not_applicable", "post_ratification": False, "safe_adoption_claim": True}
    adoption = entry.get("adoption") or {}
    methodology = adoption.get("methodology") or {}
    first_class = methodology.get("coverage")
    if isinstance(first_class, dict):
        return {**first_class, "source": "first_class_coverage_receipt", "safe_adoption_claim": first_class.get("post_ratification") is True}

    ratified_at = parse_datetime(entry.get("ratified_at"))
    computed_at = parse_datetime(methodology.get("computed_at"))
    observed_until = parse_date(methodology.get("window_end"))
    cadence = methodology.get("scanner_cadence") or {}
    stale_after = cadence.get("stale_after_seconds", DEFAULT_STALE_AFTER)
    if not isinstance(stale_after, int) or stale_after <= 0:
        stale_after = DEFAULT_STALE_AFTER
    valid_until = computed_at + timedelta(seconds=stale_after) if computed_at else None
    recorded_after = bool(ratified_at and computed_at and computed_at >= ratified_at)
    window_reaches = bool(ratified_at and observed_until and observed_until >= ratified_at.date())
    current = bool(valid_until and valid_until >= evaluated_at)
    status = (
        "never_observed" if computed_at is None else
        "pre_ratification_only" if not (recorded_after and window_reaches) else
        "stale" if not current else
        "current_post_ratification"
    )
    return {
        "status": status,
        "ratified_at": ratified_at.isoformat() if ratified_at else None,
        "post_ratification": status == "current_post_ratification",
        "observed_until": observed_until.isoformat() if observed_until else None,
        "last_observation_at": computed_at.isoformat() if computed_at else None,
        "valid_until": valid_until.isoformat() if valid_until else None,
        "source": "derived_from_legacy_methodology_fields",
        "safe_adoption_claim": status == "current_post_ratification",
        "derivation": "computed_at >= ratified_at; window_end >= ratified date; evaluated_at <= computed_at + declared stale_after_seconds",
    }


def main() -> None:
    client = AinglishClient(use_env=False)
    register = client.register()
    evaluated_at = datetime.now(timezone.utc).replace(microsecond=0)
    rows = []
    unsafe_claims = []
    for entry in register.get("entries", []):
        result = coverage(entry, evaluated_at)
        row = {
            "slug": entry.get("slug"),
            "public_id": entry.get("public_id"),
            "title": entry.get("title"),
            "kind": entry.get("kind"),
            "served_adoption_status": (entry.get("adoption") or {}).get("status"),
            "served_recent_usage": (entry.get("adoption") or {}).get("recent_usage"),
            "coverage": result,
        }
        rows.append(row)
        if entry.get("kind") != "protocol" and row["served_adoption_status"] in ("sustained", "not_yet_adopted") and not result["safe_adoption_claim"]:
            unsafe_claims.append({
                "slug": row["slug"], "served_status": row["served_adoption_status"],
                "coverage_status": result["status"],
            })
    status_counts = Counter(row["coverage"]["status"] for row in rows)
    payload = {
        "kind": "dexagon.ainglish.adoption-coverage-audit.v3",
        "evaluated_at": evaluated_at.isoformat(),
        "source": "https://ainglish.org/api/v1/register",
        "register_version": register.get("version"),
        "method": {
            "claim_rule": "sustained or not_yet_adopted is safe only under current post-ratification corpus coverage; missing, stale, or pre-ratification-only evidence is unscanned, never observed zero",
            "freshness": "valid_until is derived from computed_at plus declared scanner cadence; no stored fresh boolean is trusted",
            "resolution_limit": "legacy window_end is date-resolution; first-class coverage is preferred once deployed",
        },
        "summary": {
            "rows": len(rows),
            "coverage_statuses": dict(sorted(status_counts.items())),
            "unsafe_served_adoption_claims": len(unsafe_claims),
        },
        "unsafe_served_adoption_claims": unsafe_claims,
        "rows": rows,
    }
    payload["content_sha256"] = hashlib.sha256(canonical_bytes(payload)).hexdigest()
    (ROOT / "snapshot.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    lines = [
        "# Post-ratification adoption-coverage audit", "",
        f"Evaluated `{payload['evaluated_at']}` against register `{payload['register_version']}`.", "",
        "The audit refuses to turn absence of an instrument into an observed zero. A ratified",
        "surface can be called sustained or not-yet-adopted only when a current scan was recorded",
        "after ratification and its corpus window reaches that surface.", "",
        f"Snapshot digest: `{payload['content_sha256']}`.", "",
        "## Result", "",
        f"- rows: {payload['summary']['rows']}",
        f"- coverage states: `{json.dumps(payload['summary']['coverage_statuses'], sort_keys=True)}`",
        f"- unsafe served adoption claims: {payload['summary']['unsafe_served_adoption_claims']}", "",
    ]
    if unsafe_claims:
        lines += ["## Fail-closed findings", ""]
        for finding in unsafe_claims:
            lines.append(
                f"- `{finding['slug']}` serves `{finding['served_status']}` with coverage "
                f"`{finding['coverage_status']}`."
            )
        lines.append("")
    lines += [
        "## Reproduce", "", "```bash", "python build_audit.py", "```", "",
        "Until the first-class coverage receipt is deployed, the script derives the same rule from",
        "legacy `computed_at`, `window_end`, `ratified_at`, and scanner-cadence fields and labels",
        "that provenance explicitly. Re-run after deployment to verify every row switches to the",
        "server-owned receipt without changing the scientific classification.", "",
    ]
    (ROOT / "README.md").write_text("\n".join(lines))
    print(json.dumps(payload["summary"], indent=2))


if __name__ == "__main__":
    main()
