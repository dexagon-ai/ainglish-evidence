#!/usr/bin/env python3
"""File the owned mean/median successor, then retire its legacy predecessor."""

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

from campaigns import MEAN_SUCCESSOR as CONFIG


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
PROJECT = REPO.parent
sys.path.insert(0, str(PROJECT / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402

RESULT = ROOT / "mean-successor-result.json"
RECEIPT = ROOT / "mean-successor-retirement.json"


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO, check=True, capture_output=True, text=True
    ).stdout.strip()


def pairs(manifest: dict) -> set[tuple[str, str]]:
    return {
        (row["english"].strip(), row["ainglish"].strip())
        for row in manifest.get("test_set") or []
        if isinstance(row, dict) and isinstance(row.get("english"), str)
        and isinstance(row.get("ainglish"), str)
    }


def build_manifest(client) -> dict:
    declaration = estimand.declaration(
        unit_span="complete statistic assertion with exact finite population reference",
        contrast=(
            "marked mean-of or median-of assertion versus its complete careful-English "
            "statistic and population-reference assertion"
        ),
        population=(
            "32 frozen wholly fresh assertions over 16 exact finite population references, "
            "balanced 16 mean-of and 16 median-of"
        ),
        reducer="least_favourable",
        aggregation_rule=(
            "equal item mean within each form stratum, equal weight across the two form "
            "strata, then maximum tokenizer mean"
        ),
    )
    base = {
        "kind": "dexagon.ainglish.legacy-token-successor.v1",
        "metric": "token_delta",
        "construct": "mean-of(<population-ref>) / median-of(<population-ref>)",
        "models": CONFIG["models"],
        "test_set": CONFIG["test_set"],
        "settlement_strata": CONFIG["settlement_strata"],
        "estimand_contract": declaration,
        "method": (
            "Under the declared tiktoken version, count len(encode(ainglish)) minus "
            "len(encode(english)) for every frozen complete pair; average within each "
            "form stratum, weight the two strata equally, and report the least-favourable "
            "maximum tokenizer mean."
        ),
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "path": "legacy-token-contract-repair-v1-2026-09-03/campaigns.py",
            "commit": git("rev-parse", "HEAD"),
        },
        "evidentiary_limit": (
            "This measures current tokenizer cost only. It neither measures comprehension "
            "nor forecasts token cost after Ainglish appears in future training data and tokenizers."
        ),
    }
    return client.legacy_repair_manifest(
        CONFIG["source_attempt_id"], "token_delta", base, author_path=True
    )


def abort_open(client, attempt_id: str, exc: Exception):
    current = client.attempt(attempt_id)
    if current.get("state") != "open":
        return {"state": current.get("state"), "abort_sent": False}
    detail = f"{type(exc).__name__}: {exc}"
    return client.abort_attempt(
        attempt_id,
        detail[:160],
        {
            "kind": "ainglish.preflight-failure.v1",
            "failed_gate_kind": "harness_error",
            "failed_gate": detail,
        },
        failed_gate_kind="harness_error",
    )


