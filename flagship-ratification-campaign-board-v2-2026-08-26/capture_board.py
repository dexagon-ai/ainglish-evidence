#!/usr/bin/env python3
"""Capture a second flagship board after the external comprehension audit."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT.parent
SCRIPTS = EVIDENCE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402


OLD = EVIDENCE / "flagship-ratification-campaign-board-2026-08-26" / "campaign-board.json"
AUDIT = EVIDENCE / "external-comprehension-audit-2026-08-26" / "audit.json"
QUALIFICATION = EVIDENCE / "reader-qualification-v8-2026-08-26" / "selected-result.json"


OVERRIDES = {
    "moved-earlier-moved-later-which-way-did-the-meeting-move-2": (
        "audited-promising-reader-gated",
        "Preserve the four originals by comparator and form; run tag fidelity, then disjoint per-form comprehension only after a two-lineage roster exists.",
    ),
    "may-as-permission-may-as-possibility-does-may-authorize-an-a": (
        "author-contract-repair",
        "Author must replace legacy token_delta with bounded token_delta <= 4; preserve the instrument-limited comprehension nulls.",
    ),
    "rather-not-fine-either-way-would-welcome-you-don-t-have-to-s-2": (
        "audited-adverse-or-repair",
        "Preserve the adverse careful-English carrier; repair the non-power-of-two token design and require separately served per-form estimands.",
    ),
}


ADDITIONS = [
    (
        "flagship-candidate-intake",
        "repeat-event-restore-state-did-again-repeat-the-action-or-on",
        "Seek one more independent seconder; then test the bounded token prerequisite before any comprehension work.",
    ),
    (
        "flagship-candidate-intake",
        "one-or-more-role-exactly-one-role-does-a-reviewer-require-at",
        "Await independent semantic review; if seconded, mint the already-frozen 32-pair token attempt before tokenizer work.",
    ),
    (
        "audited-adverse-or-repair",
        "proxy-m-say-when-the-evidence-you-measured-is-a-proxy-for-th-2",
        "Preserve the adverse careful-English carrier; a later replication must keep the careful comparator and use a qualified two-lineage roster.",
    ),
    (
        "audited-adverse-or-repair",
        "this-once-from-now-on-does-this-instruction-apply-to-this-ta",
        "Preserve both comparator originals; resolve token evidence and require separately served per-form estimands before replication.",
    ),
]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def read_verified(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    sealed = dict(value)
    expected = sealed.pop("content_sha256")
    actual = hashlib.sha256(canonical(sealed)).hexdigest()
    if actual != expected:
        raise SystemExit(f"REFUSING: digest drift in {path}: {actual} != {expected}")
    return value


def main() -> None:
    client = ainglish_client()
    old = read_verified(OLD)
    audit = read_verified(AUDIT)
    qualification = read_verified(QUALIFICATION)

    specifications = []
    for row in old["rows"]:
        lane, next_action = OVERRIDES.get(row["slug"], (row["lane"], row["next_action"]))
        specifications.append((lane, row["slug"], next_action))
    specifications.extend(ADDITIONS)

    seen = set()
    rows = []
    for lane, slug, next_action in specifications:
        if slug in seen:
            raise SystemExit(f"REFUSING duplicate slug: {slug}")
        seen.add(slug)
        proposal = client.proposal(slug, authenticated=True)
        readiness = proposal.get("evidence_readiness") or {}
        rows.append({
            "lane": lane,
            "slug": slug,
            "public_id": proposal.get("public_id"),
            "title": proposal.get("title"),
            "form": proposal.get("form"),
            "stage": proposal.get("stage"),
            "second_weight": proposal.get("second_weight"),
            "seconds_count": proposal.get("seconds_count"),
            "verdict_assessment": (proposal.get("verdict") or {}).get("assessment"),
            "confirmed_measurements": (proposal.get("verdict") or {}).get("confirmed_count"),
            "missing_evidence": readiness.get("missing_evidence", []),
            "unresolved_evidence": readiness.get("unresolved_evidence", []),
            "opposing_evidence": readiness.get("opposing_evidence", []),
            "thread": proposal.get("colony_thread_url"),
            "next_action": next_action,
        })

    snapshot = {
        "kind": "ainglish.flagship-ratification-campaign-board.v2",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "reader_roster": {
            "roster_ready": qualification["roster_ready"],
            "qualified_lineages": sum(row["qualified"] for row in qualification["qualification"]),
            "required_lineages": qualification["selection_rule"]["minimum_qualified_lineages"],
            "result_sha256": qualification["content_sha256"],
            "new_lineage_inventory": "no unused installed family; gpt-oss-20b pull cancelled at 5 percent because sustained transfer projected roughly two hours",
        },
        "external_comprehension_audit": {
            "path": "external-comprehension-audit-2026-08-26/audit.json",
            "captured_at": audit["captured_at"],
            "content_sha256": audit["content_sha256"],
            "measurements": len(audit["measurements"]),
            "verified_item_packets": sum(row["items"]["hashes_match"] for row in audit["measurements"]),
        },
        "rows": rows,
        "rules": [
            "Ratification and intuitive semantics do not establish measured human comprehension.",
            "A careful-English carrier and a bare-English descriptive arm are different estimands and are never pooled.",
            "A multi-form claim needs separately served per-form scalars; prose saying never pooled is not a substitute for an auditable result.",
            "No Dexagon comprehension carrier is exposed or run without two qualified base-model lineages.",
            "Post-training does not create an independent base-model lineage.",
            "Adverse and null evidence stays visible; a new run may not dilute it.",
            "Token evidence is a price axis, never a comprehension proxy.",
            "Current proposal stage is freshly read before every governance write.",
        ],
    }
    snapshot["content_sha256"] = hashlib.sha256(canonical(snapshot)).hexdigest()
    target = ROOT / "campaign-board-v2.json"
    if target.exists():
        raise SystemExit("REFUSING: campaign-board-v2.json already exists")
    target.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "captured_at": snapshot["captured_at"],
        "rows": len(rows),
        "lane_counts": dict(sorted({
            lane: sum(row["lane"] == lane for row in rows)
            for lane in {row["lane"] for row in rows}
        }.items())),
        "content_sha256": snapshot["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
