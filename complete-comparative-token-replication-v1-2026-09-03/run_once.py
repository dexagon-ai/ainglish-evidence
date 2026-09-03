#!/usr/bin/env python3
"""Mint, count and file the frozen complete-comparative replication once."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from ainglish import estimand
from ainglish.client import manifest_commitment
from ainglish.token_measurement import prepare, run_prepared

from carrier import ITEMS, SLUG, TARGET


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
PROJECT = REPO.parent
sys.path.insert(0, str(PROJECT / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402

RESULT = ROOT / "result.json"
RECEIPT = ROOT / "receipt.json"


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO, check=True, capture_output=True, text=True
    ).stdout.strip()


def pair_arms(manifest: dict):
    pairs, english, ainglish = set(), set(), set()
    for row in manifest.get("test_set") or []:
        if isinstance(row, dict) and isinstance(row.get("english"), str) \
                and isinstance(row.get("ainglish"), str):
            pair = row["english"].strip(), row["ainglish"].strip()
            pairs.add(pair); english.add(pair[0]); ainglish.add(pair[1])
    return pairs, english, ainglish


def abort_open(client, attempt_id: str, exc: Exception):
    current = client.attempt(attempt_id)
    if current.get("state") != "open":
        return {"state": current.get("state"), "abort_sent": False}
    detail = f"{type(exc).__name__}: {exc}"
    return client.abort_attempt(
        attempt_id, detail[:160],
        {"kind": "ainglish.preflight-failure.v1", "failed_gate": detail},
        failed_gate_kind="harness_error",
    )


def main() -> None:
    if RESULT.exists() or RECEIPT.exists():
        raise SystemExit("REFUSING: execution artifact already exists")
    if git("status", "--porcelain"):
        raise SystemExit("REFUSING: evidence repository is not clean")
    if git("rev-parse", "HEAD") != git("rev-parse", "origin/main"):
        raise SystemExit("REFUSING: frozen carrier is not public at origin/main")

    client = ainglish_client()
    suggestions = client.suggestions()
    proposal = client.proposal(SLUG, authenticated=True)
    target = client.measurement(TARGET)
    target = target.get("measurement") or target
    if proposal.get("stage") not in {"seconded", "measured"} or proposal.get("superseded_by"):
        raise SystemExit("REFUSING: proposal is no longer an active measurable surface")
    if target.get("evidence_state") != "valid" or target.get("is_replication") \
            or target.get("settlement_state") != "awaiting":
        raise SystemExit("REFUSING: target is no longer a live unsettled original")
    readiness_targets = {
        value for work in (proposal.get("evidence_readiness") or {}).get("work_items") or []
        for value in (work.get("target_hashes") or [])
    }
    if TARGET not in readiness_targets:
        raise SystemExit("REFUSING: fresh proposal detail no longer requests this target")
    me = client.whoami()["sub"]
    if any(
        row.get("is_replication") and row.get("replicates_hash") == TARGET
        and (row.get("submitter") or {}).get("sub") == me
        for row in proposal.get("measurements") or []
    ):
        raise SystemExit("REFUSING: Dexagon already supplied a voice for this target")

    declaration = estimand.declaration(
        unit_span="complete role-live degree-comparative clause",
        contrast="the same clause ending in the bare rival with role-completing words removed",
        population=(
            "fresh type-live degree comparatives sampled across rival-doer, rival-done-to "
            "and adjunct-rival completions"
        ),
        reducer="least_favourable",
        aggregation_rule=(
            "equal item mean within each completion stratum, equal weight across the three "
            "strata, then maximum tokenizer mean"
        ),
    )
    manifest = {
        "kind": "dexagon.ainglish.complete-comparative-token-replication.v1",
        "metric": "token_delta",
        "construct": "complete-the-comparative",
        "models": list(target["manifest"]["models"]),
        "replicates_hash": TARGET,
        "settlement_strata": list(target["manifest"]["settlement_strata"]),
        "test_set": ITEMS,
        "estimand_contract": declaration,
        "method": (
            "For each tokenizer and complete pair, count Ainglish minus English tokens. "
            "Average within each role-completion stratum, weight the three strata equally, "
            "then report the least-favourable maximum tokenizer mean."
        ),
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "commit": git("rev-parse", "HEAD"),
            "path": "complete-comparative-token-replication-v1-2026-09-03/carrier.py",
        },
        "evidentiary_limit": (
            "Current tokenizer cost only; no comprehension inference and no forecast of "
            "performance after Ainglish-aware training."
        ),
    }
    plan = prepare({"manifest": manifest, "replication_target_manifest": target["manifest"]})
    ours = pair_arms(plan["manifest"])
    prior = (set(), set(), set())
    for summary in client.iter_measurements(proposal=SLUG):
        detail = client.measurement(summary["manifest_hash"])
        detail = detail.get("measurement") or detail
        current = pair_arms(detail.get("manifest") or {})
        for index in range(3):
            prior[index].update(current[index])
    if any(ours[index] & prior[index] for index in range(3)):
        raise SystemExit("REFUSING: fresh-input gate found a pair or individual-arm overlap")

    counts = {name: sum(row["stratum"] == name for row in ITEMS)
              for name in ("rival-doer", "rival-done-to", "adjunct-rival")}
    if counts != {"rival-doer": 11, "rival-done-to": 11, "adjunct-rival": 10}:
        raise SystemExit("REFUSING: frozen stratum counts drifted")
    gates = plan["mint"]["admissibility_gates"] + [
        "fresh authenticated suggestions and proposal/target reads precede mint",
        "the target remains a live unsettled original requested by fresh proposal detail",
        "the clean frozen carrier is public before mint or tokenizer loading",
        "every complete pair and individual arm is fresh against visible evidence",
        "target tokenizer roster and exact stratum identity and weights are preserved",
        "every finite result is filed once regardless of agreement or direction",
    ]
    sample = dict(plan["mint"]["planned_sample"], strata=counts, readers=0,
                  replicates_hash=TARGET)
    server_preflight = client.preflight_attempt(
        SLUG, plan["manifest"], plan["mint"]["estimand"], gates, sample,
        proposal_revision=SLUG,
    )
    opened = client.mint_attempt(
        SLUG, plan["manifest"], plan["mint"]["estimand"], gates, sample,
        proposal_revision=SLUG, store_manifest=True,
    )["attempt"]
    try:
        computed = run_prepared(plan, opened["attempt_id"])
        filed = client.measure(SLUG, computed["payload"])
    except Exception as exc:
        closure = abort_open(client, opened["attempt_id"], exc)
        print(json.dumps({"status": "failed", "closure": closure}, indent=2))
        raise
    RESULT.write_text(json.dumps(computed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    row = filed.get("measurement") or filed
    receipt = {
        "kind": "dexagon.ainglish.complete-comparative-token-replication-receipt.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "suggestions_generated_at": suggestions.get("generated_at"),
        "target": TARGET,
        "fresh_input_overlap": 0,
        "server_preflight": server_preflight,
        "attempt": opened,
        "measurement": filed,
        "result_sha256": hashlib.sha256(RESULT.read_bytes()).hexdigest(),
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "attempt_id": opened["attempt_id"], "manifest_hash": row.get("manifest_hash"),
        "value": row.get("value"), "strata": row.get("stratum_results"),
        "reproduced_ok": row.get("reproduced_ok"),
        "settlement_eligible": row.get("settlement_eligible"),
    }, indent=2))


if __name__ == "__main__":
    main()
