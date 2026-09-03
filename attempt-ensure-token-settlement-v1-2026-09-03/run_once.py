#!/usr/bin/env python3
"""Mint, count and file the frozen attempt/ensure token settlement replication once."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
EVIDENCE_REPO = ROOT.parent
sys.path.insert(0, str(PROJECT / "scripts"))
from local_colony_auth import ainglish_client

from ainglish.client import manifest_commitment
from ainglish.token_measurement import run_prepared

SLUG = "attempt-ensure-say-whether-the-instruction-tolerates-failure"
TARGET = "368021d8306cdaee937fce51c0963a2382cc299ad1f6e2d4fee255d58d2f26b8"
PLAN = ROOT / "prepared.json"
RESULT = ROOT / "result.json"
RECEIPT = ROOT / "receipt.json"


def git(*args: str) -> str:
    import subprocess
    return subprocess.run(
        ["git", *args], cwd=EVIDENCE_REPO, check=True, text=True, capture_output=True
    ).stdout.strip()


def pairs(manifest: dict[str, Any]) -> set[tuple[str, str]]:
    return {
        (row["english"], row["ainglish"])
        for row in manifest.get("test_set") or []
        if isinstance(row, dict) and isinstance(row.get("english"), str)
        and isinstance(row.get("ainglish"), str)
    }


def preflight(client: Any, plan: dict[str, Any]) -> dict[str, Any]:
    suggestions = client.suggestions()
    proposal = client.proposal(SLUG, authenticated=True)
    target = client.measurement(TARGET).get("measurement") or client.measurement(TARGET)
    if proposal.get("stage") not in {"seconded", "measured"}:
        raise RuntimeError(f"proposal stage is no longer measurable: {proposal.get('stage')}")
    if target.get("evidence_state") != "valid" or target.get("settlement_state") != "disputed":
        raise RuntimeError("target is no longer a valid disputed original")
    action = ((proposal.get("progression_path") or {}).get("current_action") or {})
    target_hashes = ((proposal.get("evidence_readiness") or {}).get("work_items") or [])
    if action.get("metric") != "token_delta" and not any(
        TARGET in (row.get("target_hashes") or []) for row in target_hashes
    ):
        raise RuntimeError("fresh proposal detail no longer routes token settlement")
    prior_pairs: set[tuple[str, str]] = set()
    for row in proposal.get("measurements") or []:
        manifest = row.get("manifest")
        if not isinstance(manifest, dict) and row.get("manifest_hash"):
            detail = client.measurement(row["manifest_hash"])
            manifest = (detail.get("measurement") or detail).get("manifest")
        if isinstance(manifest, dict):
            prior_pairs.update(pairs(manifest))
    overlap = sorted(pairs(plan["manifest"]) & prior_pairs)
    if overlap:
        raise RuntimeError(f"fresh-input gate failed for {len(overlap)} complete pair(s)")
    if manifest_commitment(plan["manifest"]) != plan["manifest_commitment"]:
        raise RuntimeError("prepared plan commitment does not match")
    if git("status", "--porcelain"):
        raise RuntimeError("evidence repository is not clean")
    git("merge-base", "--is-ancestor", "HEAD", "origin/main")
    return {
        "suggestions_generated_at": suggestions.get("generated_at"),
        "proposal_stage": proposal.get("stage"),
        "target_state": target.get("settlement_state"),
        "target_value": target.get("value"),
        "target_submitter": (target.get("submitter") or {}).get("name"),
        "fresh_complete_pair_overlap": 0,
        "pair_count": plan["pair_count"],
        "manifest_commitment": plan["manifest_commitment"],
    }


def abort_open(client: Any, attempt_id: str, exc: Exception) -> Any:
    attempt = client.attempt(attempt_id)
    if attempt.get("state") != "open":
        return {"state": attempt.get("state"), "abort_sent": False}
    detail = f"{type(exc).__name__}: {exc}"
    return client.abort_attempt(
        attempt_id,
        detail[:160],
        {
            "kind": "ainglish.preflight-failure.v1",
            "attempt_id": attempt_id,
            "failed_gate_kind": "harness_error",
            "failed_gate": detail,
        },
        failed_gate_kind="harness_error",
    )


def main() -> None:
    if RESULT.exists() or RECEIPT.exists():
        raise SystemExit("REFUSING: result or receipt already exists")
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    client = ainglish_client()
    checked = preflight(client, plan)
    if "--preflight" in sys.argv:
        print(json.dumps(checked, indent=2, sort_keys=True))
        return
    opened = client.mint_attempt(
        SLUG,
        manifest=plan["manifest"],
        estimand=plan["mint"]["estimand"],
        admissibility_gates=plan["mint"]["admissibility_gates"] + [
            "target remains a valid disputed original",
            "all complete English/Ainglish pairs are disjoint from every prior filed manifest",
            "every finite result is filed once, including disagreement with the target",
        ],
        planned_sample=plan["mint"]["planned_sample"],
    )["attempt"]
    try:
        result = run_prepared(plan, opened["attempt_id"])
        filed = client.measure(SLUG, result["payload"])
    except Exception as exc:
        closure = abort_open(client, opened["attempt_id"], exc)
        print(json.dumps({"status": "aborted", "closure": closure}, indent=2))
        raise
    RESULT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    receipt = {
        "kind": "ainglish.token-settlement-replication-receipt.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "proposal": SLUG,
        "target_hash": TARGET,
        "preflight": checked,
        "attempt": opened,
        "result": {
            "value": result["payload"]["value"],
            "value_lo": result["payload"]["value_lo"],
            "value_hi": result["payload"]["value_hi"],
            "per_member": result["payload"]["per_member"],
            "manifest_commitment": plan["manifest_commitment"],
        },
        "measurement": filed,
        "result_sha256": hashlib.sha256(RESULT.read_bytes()).hexdigest(),
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
