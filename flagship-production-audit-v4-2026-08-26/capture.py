#!/usr/bin/env python3
"""Capture a positive receipt only for the complete deployed flagship experience."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parent
BASE = "https://ainglish.org"
CURRENT_REPEAT = "repeat-event-restore-state-did-again-repeat-the-action-or-on-3"
STALE_REPEAT = "repeat-event-restore-state-did-again-repeat-the-action-or-on-2"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def get(path: str) -> tuple[int, bytes]:
    try:
        with urllib.request.urlopen(BASE + path, timeout=30) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def inspect() -> dict:
    api_status, api_body = get("/api/v1/flagships")
    try:
        catalog = json.loads(api_body)
    except json.JSONDecodeError:
        catalog = {}
    entries = catalog.get("entries", []) if isinstance(catalog, dict) else []
    slugs = [entry.get("pinned_slug") for entry in entries]
    editorial_complete = all(
        isinstance(entry.get("editorial"), dict)
        and all(str(entry["editorial"].get(key) or "").strip() for key in ("problem", "before", "after", "consequence", "do_not_say"))
        and " / " in entry["editorial"]["after"]
        for entry in entries
    )
    surfaces_current = all(
        entry.get("surface", {}).get("exists") is True
        and entry.get("surface", {}).get("current") is True
        and entry.get("surface", {}).get("review_required") is False
        for entry in entries
    )
    road_status, road_body = get("/road-to-register")
    road_text = road_body.decode("utf-8", errors="replace")
    detail_checks = []
    for entry in entries:
        project = entry.get("project") or {}
        path = (project.get("links") or {}).get("flagship")
        status = get(path)[0] if isinstance(path, str) and path.startswith("/flagships/") else None
        detail_checks.append({"public_id": project.get("public_id"), "path": path, "http_status": status})
    checks = {
        "api_http_200": api_status == 200,
        "entry_count_17": len(entries) == 17 and catalog.get("selection", {}).get("entry_count") == 17,
        "editorial_complete": editorial_complete,
        "surfaces_current": surfaces_current,
        "repeat_successor_current": CURRENT_REPEAT in slugs and STALE_REPEAT not in slugs,
        "road_http_200": road_status == 200,
        "road_copy_present": "The road to the register" in road_text and "promising, not standing Ainglish" in road_text,
        "detail_pages_200": len(detail_checks) == 17 and all(row["http_status"] == 200 for row in detail_checks),
    }
    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "base": BASE,
        "checks": checks,
        "passed": all(checks.values()),
        "catalogue": {
            "entries": len(entries),
            "content_sha256": catalog.get("content_sha256"),
            "pinned_slugs": slugs,
        },
        "detail_pages": detail_checks,
        "model_calls": 0,
        "governance_writes": 0,
    }


def main() -> None:
    report = inspect()
    if not report["passed"]:
        failed = [key for key, value in report["checks"].items() if not value]
        raise SystemExit("REFUSING incomplete production receipt; failed: " + ", ".join(failed))
    report["kind"] = "dexagon.ainglish.flagship-production-audit.v4"
    report["content_sha256"] = hashlib.sha256(canonical(report)).hexdigest()
    target = ROOT / "audit.json"
    if target.exists():
        raise SystemExit("REFUSING: immutable audit.json already exists")
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "passed", "content_sha256": report["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()

