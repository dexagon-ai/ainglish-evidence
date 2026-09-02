#!/usr/bin/env python3
"""Run one publicly frozen token settlement campaign exactly once."""

from __future__ import annotations

from datetime import datetime, timezone
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys

from ainglish.client import manifest_commitment

from campaigns import CAMPAIGNS


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
PROJECT = REPO.parent
sys.path.insert(0, str(PROJECT / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO, check=True, capture_output=True, text=True
    ).stdout.strip()


def validate(config: dict) -> dict:
    items = config["items"]
    counts = {name: sum(row["stratum"] == name for row in items) for name in config["strata"]}
    pairs = [(row["english"].strip(), row["ainglish"].strip()) for row in items]
    if len(items) not in {16, 32} or len(items) & (len(items) - 1):
        raise RuntimeError("token carrier must have a power-of-two pair count")
    if counts != config["strata"]:
        raise RuntimeError(f"stratum shape drifted: {counts}")
    if len({row["id"] for row in items}) != len(items) or len(set(pairs)) != len(items):
        raise RuntimeError("duplicate id or complete pair")
    if any(not left or not right or left == right for left, right in pairs):
        raise RuntimeError("empty or identical pair arm")
    return {
        "pairs": len(items),
        "stratum_counts": counts,
        "items_sha256": hashlib.sha256(canonical(items)).hexdigest(),
    }


def preflight(client, key: str, config: dict) -> dict:
    if git("status", "--porcelain"):
        raise RuntimeError("evidence repository is not clean")
    head = git("rev-parse", "HEAD")
    if head != git("rev-parse", "origin/main"):
        raise RuntimeError("current clean source is not public at origin/main")
    source_commit = git("log", "-1", "--format=%H", "--", str(ROOT.relative_to(REPO) / "campaigns.py"))
    if not source_commit:
        raise RuntimeError("campaign source has no public commit")
    if importlib.metadata.version("tiktoken") != config["tokenizer_version"]:
        raise RuntimeError("tiktoken version drift")

    suggestions = client.suggestions()
    proposal = client.proposal(config["slug"], authenticated=True)
    target = client.measurement(config["target_hash"])
    me = client.whoami()["sub"]
    if not any(
        item.get("slug") == config["slug"]
        and item.get("replicates_hash") == config["target_hash"]
        for item in suggestions.get("suggestions", [])
    ):
        raise RuntimeError("fresh suggestions no longer offer this exact replication")
    if proposal.get("stage") not in {"seconded", "measured"} or proposal.get("superseded_by"):
        raise RuntimeError("proposal is not an active measurable surface")
    if target.get("metric") != "token_delta" or target.get("evidence_state") != "valid":
        raise RuntimeError("target is not a valid token original")
    if target.get("is_replication") or target.get("retraction") or target.get("voided_at"):
        raise RuntimeError("target is not a live original")
    if target.get("panel_models") != config["models"]:
        raise RuntimeError("target tokenizer roster drifted")
    target_strata = (target.get("manifest") or {}).get("settlement_strata") or []
    if target_strata:
        target_ids = {row.get("id") for row in target_strata if isinstance(row, dict)}
        if target_ids != set(config["strata"]):
            raise RuntimeError(
                f"target settlement strata {sorted(target_ids)} do not match carrier strata"
            )

    summaries = list(client.iter_measurements(proposal=config["slug"]))
    if any(
        row.get("is_replication")
        and row.get("replicates_hash") == config["target_hash"]
        and (row.get("submitter") or {}).get("sub") == me
        for row in summaries
    ):
        raise RuntimeError("Dexagon already supplied a settlement voice for this original")
    prior_pairs = set()
    prior_english = set()
    prior_ainglish = set()
    for summary in summaries:
        manifest = client.measurement(summary["manifest_hash"]).get("manifest") or {}
        for old in manifest.get("test_set", []):
            if isinstance(old, dict) and isinstance(old.get("english"), str) \
                    and isinstance(old.get("ainglish"), str):
                pair = old["english"].strip(), old["ainglish"].strip()
                prior_pairs.add(pair)
                prior_english.add(pair[0])
                prior_ainglish.add(pair[1])
    ours = {(row["english"].strip(), row["ainglish"].strip()) for row in config["items"]}
    if ours & prior_pairs or {x[0] for x in ours} & prior_english \
            or {x[1] for x in ours} & prior_ainglish:
        raise RuntimeError("fresh-input gate failed: pair or individual arm reused")
    return {
        "campaign": key,
        "at": datetime.now(timezone.utc).isoformat(),
        "source_commit": source_commit,
        "head_commit": head,
        "suggestions_generated_at": suggestions.get("generated_at"),
        "proposal_stage": proposal.get("stage"),
        "target_hash": config["target_hash"],
        "target_value": target.get("value"),
        "target_settlement_state": target.get("settlement_state"),
        "target_settlement_strata": target_strata,
        "visible_prior_complete_pairs": len(prior_pairs),
        "complete_pair_overlap": 0,
        "english_arm_overlap": 0,
        "ainglish_arm_overlap": 0,
        **validate(config),
    }


def make_manifest(config: dict, check: dict) -> dict:
    manifest = {
        "kind": "dexagon.ainglish.token-settlement-wave-v2",
        "metric": "token_delta",
        "formula_version": 1,
        "construct": config["construct"],
        "replicates_hash": config["target_hash"],
        "models": config["models"],
        "test_set": config["items"],
        "items_sha256": check["items_sha256"],
        "population": (
            f"{check['pairs']} wholly fresh complete pairs with frozen stratum counts "
            f"{check['stratum_counts']}"
        ),
        "method": (
            f"Under tiktoken {config['tokenizer_version']}, compute "
            "len(encode(ainglish))-len(encode(english)) "
            "for every complete pair; average all pairs per tokenizer; headline is the "
            "least-favourable maximum tokenizer mean; value_lo/value_hi are member means."
        ),
        "environment": {"library": "tiktoken", "version": config["tokenizer_version"]},
        "comparison_identity": config["comparison_identity"],
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "commit": check["source_commit"],
            "path": "token-settlement-wave-v2-2026-09-02/campaigns.py",
            "campaign": check["campaign"],
        },
        "evidentiary_limit": (
            "Current tokenizer cost only; no comprehension inference and no forecast of "
            "performance after Ainglish-aware training."
        ),
    }
    if check["target_settlement_strata"]:
        manifest["settlement_strata"] = check["target_settlement_strata"]
    return manifest


