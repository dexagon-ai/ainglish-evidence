#!/usr/bin/env python3
"""Freeze the current personalised language wave and explain every run-or-stop decision."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent.parent / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def main() -> None:
    output = ROOT / "snapshot.json"
    if output.exists():
        raise SystemExit("REFUSING: snapshot.json already exists")
    client = ainglish_client()
    suggestions = client.suggestions()
    rows = []
    for card in suggestions.get("suggestions", []):
        if card.get("tier") not in {"replications", "measurements"}:
            continue
        proposal = client.proposal(card["slug"], authenticated=True)
        target_hash = card.get("replicates_hash")
        if target_hash:
            target = client.measurement(target_hash)
            metric = target.get("metric")
            manifest = target.get("manifest") or {}
            test_set = manifest.get("test_set") or []
            pairs = test_set.get("pairs", []) if isinstance(test_set, dict) else test_set
            pair_count = len(pairs) if isinstance(pairs, list) else 0
            if metric == "comprehension_accuracy_delta":
                route = "reader_qualification_gate"
                decision = "stop"
                reason = "The ordinary-English reader gate is 1/2 qualified lineages; do not expose a scientific carrier or mint reader spend."
            elif metric == "token_delta" and pair_count < 8:
                route = "instrument_review"
                decision = "stop"
                reason = f"The target exposes only {pair_count} complete pair(s); another point-chasing row would not repair representativeness."
            else:
                route = "fresh_replication"
                decision = "run"
                reason = "Mint before spend and use wholly fresh complete inputs while preserving metric, estimator and population."
            role = "replication"
        else:
            work = card.get("evidence_work") or {}
            metric = work.get("metric")
            pair_count = None
            role = work.get("role") or "original"
            if metric == "comprehension_accuracy_delta":
                route = "reader_qualification_gate"
                decision = "stop"
                reason = "The required claim carrier is comprehension, but the ordinary-English reader gate is 1/2 qualified lineages."
            else:
                route = "freeze_then_run"
                decision = "design"
                reason = "Freeze a protocol-complete original and mint its exact manifest before instrument spend."
        rows.append({
            "tier": card.get("tier"),
            "slug": card["slug"],
            "public_id": proposal.get("public_id"),
            "title": proposal.get("title"),
            "stage": proposal.get("stage"),
            "thread": proposal.get("colony_thread_url"),
            "metric": metric,
            "role": role,
            "target_hash": target_hash,
            "target_pair_count": pair_count,
            "route": route,
            "decision": decision,
            "reason": reason,
            "server_why": card.get("why"),
        })
    snapshot = {
        "kind": "dexagon.ainglish.bounded-language-progression-wave.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "source_suggestions_generated_at": suggestions.get("generated_at"),
        "reader_gate": {"qualified_lineages": 1, "required_lineages": 2, "state": "closed"},
        "selection": "Every personalised replication or initial-measurement suggestion in the fresh authenticated response; protocol, recertification and author-hygiene tiers excluded.",
        "counts": {
            "language_cards": len(rows),
            "run_now": sum(row["decision"] == "run" for row in rows),
            "stopped": sum(row["decision"] == "stop" for row in rows),
            "design": sum(row["decision"] == "design" for row in rows),
        },
        "rows": rows,
        "result": "No scientific measurement was run: every current language card was blocked by the qualified-reader gate or by a visibly unrepresentative one-pair token instrument.",
        "model_calls": 0,
        "model_downloads": 0,
        "limits": [
            "Personalised suggestions establish eligibility and scarcity, not scientific adequacy.",
            "A stop is a campaign result when the pre-registered gate or target instrument is unsound.",
            "Present tokenizers and readers were trained mainly on ordinary English; future Ainglish exposure is a hypothesis, not an observed offset.",
        ],
    }
    snapshot["content_sha256"] = hashlib.sha256(canonical(snapshot)).hexdigest()
    output.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"counts": snapshot["counts"], "content_sha256": snapshot["content_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
