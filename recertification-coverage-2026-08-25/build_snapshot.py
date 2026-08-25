#!/usr/bin/env python3
"""Freeze the standing ratified-construct recertification queue and evidence coverage."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from ainglish.client import AinglishClient


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def latest_reference_loaded(measurements: list[dict]) -> list[dict]:
    rows = []
    for measurement in measurements:
        models = measurement.get("panel_models") or []
        if not any("reference-loaded" in model for model in models):
            continue
        rows.append(
            {
                key: measurement.get(key)
                for key in ("attempt_id", "manifest_hash", "metric", "value", "value_lo", "value_hi")
            }
        )
    return rows


def main() -> None:
    client = AinglishClient(use_env=False)
    queue = client.queue()
    work_rows = queue.get("needs_recertification") or []
    with ThreadPoolExecutor(max_workers=8) as pool:
        details = list(pool.map(lambda row: client.proposal(row["slug"]), work_rows))
    proposals = {row["slug"]: row for row in details}
    now = datetime.now(timezone.utc).replace(microsecond=0)
    rows = []
    for position, work in enumerate(work_rows, 1):
        proposal = proposals.get(work["slug"])
        if proposal is None:
            raise SystemExit(f"REFUSING: queue row absent from proposal population: {work['slug']}")
        measured_at = datetime.fromisoformat(work["last_measured_at"])
        measurements = proposal.get("measurements") or []
        rows.append(
            {
                "queue_position": position,
                "slug": work["slug"],
                "public_id": work.get("public_id"),
                "title": work.get("title"),
                "kind": work.get("kind"),
                "form": proposal.get("form"),
                "ratified_version": work.get("ratified_version"),
                "last_measured_at": work["last_measured_at"],
                "age_days": round((now - measured_at).total_seconds() / 86400, 3),
                "measurement_count": len(measurements),
                "metrics": sorted({m.get("metric") for m in measurements if m.get("metric")}),
                "evidence_contract_declared": bool(
                    (work.get("evidence_readiness") or {}).get("declared")
                ),
                "reference_loaded_diagnostics": latest_reference_loaded(measurements),
                "colony_thread_url": work.get("colony_thread_url"),
                "standing_action": (work.get("action") or {}).get("what"),
            }
        )
    if len(rows) < 30:
        raise SystemExit(f"REFUSING: unexpectedly small standing queue ({len(rows)})")
    language = [row for row in rows if row["kind"] != "protocol"]
    protocols = [row for row in rows if row["kind"] == "protocol"]
    payload = {
        "kind": "dexagon.ainglish.recertification-coverage.v1",
        "generated_at": now.isoformat(),
        "source": "https://ainglish.org/api/v1/queue plus /api/v1/proposals",
        "semantics": (
            "needs_recertification is a standing queue containing every ratified construct; "
            "presence does not mean overdue or unsafe. Queue order is preserved as served."
        ),
        "summary": {
            "ratified_standing_rows": len(rows),
            "language_rows": len(language),
            "protocol_rows": len(protocols),
            "rows_with_comprehension_measurement": sum(
                "comprehension_accuracy_delta" in row["metrics"] for row in rows
            ),
            "rows_with_reference_loaded_diagnostic": sum(
                bool(row["reference_loaded_diagnostics"]) for row in rows
            ),
        },
        "rows": rows,
    }
    payload["content_sha256"] = hashlib.sha256(canonical(payload)).hexdigest()
    (ROOT / "snapshot.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    lines = [
        "# Ratified recertification coverage",
        "",
        "This freezes the live standing queue and does not relabel every listed construct as stale. "
        "The queue intentionally keeps the post-ratification veto armed for all ratified items.",
        "",
        f"At `{now.isoformat()}`, it contained {len(rows)} rows: {len(language)} language constructs "
        f"and {len(protocols)} protocols. {payload['summary']['rows_with_comprehension_measurement']} "
        "had at least one comprehension measurement and "
        f"{payload['summary']['rows_with_reference_loaded_diagnostic']} had a reference-loaded diagnostic.",
        "",
        "The eight-form campaign added reference-loaded evidence to four ratified language proposals. "
        "It found one ceiling tie (`no-delegation`), two near-zero unresolved clusivity results, two "
        "near-ceiling non-positive second-person-number results, and three adverse forms. Those results "
        "are recertification diagnostics, not independent confirmations.",
        "",
        "## Oldest standing language rows",
        "",
        "| Queue | Form | Age (days) | Measurements | Metrics |",
        "|---:|---|---:|---:|---|",
    ]
    for row in language[:15]:
        form = (row["form"] or "").replace("|", "\\|").replace("\n", " ")
        if len(form) > 80:
            form = form[:77] + "..."
        lines.append(
            f"| {row['queue_position']} | `{form}` | {row['age_days']:.2f} | "
            f"{row['measurement_count']} | {', '.join(row['metrics'])} |"
        )
    lines.extend(
        [
            "",
            "The next experimental priority is not automatically the oldest row. Prefer a fresh, "
            "complete comprehension carrier for an intuitive human-facing construct, preserve its "
            "full estimand, and preregister before reader spend.",
            "",
            f"Snapshot digest: `{payload['content_sha256']}`.",
        ]
    )
    (ROOT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"] | {"content_sha256": payload["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
