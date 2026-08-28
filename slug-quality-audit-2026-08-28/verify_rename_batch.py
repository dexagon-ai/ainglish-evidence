#!/usr/bin/env python3
"""Verify the conservative production rename batch through every public resolution surface."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request

from ainglish.client import AinglishClient


ROOT = Path(__file__).resolve().parent
REASON = (
    "Replace a truncated title-derived API slug with the proposal's concise construct name; "
    "the immutable public ID remains canonical and the former slug remains a permanent alias."
)
TARGETS = [
    ("a-0w08sbp8900wxtqb", "by-construction-by-rule-in-practice-mark-whether-a-standing-", "by-construction-by-rule-in-practice"),
    ("a-ptwhg57dq4w4fas4", "same-one-same-kind-same-name-mark-whether-same-claims-one-sh-2", "same-one-same-kind-same-name"),
    ("a-1v2tfbyk5zc0g40w", "repeat-event-restore-state-did-again-repeat-the-action-or-on-4", "repeat-event-restore-state"),
    ("a-vdfmetgvbqe4eczj", "percentage-points-not-bare-percent-a-change-to-a-percentage-", "percentage-points-not-percent"),
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def main() -> None:
    client = AinglishClient(use_env=False)
    current = {row["public_id"]: row for row in client.iter_proposals(page_size=200)}
    receipts = []
    for public_id, old_slug, new_slug in TARGETS:
        by_new = client.proposal(new_slug)
        by_old = client.proposal(old_slug)
        history = client.proposal_slug_history(public_id)
        search = list(client.search_proposals(new_slug, page_size=200))
        with urllib.request.urlopen(f"https://ainglish.org/proposals/{public_id}", timeout=20) as response:
            stable_status = response.status
        matching_changes = [
            change for change in history.get("changes", [])
            if change.get("old_slug") == old_slug and change.get("new_slug") == new_slug
        ]
        checks = {
            "complete_list_current": current.get(public_id, {}).get("slug") == new_slug,
            "new_slug_resolves": by_new.get("public_id") == public_id and by_new.get("slug") == new_slug,
            "former_slug_resolves": by_old.get("public_id") == public_id and by_old.get("slug") == new_slug,
            "history_current": history.get("current_slug") == new_slug,
            "history_retains_former_alias": old_slug in history.get("aliases", []),
            "history_has_exact_change": len(matching_changes) == 1,
            "history_reason_matches": len(matching_changes) == 1 and matching_changes[0].get("reason") == REASON,
            "search_returns_current_name": any(row.get("public_id") == public_id and row.get("slug") == new_slug for row in search),
            "stable_human_page_200": stable_status == 200,
        }
        if not all(checks.values()):
            raise SystemExit(f"REFUSING: failed public resolution checks for {public_id}: {checks}")
        receipts.append({
            "public_id": public_id,
            "old_slug": old_slug,
            "new_slug": new_slug,
            "reason": REASON,
            "change": matching_changes[0],
            "stable_url": f"https://ainglish.org/proposals/{public_id}",
            "checks": checks,
        })

    artifact = {
        "kind": "dexagon.ainglish.proposal-slug-rename-batch.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "frozen_prewrite_ledger_commit": "ef74fbbcfc182cdf5586c95fbd5222747e8798bd",
        "preflight": {
            "checked_at": "2026-08-28T16:08:14+00:00",
            "moderator_role_present": True,
            "global_new_reports": 0,
            "exact_new_reports_per_old_slug": {old: 0 for _, old, _ in TARGETS},
            "candidate_names_unoccupied": True,
            "all_targets_visible_active_never_ratified": True,
            "private_report_content_persisted": False,
        },
        "batch_size": len(receipts),
        "receipts": receipts,
        "all_checks_passed": True,
        "model_calls": 0,
        "governance_evidence_claimed": False,
    }
    artifact["content_sha256"] = hashlib.sha256(canonical(artifact)).hexdigest()
    (ROOT / "rename-batch.json").write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    names = ["ledger.json", "ledger.csv", "ranked-active.md", "rename-batch.json"]
    (ROOT / "SHA256SUMS").write_text("\n".join(
        f"{hashlib.sha256((ROOT / name).read_bytes()).hexdigest()}  {name}" for name in names
    ) + "\n", encoding="utf-8")
    print(json.dumps({"batch_size": len(receipts), "content_sha256": artifact["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
