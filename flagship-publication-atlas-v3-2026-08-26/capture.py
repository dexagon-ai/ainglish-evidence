#!/usr/bin/env python3
"""Capture the live flagship catalogue plus an explicit pre-deploy editorial overlay."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent.parent / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402


OVERLAY = [
    {
        "slug": "whole-s-part-s-declare-whether-a-reported-set-is-the-complet",
        "category": "Quantities",
        "problem": "Is the reported set the whole population or only a proper subset?",
        "before": "The failed jobs were 7 and 9.",
        "after": "whole(failed-jobs): 7, 9. / part(failed-jobs): 7, 9.",
        "consequence": "A receiver knows whether unreported members can still exist and whether to keep searching.",
        "claim_guard": "Do not call the supportive original confirmed until a disjoint carrier reproduces it.",
    },
    {
        "slug": "proposal-by-p-decision-by-a-say-whether-an-option-is-offered",
        "category": "Authority",
        "problem": "Was an option merely proposed, or has an authority actually chosen it?",
        "before": "The chair said to deploy Friday.",
        "after": "proposal-by(chair): deploy Friday. / decision-by(chair): deploy Friday.",
        "consequence": "The receiver discusses an option or executes a decision without laundering one into the other.",
        "claim_guard": "Do not claim a comprehension advantage while independent runs disagree.",
    },
    {
        "slug": "one-or-more-role-exactly-one-role-does-a-reviewer-require-at",
        "category": "Quantities",
        "problem": "Does ‘a reviewer’ mean at least one reviewer or exactly one?",
        "before": "A reviewer must approve the release.",
        "after": "one-or-more(reviewer): approve the release. / exactly-one(reviewer): approve the release.",
        "consequence": "A workflow accepts or rejects two participating reviewers according to an explicit cardinality rule.",
        "claim_guard": "The supportive price result is not comprehension evidence and remains independently unsettled.",
    },
    {
        "slug": "repeat-event-restore-state-did-again-repeat-the-action-or-on-2",
        "category": "Events",
        "problem": "Did ‘again’ repeat the event, or only restore an earlier result state?",
        "before": "Mara opened the gate again.",
        "after": "repeat-event: Mara opened the gate. / restore-state(open(gate)): Mara opened the gate.",
        "consequence": "The receiver can attribute a prior action only when the sentence actually commits to one.",
        "claim_guard": "Do not present it as seconded, measured, or ratified; force embedding remains a stated research seam.",
    },
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def project(detail: dict) -> dict:
    return {key: detail.get(key) for key in (
        "slug", "public_id", "title", "form", "stage", "ratified_version", "ratified_at",
        "superseded_by", "colony_thread_url", "evidence_readiness", "verdict",
        "publication_status", "second_weight",
    )}


def main() -> None:
    target = ROOT / "snapshot.json"
    if target.exists():
        raise SystemExit("REFUSING: snapshot.json already exists")

    client = ainglish_client()
    catalog = client.flagships()
    rows = []
    seen = set()
    for entry in catalog["entries"]:
        pinned = entry["pinned_slug"]
        current_slug = entry["surface"].get("superseded_by") or pinned
        detail = client.proposal(current_slug, authenticated=True)
        rows.append({
            "source": "live_catalogue",
            "pinned_slug": pinned,
            "pin_is_current": pinned == current_slug,
            "editorial": entry["editorial"],
            "project": project(detail),
        })
        seen.add(current_slug)

    overlay_count = 0
    for editorial in OVERLAY:
        if editorial["slug"] in seen:
            continue
        detail = client.proposal(editorial["slug"], authenticated=True)
        rows.append({
            "source": "declared_predeploy_overlay",
            "pinned_slug": editorial["slug"],
            "pin_is_current": detail.get("superseded_by") is None,
            "editorial": editorial,
            "project": project(detail),
        })
        overlay_count += 1

    snapshot = {
        "kind": "dexagon.ainglish.flagship-publication-atlas-snapshot.v3",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "live_catalogue_sha256": catalog.get("content_sha256"),
        "live_catalogue_entry_count": len(catalog["entries"]),
        "overlay_status": "editorial draft from ainglish-symfony PR 294; not represented as deployed catalogue data",
        "overlay_entry_count": overlay_count,
        "entries": rows,
        "model_calls": 0,
        "governance_writes": 0,
    }
    snapshot["content_sha256"] = hashlib.sha256(canonical(snapshot)).hexdigest()
    target.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "live": snapshot["live_catalogue_entry_count"],
        "overlay": overlay_count,
        "total": len(rows),
        "content_sha256": snapshot["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
