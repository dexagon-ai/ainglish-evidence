#!/usr/bin/env python3
"""Capture the live token-dispute settlement intake without running tokenizers."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client

OUT = ROOT / "snapshot.json"


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def main() -> None:
    client = ainglish_client()
    suggestions = client.suggestions()
    me = client.me()["sub"]
    rows = []
    for queued in client.queue()["needs_dispute_settlement"]:
        work = queued.get("evidence_work") or {}
        if work.get("metric") != "token_delta":
            continue
        proposal = client.proposal(queued["slug"], authenticated=True)
        for target_hash in work.get("target_hashes") or []:
            target = client.measurement(target_hash)
            target_manifest = target.get("manifest") or {}
            target_submitter = target.get("submitter") or {}
            target_attempt = target.get("attempt") or {}
            replications = [
                row
                for row in proposal.get("measurements") or []
                if row.get("replicates_hash") == target_hash
                and row.get("evidence_state") == "valid"
            ]
            eligible = [row for row in replications if row.get("settlement_eligible")]
            agreements = [row for row in eligible if row.get("reproduced_ok")]
            disagreements = [
                row for row in eligible if row.get("reproduced_ok") is False
            ]
            dexagon_rows = [
                row for row in eligible if (row.get("submitter") or {}).get("sub") == me
            ]
            test_set = target_manifest.get("test_set") or []
            exact_form_mapping = False
            if len(test_set) == 1 and isinstance(test_set[0], dict):
                exact_form_mapping = bool(
                    test_set[0].get("ainglish") == proposal.get("form")
                    and test_set[0].get("english") == proposal.get("english_mapping")
                )

            if target.get("confirmed"):
                lane = "already_confirmed_refresh_queue"
            elif target_submitter.get("sub") == me:
                lane = "independent_agent_required_dexagon_original"
            elif dexagon_rows:
                lane = "independent_agent_required_dexagon_already_has_voice"
            elif target_attempt.get("manifest_storage") == "commitment_only":
                lane = "blocked_exact_estimand_not_retrievable"
            elif len(test_set) <= 1:
                lane = "do_not_bruteforce_definition_or_singleton_estimand"
            else:
                lane = "dexagon_candidate_after_estimand_review"

            agreements_needed = max(0, len(disagreements) + 1 - (1 + len(agreements)))
            rows.append(
                {
                    "proposal": {
                        "slug": proposal["slug"],
                        "public_id": proposal["public_id"],
                        "title": proposal["title"],
                        "proposer": proposal.get("proposer"),
                    },
                    "target": {
                        "manifest_hash": target_hash,
                        "value": target.get("value"),
                        "models": target_manifest.get("models")
                        or target.get("panel_models"),
                        "submitter": target_submitter,
                        "manifest_storage": target_attempt.get("manifest_storage"),
                        "manifest_retrievable": bool(target_manifest),
                        "test_set_items": len(test_set),
                        "exact_form_vs_mapping_singleton": exact_form_mapping,
                        "confirmed": target.get("confirmed"),
                        "settlement_state": target.get("settlement_state"),
                    },
                    "settlement": {
                        "eligible_agreements": len(agreements),
                        "eligible_disagreements": len(disagreements),
                        "agreements_needed_for_strict_majority": agreements_needed,
                        "eligible_agents": [
                            {
                                "name": (row.get("submitter") or {}).get("name"),
                                "reproduced_ok": row.get("reproduced_ok"),
                                "value": row.get("value"),
                            }
                            for row in eligible
                        ],
                        "dexagon_already_has_voice": bool(dexagon_rows),
                    },
                    "recommended_lane": lane,
                }
            )

    by_lane: dict[str, int] = {}
    by_storage: dict[str, int] = {}
    for row in rows:
        lane = row["recommended_lane"]
        by_lane[lane] = by_lane.get(lane, 0) + 1
        storage = str(row["target"]["manifest_storage"])
        by_storage[storage] = by_storage.get(storage, 0) + 1
    result = {
        "kind": "dexagon.ainglish.token-dispute-settlement-intake.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "selection": (
            "Authenticated suggestions first, then every live needs_dispute_settlement queue "
            "target whose metric is token_delta; every proposal and target was freshly read."
        ),
        "interpretation": (
            "token_delta prices only the named current tokenizers. English has current training "
            "and tokenizer exposure advantages; future Ainglish training may improve model "
            "familiarity, while only tokenizer adaptation can change literal segmentation."
        ),
        "summary": {
            "targets": len(rows),
            "by_lane": dict(sorted(by_lane.items())),
            "by_manifest_storage": dict(sorted(by_storage.items())),
            "manifest_retrievable": sum(
                bool(row["target"]["manifest_retrievable"]) for row in rows
            ),
            "singleton_test_sets": sum(
                row["target"]["test_set_items"] <= 1 for row in rows
            ),
            "dexagon_can_take_without_independence_or_input_block": sum(
                row["recommended_lane"] == "dexagon_candidate_after_estimand_review"
                for row in rows
            ),
            "principle": (
                "Do not manufacture settlement by changing comparator genre or reconstructing a "
                "commitment-only manifest from prose. Assign independent principals to stored "
                "complete-pair targets; route legacy estimand ambiguity to the estimand-contract "
                "protocol rather than adding incomparable rows."
            ),
        },
        "suggestion_tier_count": len(suggestions.get("tiers") or []),
        "targets": rows,
    }
    result["content_sha256"] = hashlib.sha256(canonical(result)).hexdigest()
    OUT.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
