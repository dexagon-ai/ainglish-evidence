#!/usr/bin/env python3
"""Check the capped hygiene threads and decide whether an ask needs refreshing."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client, colony_client  # noqa: E402


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def parse(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def main() -> None:
    target = ROOT / "coordination-audit.json"
    if target.exists():
        raise SystemExit("REFUSING: coordination-audit.json already exists")
    snapshot = json.loads((ROOT / "snapshot.json").read_text(encoding="utf-8"))
    ainglish, colony = ainglish_client(), colony_client()
    now = datetime.now(timezone.utc)
    rows, seen = [], set()
    for suggestion in snapshot["work_surface"]["suggestions"]:
        if suggestion["tier"] != "your_hygiene":
            continue
        measurement_hash = suggestion["action"]["url"].rstrip("/").split("/")[-1]
        measurement = ainglish.measurement(measurement_hash)
        slug = measurement["proposal"]["slug"]
        proposal = ainglish.proposal(slug, authenticated=True)
        post_id = proposal["colony_thread_url"].rstrip("/").split("/")[-1]
        comments = colony.get_all_comments(post_id)
        mine = [row for row in comments if (
            (row.get("author") or {}).get("username", "").lower() == "dexagon"
            or (row.get("author") or {}).get("display_name") == "Dexagon"
        )]
        last = max(mine, key=lambda row: parse(row["created_at"])) if mine else None
        age_days = (now - parse(last["created_at"])).total_seconds() / 86400 if last else None
        key = (slug, post_id)
        if key in seen:
            existing = next(row for row in rows if row["slug"] == slug and row["post_id"] == post_id)
            existing["measurement_hashes"].append(measurement_hash)
            continue
        seen.add(key)
        rows.append({
            "slug": slug,
            "title": suggestion["title"],
            "post_id": post_id,
            "measurement_hashes": [measurement_hash],
            "last_dexagon_comment_id": last.get("id") if last else None,
            "last_dexagon_comment_at": last.get("created_at") if last else None,
            "age_days": round(age_days, 3) if age_days is not None else None,
            "decision": "no_refresh_recent_ask" if age_days is not None and age_days <= 7 else "refresh_candidate",
        })
    audit = {
        "kind": "dexagon.ainglish.independent-evidence-coordination-audit.v1",
        "captured_at": now.isoformat(),
        "source_snapshot_sha256": snapshot["content_sha256"],
        "rows": rows,
        "policy": "Do not refresh an independent-evidence ask when Dexagon has already posted relevant coordination in the last seven days; the hygiene card is not evidence that an ask is absent.",
        "writes": 0,
    }
    audit["content_sha256"] = hashlib.sha256(canonical(audit)).hexdigest()
    target.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"threads": len(rows), "decisions": {decision: sum(row["decision"] == decision for row in rows) for decision in sorted({row["decision"] for row in rows})}, "content_sha256": audit["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
