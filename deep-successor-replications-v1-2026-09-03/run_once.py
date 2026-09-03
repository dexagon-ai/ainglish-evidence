#!/usr/bin/env python3
"""Preregister, run, and file the two deterministic successor replications once."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from ainglish.token_measurement import prepare, run_prepared

from campaigns import CAMPAIGNS


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
PROJECT = REPO.parent
sys.path.insert(0, str(PROJECT / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402


def git(*args):
    return subprocess.run(["git", *args], cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()


def arms(manifest):
    rows = manifest.get("test_set") or []
    return ({row["english"].strip() for row in rows}, {row["ainglish"].strip() for row in rows})


def close_open(client, attempt_id, exc):
    state = client.attempt(attempt_id)
    if state.get("state") != "open":
        return
    detail = f"{type(exc).__name__}: {exc}"[:160]
    client.abort_attempt(
        attempt_id, detail,
        {"kind": "ainglish.preflight-failure.v1", "failed_gate_kind": "harness_error", "failed_gate": detail},
        failed_gate_kind="harness_error",
    )


def run_campaign(client, config):
    result_path = ROOT / f"{config['name']}.result.json"
    receipt_path = ROOT / f"{config['name']}.receipt.json"
    if result_path.exists() or receipt_path.exists():
        return {"campaign": config["name"], "state": "already_settled_local"}

    proposal = client.proposal(config["slug"], authenticated=True)
    target_row = client.measurement(config["target_hash"])
    target_row = target_row.get("measurement") or target_row
    target = client.attempt_manifest(config["target_attempt_id"])
    if proposal.get("superseded_by") or proposal.get("stage") not in {"seconded", "measured"}:
        raise RuntimeError(f"{config['name']}: proposal is no longer measurable")
    if target_row.get("manifest_hash") != config["target_hash"] or target_row.get("evidence_state") != "valid":
        raise RuntimeError(f"{config['name']}: target identity or evidence state drifted")
    if target_row.get("settlement_state") != "awaiting" or target_row.get("is_replication"):
        raise RuntimeError(f"{config['name']}: target is no longer an awaiting original")

    manifest = {
        "kind": "dexagon.ainglish.deep-successor-fresh-replication.v1",
        "metric": "token_delta",
        "construct": target["construct"],
        "models": target["models"],
        "test_set": config["test_set"],
        "settlement_strata": target["settlement_strata"],
        "estimand_contract": target["estimand_contract"],
        "replicates_hash": config["target_hash"],
        "method": "Canonical SDK token runner; count every complete pair under each target tokenizer, preserve target strata and least-favourable aggregation, and file every finite direction once.",
        "source": {"repository": "dexagon-ai/ainglish-evidence", "path": "deep-successor-replications-v1-2026-09-03/campaigns.py", "commit": git("rev-parse", "HEAD")},
        "evidentiary_limit": "Current tokenizer cost only; not comprehension and not a forecast of future Ainglish-aware training or tokenizers.",
        "comparison_identity": {
            "comparator_genre": target["comparison_identity"]["comparator_genre"],
            "pair_rendering": target["comparison_identity"]["pair_rendering"],
        },
    }
    plan = prepare({"manifest": manifest, "replication_target_manifest": target})

    prior_english, prior_ainglish = set(), set()
    for summary in client.iter_measurements(proposal=config["slug"]):
        detail = client.measurement(summary["manifest_hash"])
        detail = detail.get("measurement") or detail
        english, ainglish = arms(detail.get("manifest") or {})
        prior_english.update(english)
        prior_ainglish.update(ainglish)
    current_english, current_ainglish = arms(plan["manifest"])
    if current_english & prior_english or current_ainglish & prior_ainglish:
        raise RuntimeError(f"{config['name']}: fresh individual-arm gate found overlap")

    gates = plan["mint"]["admissibility_gates"] + [
        "fresh authenticated proposal and target reads precede mint",
        "the target remains a valid awaiting original with the exact committed manifest",
        "the fresh complete carrier is public before mint",
        "no English or Ainglish arm overlaps any visible prior measurement on this proposal",
        "the replication preserves target metric, two settlement strata, tokenizer roster, estimand contract, unit span, and item count",
        "every finite supportive, null, or adverse result is filed once without outcome retry",
    ]
    sample = dict(plan["mint"]["planned_sample"], strata={row["id"]: 8 for row in target["settlement_strata"]}, readers=0)
    preflight = client.preflight_attempt(config["slug"], plan["manifest"], plan["mint"]["estimand"], gates, sample, proposal_revision=config["slug"])
    opened = client.mint_attempt(config["slug"], plan["manifest"], plan["mint"]["estimand"], gates, sample, proposal_revision=config["slug"], store_manifest=True)["attempt"]
    try:
        computed = run_prepared(plan, opened["attempt_id"])
        filed = client.measure(config["slug"], computed["payload"])
    except Exception as exc:
        close_open(client, opened["attempt_id"], exc)
        raise
    result_path.write_text(json.dumps(computed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    receipt = {
        "kind": "dexagon.ainglish.deep-successor-fresh-replication-receipt.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "campaign": config["name"],
        "fresh_english_overlap": 0,
        "fresh_ainglish_overlap": 0,
        "server_preflight": preflight,
        "attempt": opened,
        "measurement": filed,
        "result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    row = filed.get("measurement") or filed
    return {"campaign": config["name"], "state": "filed", "attempt_id": opened["attempt_id"], "manifest_hash": row.get("manifest_hash"), "value": row.get("value"), "settlement_state": row.get("settlement_state")}


def main():
    tracked_drift = subprocess.run(
        ["git", "diff", "--quiet", "--", ROOT.name], cwd=REPO
    ).returncode
    untracked_source = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "--", ROOT.name],
        cwd=REPO, check=True, capture_output=True, text=True,
    ).stdout.strip()
    if tracked_drift or untracked_source:
        raise SystemExit("REFUSING: this campaign's frozen source has local drift")
    if git("rev-parse", "HEAD") != git("rev-parse", "origin/main"):
        raise SystemExit("REFUSING: frozen source is not public at origin/main")
    client = ainglish_client()
    client.suggestions()  # discovery refresh; the rotating shortlist is not exhaustive
    print(json.dumps([run_campaign(client, config) for config in CAMPAIGNS], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
