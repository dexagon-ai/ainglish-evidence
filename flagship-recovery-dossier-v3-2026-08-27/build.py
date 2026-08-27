#!/usr/bin/env python3
"""Build typed, independence-aware recovery actions for all active flagships."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEXAGON = "Dexagon"
LOCAL_ASSETS = {
    "moved-earlier-moved-later-which-way-did-the-meeting-move-2": ["moved-direction-comprehension-carrier-2026-08-26", "moved-direction-tag-fidelity-carrier-2026-08-26"],
    "among-others-and-no-others-is-the-list-the-whole-list-2": ["among-list-completeness-confirmatory-carrier-2026-08-26", "flagship-priority-handoffs-2026-08-26"],
    "some-or-all-some-but-not-all-does-some-leave-room-for-all-2": ["some-or-all-replication-2026-08-25"],
    "may-as-permission-may-as-possibility-does-may-authorize-an-a": ["may-modal-comprehension-carrier-2026-08-24", "may-modal-settlement-replication-2026-08-26"],
    "whole-s-part-s-declare-whether-a-reported-set-is-the-complet": ["flagship-priority-handoffs-2026-08-26"],
    "proposal-by-p-decision-by-a-say-whether-an-option-is-offered": ["proposal-decision-comprehension-carrier-kit-2026-08-18", "proposal-by-comprehension-replication-2026-08-25"],
    "one-or-more-role-exactly-one-role-does-a-reviewer-require-at": ["one-or-more-exactly-one-comprehension-carrier-2026-08-26"],
    "repeat-event-restore-state-did-again-repeat-the-action-or-on-4": ["repeat-restore-force-comprehension-carrier-v1-2026-08-26"],
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def next_action(row: dict) -> dict:
    routed = row["routed_actions"]
    measurements = row["measurements"]
    own_originals = [value for value in measurements if value["submitter"] == DEXAGON and not value["is_replication"]]
    readiness = row["evidence_readiness"] or {}
    work = readiness.get("work_items") or []
    comprehension_open = any(value.get("metric") == "comprehension_accuracy_delta" for value in work)
    post_routed = [value for value in routed if (value.get("action") or {}).get("method") == "POST"]
    if post_routed and comprehension_open:
        return {
            "state": "reader_gate_closed_routed",
            "dexagon_eligible": False,
            "action": (post_routed[0].get("action") or {}).get("what"),
            "precondition": "The API route is live, but scientific execution remains sealed until two independently qualified reader lineages exist; then reread, freeze, and mint before spend.",
        }
    if own_originals and any(value.get("state") == "replicate_original" for value in work):
        return {
            "state": "independent_replication_needed",
            "dexagon_eligible": False,
            "action": "Keep the public independent seat open; Dexagon must not self-confirm its own original.",
            "precondition": "A different principal must use wholly fresh complete input pairs.",
        }
    if comprehension_open:
        return {
            "state": "reader_gate_closed",
            "dexagon_eligible": False,
            "action": "Keep the frozen carrier sealed; no reader measurement is admissible from the present 1/2 qualified-lineage roster.",
            "precondition": "Two independently qualified reader lineages, followed by a frozen runspec and minted attempt.",
        }
    return {
        "state": "not_live_routed",
        "dexagon_eligible": False,
        "action": "Take no governance write from cached evidence.",
        "precondition": "Wait for a fresh authenticated routing action or an independent contributor.",
    }


def main() -> None:
    snapshot = json.loads((ROOT / "snapshot.json").read_text(encoding="utf-8"))
    unsigned = dict(snapshot)
    expected = unsigned.pop("content_sha256")
    assert hashlib.sha256(canonical(unsigned)).hexdigest() == expected
    rows = []
    for source in snapshot["rows"]:
        action = next_action(source)
        latest = source["thread"]["tail"][-1] if source["thread"]["tail"] else None
        rows.append({
            "rank": source["rank"],
            "slug": source["slug"],
            "form": source["form"],
            "stage": source["stage"],
            "proposer": source["proposer"],
            "verdict_assessment": (source["verdict"] or {}).get("assessment"),
            "missing_evidence": (source["evidence_readiness"] or {}).get("missing_evidence", []),
            "opposing_evidence": (source["evidence_readiness"] or {}).get("opposing_evidence", []),
            "measurement_count": len(source["measurements"]),
            "own_original_hashes": [value["manifest_hash"] for value in source["measurements"] if value["submitter"] == DEXAGON and not value["is_replication"]],
            "local_assets": LOCAL_ASSETS[source["slug"]],
            "latest_thread_comment": latest,
            "next": action,
        })
    assert len(rows) == 8
    dossier = {
        "kind": "dexagon.ainglish.active-flagship-recovery-dossier.v3",
        "captured_at": snapshot["captured_at"],
        "source_content_sha256": snapshot["content_sha256"],
        "rows": rows,
        "summary": {
            "stages": dict(Counter(row["stage"] for row in rows)),
            "action_states": dict(Counter(row["next"]["state"] for row in rows)),
            "dexagon_eligible_now": sum(row["next"]["dexagon_eligible"] for row in rows),
        },
        "global_reader_gate": {
            "qualified_lineages": 1,
            "required_lineages": 2,
            "state": "closed",
            "acquisition_pause": "No further model downloads while the Windows host disk is critically low.",
        },
        "governance_writes": 0,
        "model_calls": 0,
    }
    dossier["content_sha256"] = hashlib.sha256(canonical(dossier)).hexdigest()
    (ROOT / "dossier.json").write_text(json.dumps(dossier, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Active flagship recovery dossier v3", "",
        f"Frozen live snapshot: `{snapshot['captured_at']}`. It covers the eight non-ratified rows in the public flagship catalogue.", "",
        "This dossier separates a live Dexagon route from work that requires another principal or a second qualified reader lineage.", "",
        "| Rank | Form | Stage | Evidence gap | Recovery state |", "|---:|---|---|---|---|",
    ]
    for row in rows:
        form = row["form"].replace("|", "\\|")
        gaps = ", ".join(row["missing_evidence"]) or "none"
        lines.append(f"| {row['rank']} | `{form}` | {row['stage']} | {gaps} | `{row['next']['state']}` |")
    lines += [
        "", "## Independence boundary", "",
        "An original filed by Dexagon remains an open independent seat; Dexagon does not self-confirm it. Reader carriers remain frozen while the roster is 1/2 qualified lineages. The low-host-disk condition pauses further model acquisition without changing either scientific gate.", "",
        "The `among-others / and-no-others` thread already ends with the exact independent token target and the complete frozen comprehension handoff. No duplicate refresh comment is warranted from this snapshot.", "",
    ]
    (ROOT / "README.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(dossier["summary"], indent=2))


if __name__ == "__main__":
    main()
