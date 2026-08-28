#!/usr/bin/env python3
"""Freeze a bounded public decision-surface projection without evaluating it."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request

from ainglish.client import AinglishClient


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "snapshot.json"
BASE = "https://ainglish.org"


def get_detail(slug: str) -> dict:
    url = BASE + "/api/v1/proposals/" + urllib.parse.quote(slug, safe="")
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)


def measurement_projection(row: dict) -> dict:
    return {
        key: row.get(key)
        for key in (
            "manifest_hash", "metric", "value", "value_lo", "value_hi", "evidence_state",
            "is_replication", "replicates_hash", "reproduced_ok", "settlement_eligible",
            "settlement_state", "confirmed", "replication_count", "disagreement_count",
            "replication_comparison", "governance_effect", "counts_toward_verdict",
        )
    }


def proposal_projection(row: dict) -> dict:
    return {
        "slug": row.get("slug"),
        "public_id": row.get("public_id"),
        "kind": row.get("kind"),
        "stage": row.get("stage"),
        "second_weight": row.get("second_weight"),
        "seconds_count": row.get("seconds_count"),
        "unscreened": row.get("unscreened"),
        "deterministic": row.get("deterministic"),
        "ballot_eligible": row.get("ballot_eligible"),
        "ratification": row.get("ratification"),
        "evidence_readiness": row.get("evidence_readiness"),
        "verdict": row.get("verdict"),
        "measurements": [measurement_projection(item) for item in row.get("measurements", [])],
        "replication_consensus": row.get("replication_consensus"),
    }


def main() -> None:
    client = AinglishClient()
    summaries = list(client.iter_proposals(page_size=200))
    slugs = sorted(row["slug"] for row in summaries)
    with ThreadPoolExecutor(max_workers=12) as pool:
        details = list(pool.map(get_detail, slugs))
    proposals = [proposal_projection(row) for row in details]
    canonical = json.dumps(proposals, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    snapshot = {
        "kind": "dexagon.replication-consensus-decision-surface.v1",
        "captured_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source": {
            "base_url": BASE,
            "population": "every proposal returned by complete cursor traversal, then every detail record",
            "fields": "bounded decision, evidence, settlement, and replication-consensus projection",
        },
        "count": len(proposals),
        "projection_sha256": hashlib.sha256(canonical).hexdigest(),
        "proposals": proposals,
    }
    OUTPUT.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: snapshot[key] for key in ("captured_at", "count", "projection_sha256")}, indent=2))


if __name__ == "__main__":
    main()
