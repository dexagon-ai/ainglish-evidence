#!/usr/bin/env python3
"""Build three balanced 32-pair token prerequisite packets without network calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def campaign(slug: str, forms: list[str], rows: list[dict], acceptance: dict | None) -> dict:
    if not rows or len(rows) & (len(rows) - 1):
        raise SystemExit("REFUSING: pair count must be a power of two")
    if len({(row["english"], row["ainglish"]) for row in rows}) != len(rows):
        raise SystemExit("REFUSING: duplicate complete pair")
    counts = {form: sum(row["form"] == form for row in rows) for form in forms}
    if len(set(counts.values())) != 1:
        raise SystemExit("REFUSING: form imbalance")
    return {"slug": slug, "forms": forms, "acceptance": acceptance, "test_set": rows, "items_sha256": hashlib.sha256(canonical(rows)).hexdigest()}


def build_they() -> list[dict]:
    actions = (
        "approved the release", "owns the incident", "signed the receipt", "accepted the handoff",
        "scheduled the audit", "closed the ballot", "reviewed the patch", "confirmed the booking",
        "received the alert", "controls the key", "submitted the report", "accepted the invitation",
        "started the migration", "holds the lease", "authorized the refund", "completed the checklist",
    )
    rows = []
    for index, action in enumerate(actions, 1):
        rows.append({"form": "they-one", "english": f"Case {index:02d}: That one person {action}.", "ainglish": f"Case {index:02d}: They-one {action}."})
        rows.append({"form": "they-many", "english": f"Case {index:02d}: Those two or more people {action}.", "ainglish": f"Case {index:02d}: They-many {action}."})
    return rows


def build_next() -> list[dict]:
    dates = (
        "2026-09-02", "2026-09-07", "2026-09-11", "2026-09-15", "2026-09-20", "2026-09-24", "2026-09-28", "2026-10-03",
        "2026-10-07", "2026-10-12", "2026-10-16", "2026-10-21", "2026-10-25", "2026-10-30", "2026-11-03", "2026-11-08",
    )
    days = ("Friday", "Tuesday", "Monday", "Thursday")
    actions = ("review", "audit", "maintenance window", "release call", "delivery", "ballot", "backup", "handoff")
    rows = []
    for index, date in enumerate(dates, 1):
        day = days[(index - 1) % len(days)]
        action = actions[(index - 1) % len(actions)]
        rows.append({
            "form": "next-up",
            "english": f"Schedule {action} {index:02d} for the first {day} strictly after {date}.",
            "ainglish": f"Schedule {action} {index:02d} for next-up({day}@{date}).",
        })
        rows.append({
            "form": "next-week",
            "english": f"Schedule {action} {index:02d} for {day} in the calendar week immediately after the Monday-start week containing {date}.",
            "ainglish": f"Schedule {action} {index:02d} for next-week({day}@{date};Monday).",
        })
    return rows


def build_different() -> list[dict]:
    nouns = ("model", "artifact", "endpoint", "reviewer", "checksum", "owner", "version", "region", "worker", "queue", "account", "policy", "dataset", "provider", "image", "route")
    keys = ("model-id", "checksum", "owner", "version")
    rows = []
    for index, noun in enumerate(nouns, 1):
        key = keys[(index - 1) % len(keys)]
        rows.append({
            "form": "different-from",
            "english": f"Choice {index:02d}: select a {noun} whose {key} is unequal to the reference {noun}'s {key}.",
            "ainglish": f"Choice {index:02d}: select a {noun} different-from(reference-{noun}, by={key}).",
        })
        rows.append({
            "form": "different-across",
            "english": f"Choice {index:02d}: assign a {noun} to every reviewer such that distinct reviewers' selected {key} values are pairwise unequal.",
            "ainglish": f"Choice {index:02d}: assign a {noun} to every reviewer different-across(reviewers, by={key}).",
        })
    return rows


def main() -> None:
    campaigns = {
        "they": campaign("they-one-they-many-say-whether-they-is-one-actor-or-several", ["they-one", "they-many"], build_they(), {"at_most": 1}),
        "next": campaign("next-up-day-date-next-week-day-date-weekstart-which-next-fri", ["next-up", "next-week"], build_next(), None),
        "different": campaign("different-from-ref-by-key-different-across-group-by-key-what", ["different-from", "different-across"], build_different(), {"at_most": 2}),
    }
    packet = {"kind": "ainglish.deterministic-token-sweep.v1", "seed": "none - deterministic authored minimal pairs", "model_calls": 0, "campaigns": campaigns}
    packet["content_sha256"] = hashlib.sha256(canonical(packet)).hexdigest()
    target = ROOT / "items.json"
    target.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({name: {"pairs": len(row["test_set"]), "items_sha256": row["items_sha256"]} for name, row in campaigns.items()}, indent=2))


if __name__ == "__main__":
    main()