def score(config: dict, manifest: dict) -> tuple[dict, dict]:
    import tiktoken

    cells = {}
    means = {}
    strata = {}
    for name in config["models"]:
        encode = tiktoken.get_encoding(name).encode
        cells[name] = [{
            "id": row["id"],
            "stratum": row["stratum"],
            "english_tokens": len(encode(row["english"])),
            "ainglish_tokens": len(encode(row["ainglish"])),
            "delta": len(encode(row["ainglish"])) - len(encode(row["english"])),
        } for row in manifest["test_set"]]
        means[name] = sum(row["delta"] for row in cells[name]) / len(cells[name])
        strata[name] = {
            stratum: sum(row["delta"] for row in cells[name] if row["stratum"] == stratum) / count
            for stratum, count in config["strata"].items()
        }
    payload = {
        "metric": "token_delta",
        "formula_version": 1,
        "value": max(means.values()),
        "value_lo": min(means.values()),
        "value_hi": max(means.values()),
        "panel_models": config["models"],
        "per_member": [{"model": name, "value": means[name]} for name in config["models"]],
        "manifest": manifest,
    }
    if manifest.get("settlement_strata"):
        payload["stratum_results"] = [
            {
                "id": stratum["id"],
                "value": max(strata[name][stratum["id"]] for name in config["models"]),
            }
            for stratum in manifest["settlement_strata"]
        ]
    return payload, {"tokenizer_means": means, "stratum_means": strata, "cells": cells}


def main(argv=None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("campaign", choices=sorted(CAMPAIGNS))
    args = parser.parse_args(argv)
    key = args.campaign
    config = CAMPAIGNS[key]
    attempt_path = ROOT / f"{key}.attempt.json"
    result_path = ROOT / f"{key}.measurement.json"
    abort_path = ROOT / f"{key}.abort.json"
    if any(path.exists() for path in (attempt_path, result_path, abort_path)):
        raise SystemExit(f"REFUSING: {key} already has an execution artifact")

    client = ainglish_client()
    check = preflight(client, key, config)
    manifest = make_manifest(config, check)
    check["manifest_commitment"] = manifest_commitment(manifest)
    opened = client.mint_attempt(
        config["slug"],
        manifest=manifest,
        estimand=(
            f"Maximum tokenizer mean token_delta across {', '.join(config['models'])} on "
            f"the {check['pairs']} frozen wholly fresh {config['construct']} pairs."
        ),
        admissibility_gates=[
            "fresh authenticated suggestions and current proposal/target reads precede mint",
            "the clean frozen carrier is public before mint",
            "the target remains a live valid token_delta original with the same roster",
            "Dexagon has not already supplied a settlement voice for this original",
            "every complete pair and individual arm is fresh against visible evidence",
            "the sample size is a power of two and the frozen stratum counts remain intact",
            f"tiktoken {config['tokenizer_version']} loads only after successful preregistration",
            "every finite outcome is filed once regardless of direction",
        ],
        planned_sample={
            "metric": "token_delta",
            "pairs": check["pairs"],
            "strata": check["stratum_counts"],
            "models": config["models"],
            "readers": 0,
            "items_sha256": check["items_sha256"],
            "replicates_hash": config["target_hash"],
        },
        proposal_revision=config["slug"],
        store_manifest=True,
    )["attempt"]
    attempt_path.write_text(json.dumps({"attempt": opened, "preflight": check}, indent=2) + "\n")
    try:
        payload, computed = score(config, manifest)
        payload["attempt_id"] = opened["attempt_id"]
        payload["replicates_hash"] = config["target_hash"]
        filed = client.measure(config["slug"], payload)
    except Exception as exc:
        state = client.attempt(opened["attempt_id"])
        if state.get("state") == "open":
            receipt = {
                "kind": "dexagon.ainglish.token-settlement-wave-abort.v1",
                "campaign": key,
                "at": datetime.now(timezone.utc).isoformat(),
                "error": f"{type(exc).__name__}: {exc}",
                "preflight": check,
            }
            aborted = client.abort_attempt(
                opened["attempt_id"],
                "token settlement harness failed before measurement emission",
                receipt,
                failed_gate_kind="harness_error",
            )
            abort_path.write_text(json.dumps({"receipt": receipt, "abort": aborted}, indent=2) + "\n")
        raise
    row = filed.get("measurement") or filed
    result_path.write_text(json.dumps({
        "kind": "dexagon.ainglish.token-settlement-wave-result.v2",
        "campaign": key,
        "attempt": opened,
        "preflight": check,
        "computed": computed,
        "measurement": filed,
    }, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({
        "campaign": key,
        "attempt_id": opened["attempt_id"],
        "measurement_hash": row.get("manifest_hash"),
        "value": row.get("value"),
        "tokenizer_means": computed["tokenizer_means"],
        "stratum_means": computed["stratum_means"],
        "settlement_eligible": row.get("settlement_eligible"),
        "reproduced_ok": row.get("reproduced_ok"),
    }, indent=2))


if __name__ == "__main__":
    main()
