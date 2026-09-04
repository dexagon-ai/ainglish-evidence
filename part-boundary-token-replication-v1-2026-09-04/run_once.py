#!/usr/bin/env python3
"""Mint, execute and file the frozen part-boundary token replication once."""

from __future__ import annotations

from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys

from ainglish.client import manifest_commitment
from ainglish.token_measurement import run_prepared, verify_payload


ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT.parent
PROJECT = EVIDENCE.parent
sys.path.insert(0, str(PROJECT / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402

SLUG = "part-chosen-rule-part-capped-limiter-was-the-edge-of-the-set"
TARGET = "13a722dd4d8b0206a42ff6450c5de1fea05a0f828d14254c61889bd7af894e83"
RESULT = ROOT / "result.json"
RECEIPT = ROOT / "receipt.json"


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=EVIDENCE, check=True, text=True, capture_output=True
    ).stdout.strip()


def main() -> None:
    if RESULT.exists() or RECEIPT.exists():
        raise SystemExit("REFUSING: this one-shot carrier already has an outcome")
    if importlib.metadata.version("ainglish") != "0.2.53":
        raise SystemExit("REFUSING: requires ainglish 0.2.53")
    if importlib.metadata.version("tiktoken") != "0.14.0":
        raise SystemExit("REFUSING: requires tiktoken 0.14.0")
    if git("status", "--porcelain"):
        raise SystemExit("REFUSING: evidence repository must be clean")
    if git("rev-parse", "HEAD") != git("rev-parse", "origin/main"):
        raise SystemExit("REFUSING: frozen carrier commit must be published as origin/main")

    plan = json.loads((ROOT / "plan.json").read_text(encoding="utf-8"))
    if manifest_commitment(plan["manifest"]) != plan["manifest_commitment"]:
        raise SystemExit("REFUSING: frozen plan commitment mismatch")
    if plan["manifest"].get("replicates_hash") != TARGET:
        raise SystemExit("REFUSING: target changed in frozen plan")

    client = ainglish_client()
    suggestions = client.suggestions()
    matching_suggestions = [
        row for row in suggestions.get("suggestions") or []
        if row.get("replicates_hash") == TARGET
    ]
    if matching_suggestions and not any(row.get("executable_now") is True for row in matching_suggestions):
        raise SystemExit("REFUSING: personalised suggestions mark this target non-executable")
    proposal = client.proposal(SLUG, authenticated=True)
    live_targets = {
        value
        for item in (proposal.get("evidence_readiness") or {}).get("work_items") or []
        for value in item.get("target_hashes") or []
    }
    if TARGET not in live_targets:
        raise SystemExit("REFUSING: fresh proposal no longer requests this target")
    identity = client.whoami()
    prior_own_rows = [
        row for row in proposal.get("measurements") or []
        if row.get("replicates_hash") == TARGET
        and (row.get("submitter") or {}).get("sub") == identity.get("sub")
        and row.get("settlement_eligible") is True
    ]
    if prior_own_rows:
        raise SystemExit("REFUSING: this identity already supplied a settlement-bearing replication")
    print(
        "LIVE PREFLIGHT PASS:", suggestions.get("generated_at"),
        "proposal-work-item=exact",
        "suggestion-row=" + ("present" if matching_suggestions else "rotated-out"),
        flush=True,
    )

    check = client.preflight_attempt(
        SLUG,
        manifest=plan["manifest"],
        estimand=plan["mint"]["estimand"],
        admissibility_gates=plan["mint"]["admissibility_gates"],
        planned_sample=plan["mint"]["planned_sample"],
    )
    opened = client.mint_attempt(
        SLUG,
        manifest=plan["manifest"],
        estimand=plan["mint"]["estimand"],
        admissibility_gates=plan["mint"]["admissibility_gates"],
        planned_sample=plan["mint"]["planned_sample"],
    )["attempt"]
    attempt_id = opened["attempt_id"]
    try:
        result = run_prepared(plan, attempt_id)
        verify_payload(result["payload"])
        filed = client.measure(SLUG, result["payload"])
    except Exception as exc:
        current = client.attempt(attempt_id)
        closure = None
        if current.get("state") == "open":
            closure = client.abort_attempt(
                attempt_id,
                f"{type(exc).__name__}: {exc}"[:160],
                {"kind": "dexagon.ainglish.token-run-abort.v1", "failed_gate": str(exc)},
                failed_gate_kind="harness_error",
            )
        RECEIPT.write_text(json.dumps({
            "state": "aborted", "attempt_id": attempt_id,
            "error": f"{type(exc).__name__}: {exc}", "closure": closure,
        }, indent=2) + "\n", encoding="utf-8")
        raise

    RESULT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt = {
        "kind": "dexagon.ainglish.part-boundary-token-replication-receipt.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "state": "filed",
        "suggestions_generated_at": suggestions.get("generated_at"),
        "proposal_stage_before": proposal.get("stage"),
        "target": TARGET,
        "preflight": check,
        "attempt": opened,
        "computed": {
            "value": result["payload"]["value"],
            "value_lo": result["payload"]["value_lo"],
            "value_hi": result["payload"]["value_hi"],
            "per_member": result["payload"]["per_member"],
            "stratum_results": result["payload"].get("stratum_results"),
            "manifest_hash": manifest_commitment(result["payload"]["manifest"]),
        },
        "server": filed,
    }
    RECEIPT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt["computed"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