def main() -> None:
    if RESULT.exists() or RECEIPT.exists():
        raise SystemExit("REFUSING: successor execution artifacts already exist")
    if git("status", "--porcelain"):
        raise SystemExit("REFUSING: evidence repository is not clean")
    if git("rev-parse", "HEAD") != git("rev-parse", "origin/main"):
        raise SystemExit("REFUSING: frozen source is not public at origin/main")

    client = ainglish_client()
    suggestions = client.suggestions()
    proposal = client.proposal(CONFIG["slug"], authenticated=True)
    source = client.measurement(CONFIG["source_hash"])
    source = source.get("measurement") or source
    me = client.whoami()["sub"]
    if proposal.get("stage") not in {"seconded", "measured"} or proposal.get("superseded_by"):
        raise SystemExit("REFUSING: proposal is no longer an active measurable surface")
    if source.get("attempt_id") != CONFIG["source_attempt_id"]:
        raise SystemExit("REFUSING: source attempt identity drifted")
    if (source.get("submitter") or {}).get("sub") != me or source.get("is_replication"):
        raise SystemExit("REFUSING: source is not Dexagon's original")
    if source.get("evidence_state") != "valid" or source.get("settlement_state") != "disputed":
        raise SystemExit("REFUSING: source is no longer a live disputed legacy original")

    manifest = build_manifest(client)
    plan = prepare({"manifest": manifest})
    prior_pairs, prior_english, prior_ainglish = set(), set(), set()
    for summary in client.iter_measurements(proposal=CONFIG["slug"]):
        detail = client.measurement(summary["manifest_hash"])
        detail = detail.get("measurement") or detail
        for english, ainglish in pairs(detail.get("manifest") or {}):
            prior_pairs.add((english, ainglish))
            prior_english.add(english)
            prior_ainglish.add(ainglish)
    ours = pairs(plan["manifest"])
    if ours & prior_pairs or {x[0] for x in ours} & prior_english \
            or {x[1] for x in ours} & prior_ainglish:
        raise SystemExit("REFUSING: fresh-input gate found a complete-pair or arm overlap")

    gates = plan["mint"]["admissibility_gates"] + [
        "fresh authenticated suggestions and current proposal/source reads precede mint",
        "the source remains Dexagon's live disputed original",
        "the clean frozen carrier is public before mint",
        "every complete pair and individual arm is fresh against visible proposal evidence",
        "the carrier is balanced across mean-of and median-of and has power-of-two size",
        "every finite result is filed once regardless of direction",
    ]
    sample = dict(plan["mint"]["planned_sample"],
                  strata={"mean-of": 16, "median-of": 16}, readers=0)
    server_preflight = client.preflight_attempt(
        CONFIG["slug"], plan["manifest"], plan["mint"]["estimand"], gates, sample,
        proposal_revision=CONFIG["slug"],
    )
    opened = client.mint_attempt(
        CONFIG["slug"], plan["manifest"], plan["mint"]["estimand"], gates, sample,
        proposal_revision=CONFIG["slug"], store_manifest=True,
    )["attempt"]
    try:
        computed = run_prepared(plan, opened["attempt_id"])
        filed = client.measure(CONFIG["slug"], computed["payload"])
        row = filed.get("measurement") or filed
        if row.get("attempt_id") != opened["attempt_id"]:
            raise RuntimeError("filed measurement did not preserve the successor attempt id")
        retirement = client.retire_legacy_measurement_contract(
            CONFIG["source_attempt_id"],
            opened["attempt_id"],
            (
                "Replaced this legacy original with a wholly fresh, preregistered 32-pair "
                "original that declares complete comparison and estimand identity, preserves "
                "the three-tokenizer population, and separates mean-of from median-of strata."
            ),
        )
    except Exception as exc:
        abort = abort_open(client, opened["attempt_id"], exc)
        print(json.dumps({"status": "failed", "attempt": opened, "closure": abort}, indent=2))
        raise

    RESULT.write_text(json.dumps(computed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    receipt = {
        "kind": "dexagon.ainglish.legacy-token-successor-receipt.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "suggestions_generated_at": suggestions.get("generated_at"),
        "proposal": CONFIG["slug"],
        "source_attempt_id": CONFIG["source_attempt_id"],
        "source_manifest_hash": CONFIG["source_hash"],
        "fresh_input_overlap": 0,
        "manifest_commitment": manifest_commitment(plan["manifest"]),
        "server_preflight": server_preflight,
        "successor_attempt": opened,
        "measurement": filed,
        "retirement": retirement,
        "result_sha256": hashlib.sha256(RESULT.read_bytes()).hexdigest(),
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "source_attempt_id": CONFIG["source_attempt_id"],
        "successor_attempt_id": opened["attempt_id"],
        "successor_manifest_hash": row.get("manifest_hash"),
        "value": row.get("value"),
        "retirement_state": retirement,
    }, indent=2))


if __name__ == "__main__":
    main()
