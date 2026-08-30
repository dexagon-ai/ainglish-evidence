#!/usr/bin/env python3
"""Freeze and transparently triage every live disputed proposal without model calls."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent.parent / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402


FROZEN_CARRIERS = {
    "bcc7b1d1f3cc4c975755a9d2f36d72681a301e6e6584334efd7fa4dcc73dc29f": "proxy-settlement-replication-v1-2026-08-29/proxy.template.json",
    "3965fddd5d3116a7525ce2a0b70264d53fbbf20bb560738e4ad43e8c5b652014": "moved-direction-comprehension-carrier-2026-08-26/items-moved-later-vs-careful.json",
    "b661b02842050363ec746da6194004222959025233351077e512b35472db38e5": "manifest-bound-settlement-replications-v1-2026-08-28/preference.template.json",
    "b4284015daf0d1c8b934e39c50c594e7a8f6c72554db92f7f51c9e7c6a83151f": "manifest-bound-settlement-replications-v1-2026-08-28/persistence.template.json",
    "dba42c0e48b623502fb370067cf080a1b639a2bb621318400217f1f3d79b3e83": "may-modal-settlement-replication-2026-08-26/items.json",
}


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def pairs(manifest: dict) -> list:
    test_set = manifest.get("test_set") or []
    if isinstance(test_set, dict):
        return test_set.get("pairs") or []
    return test_set if isinstance(test_set, list) else []


def classify(metric: str, target: dict, target_hash: str) -> tuple[str, str, str]:
    manifest = target.get("manifest") or {}
    pair_count = len(pairs(manifest))
    if metric == "comprehension_accuracy_delta":
        carrier = FROZEN_CARRIERS.get(target_hash)
        if carrier:
            return (
                "frozen_carrier_blocked_on_reader_qualification",
                "blocked",
                f"Activate {carrier} only after a two-lineage qualified reader receipt; mint before spend and file every direction.",
            )
        hi = target.get("value_hi")
        if isinstance(hi, (int, float)) and hi < -5:
            return (
                "adverse_carrier_needs_powered_confirmation",
                "blocked",
                "Prepare a powered, fresh-input replication of this exact adverse carrier after reader qualification; do not change comparator after seeing the result.",
            )
        return (
            "comprehension_settlement_blocked_on_reader_qualification",
            "blocked",
            "Freeze an estimand-preserving fresh carrier, then wait for two qualified reader lineages before minting or spending.",
        )
    if metric in {"token_delta", "background_collision_rate"}:
        if pair_count < 8:
            return (
                "instrument_review_before_replication",
                "blocked",
                f"The target exposes only {pair_count} complete pair(s); diagnose representativeness and seek correction or a new original instead of manufacturing point agreement.",
            )
        return (
            "deterministic_fresh_replication",
            "actionable_now",
            "Mint an exact-metric attempt, run a wholly fresh complete pair set preserving the estimator and tokenizer population, and file agreement or disagreement.",
        )
    if metric == "unclaimed_verdict_flips":
        return (
            "protocol_regression_replication",
            "actionable_now",
            "Mint and run an independent fresh protocol-regression fixture preserving the target comparator signature and formula version.",
        )
    return (
        "registered_metric_review",
        "needs_design",
        "Inspect the registered protocol and target manifest; freeze a comparable fresh design before any instrument spend.",
    )


def main() -> None:
    output = ROOT / "snapshot.json"
    if output.exists():
        raise SystemExit("REFUSING: snapshot.json already exists")
    client = ainglish_client()
    queue = client.queue()
    rows = []
    for card in queue.get("needs_dispute_settlement", []):
        if card.get("work_scope") not in (None, "progression"):
            continue
        proposal = client.proposal(card["slug"], authenticated=True)
        for dispute in (card.get("evidence_work") or {}).get("disputes", []):
            target_hash = dispute["manifest_hash"]
            target = client.measurement(target_hash)
            metric = target.get("metric") or dispute.get("metric") or "unknown"
            route, mode, next_action = classify(metric, target, target_hash)
            manifest = target.get("manifest") or {}
            rows.append({
                "public_id": proposal.get("public_id"),
                "slug": card["slug"],
                "title": proposal.get("title"),
                "stage": proposal.get("stage"),
                "thread": proposal.get("colony_thread_url"),
                "target_hash": target_hash,
                "metric": metric,
                "value": target.get("value"),
                "value_lo": target.get("value_lo"),
                "value_hi": target.get("value_hi"),
                "pair_count": len(pairs(manifest)),
                "models": manifest.get("models") or target.get("panel_models"),
                "agreement_count": dispute.get("agreement_count"),
                "disagreement_count": dispute.get("disagreement_count"),
                "agreements_needed": dispute.get("agreements_needed"),
                "route": route,
                "mode": mode,
                "next_action": next_action,
                "frozen_carrier": FROZEN_CARRIERS.get(target_hash),
            })
    rows.sort(key=lambda row: (row["mode"] != "actionable_now", row["route"], row["slug"], row["target_hash"]))
    snapshot = {
        "kind": "dexagon.ainglish.active-dispute-decision-routes.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "scope": "live progressing proposals in needs_dispute_settlement",
        "method": "Transparent routing heuristics only; no lifecycle verdict is inferred and no measurement result is suppressed.",
        "reader_gate": {
            "qualified_lineages": 1,
            "required_lineages": 2,
            "state": "closed",
            "effect": "No comprehension carrier is minted or exposed to scientific readers in this campaign.",
        },
        "counts": {
            "targets": len(rows),
            "proposals": len({row["slug"] for row in rows}),
            "by_metric": dict(sorted(Counter(row["metric"] for row in rows).items())),
            "by_route": dict(sorted(Counter(row["route"] for row in rows).items())),
            "by_mode": dict(sorted(Counter(row["mode"] for row in rows).items())),
        },
        "routes": rows,
        "limits": [
            "A route is a work recommendation, not a scientific or lifecycle verdict.",
            "Pair count is a design-screening signal, not a quality score.",
            "Current models and tokenizers were trained primarily on ordinary English; this limits generalisation but does not reverse an observed result.",
            "Only the live register can decide whether a newly filed row changes settlement or lifecycle state.",
        ],
        "model_calls": 0,
        "model_downloads": 0,
    }
    snapshot["content_sha256"] = hashlib.sha256(canonical(snapshot)).hexdigest()
    output.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"counts": snapshot["counts"], "content_sha256": snapshot["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
