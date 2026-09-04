#!/usr/bin/env python3
"""Preflight, mint, count and file each still-offered carrier exactly once."""

from __future__ import annotations

from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys

from ainglish.client import manifest_commitment


ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT.parent
PROJECT = ROOT.parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=EVIDENCE, check=True, text=True, capture_output=True,
    ).stdout.strip()


def complete_pairs(manifest: dict) -> set[tuple[str, str]]:
    return {
        (row["english"], row["ainglish"])
        for row in manifest.get("test_set") or []
        if isinstance(row, dict)
        and isinstance(row.get("english"), str)
        and isinstance(row.get("ainglish"), str)
    }


def abort(client, attempt_id: str, exc: Exception) -> dict:
    current = client.attempt(attempt_id)
    if current.get("state") != "open":
        return {"state": current.get("state"), "abort_sent": False}
    detail = f"{type(exc).__name__}: {exc}"
    return client.abort_attempt(
        attempt_id,
        detail[:160],
        {"kind": "dexagon.ainglish.progression-token-run-abort.v1", "failed_gate": detail},
        failed_gate_kind="harness_error",
    )


def fresh_preflight(client, identity: dict, meta: dict, manifest: dict) -> dict:
    suggestions = client.suggestions()
    offered = {
        row.get("replicates_hash")
        for row in suggestions.get("suggestions", [])
        if row.get("tier") == "replications" and row.get("executable_now") is True
    }
    if meta["replicates_hash"] not in offered:
        return {"offered": False, "suggestions_generated_at": suggestions.get("generated_at")}

    proposal = client.proposal(meta["slug"], authenticated=True)
    target_hashes = {
        target
        for item in (proposal.get("evidence_readiness") or {}).get("work_items", [])
        for target in (item.get("target_hashes") or [])
    }
    if meta["replicates_hash"] not in target_hashes:
        return {
            "offered": False,
            "suggestions_generated_at": suggestions.get("generated_at"),
            "reason": "target left current evidence work items",
        }
    if proposal.get("stage") not in {"seconded", "measured"} or proposal.get("superseded_by"):
        raise RuntimeError("proposal is no longer current in a measurement-accepting stage")
    if any(
        row.get("replicates_hash") == meta["replicates_hash"]
        and (row.get("submitter") or {}).get("sub") == identity.get("sub")
        and row.get("settlement_eligible") is True
        for row in proposal.get("measurements") or []
    ):
        raise RuntimeError("this principal already supplied a settlement-bearing replication")

    target_response = client.measurement(meta["replicates_hash"])
    target = target_response.get("measurement", target_response)
    target_manifest = target.get("manifest") or {}
    if target.get("metric") != "token_delta" or target_manifest.get("models") != manifest["models"]:
        raise RuntimeError("target metric or tokenizer roster changed")
    method = str(target_manifest.get("method") or "")
    target_version = (target_manifest.get("environment") or {}).get("version")
    if target_version != "0.14.0" and "0.14.0" not in method:
        raise RuntimeError("target does not declare tiktoken 0.14.0")
    if manifest_commitment(manifest) != meta["manifest_sha256"]:
        raise RuntimeError("published manifest commitment mismatch")

    prior_pairs: set[tuple[str, str]] = set()
    for row in proposal.get("measurements") or []:
        prior_manifest = row.get("manifest")
        if not isinstance(prior_manifest, dict) and row.get("manifest_hash"):
            detail = client.measurement(row["manifest_hash"])
            prior_manifest = detail.get("measurement", detail).get("manifest")
        if isinstance(prior_manifest, dict):
            prior_pairs.update(complete_pairs(prior_manifest))
    overlap = complete_pairs(manifest) & prior_pairs
    if overlap:
        raise RuntimeError(f"fresh-input gate found {len(overlap)} complete-pair overlaps")
    # main() proves a clean public carrier once. Receipts from earlier rows in this same one-shot
    # wave are then expected untracked files; each manifest commitment below still guards its row.
    git("merge-base", "--is-ancestor", "HEAD", "origin/main")
    return {
        "offered": True,
        "suggestions_generated_at": suggestions.get("generated_at"),
        "proposal_stage": proposal.get("stage"),
        "target_value": target.get("value"),
        "target_submitter": (target.get("submitter") or {}).get("name"),
        "fresh_complete_pair_overlap": 0,
        "pair_count": len(manifest["test_set"]),
        "tokenizer_roster": manifest["models"],
    }


def main() -> None:
    if importlib.metadata.version("ainglish") != "0.2.53":
        raise SystemExit("REFUSING: requires ainglish 0.2.53")
    if importlib.metadata.version("tiktoken") != "0.14.0":
        raise SystemExit("REFUSING: requires tiktoken 0.14.0")
    if list(ROOT.glob("*.receipt.json")) or (ROOT / "results.json").exists():
        raise SystemExit("REFUSING: this one-shot directory already contains an outcome")
    if git("status", "--porcelain"):
        raise SystemExit("REFUSING: evidence repository must be clean")
    git("merge-base", "--is-ancestor", "HEAD", "origin/main")

    index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    client = ainglish_client()
    identity = client.whoami()
    outcomes = []
    for name, meta in index["campaigns"].items():
        manifest = json.loads((ROOT / meta["file"]).read_text(encoding="utf-8"))
        checked = fresh_preflight(client, identity, meta, manifest)
        if not checked["offered"]:
            outcome = {
                "campaign": name,
                "state": "not_currently_offered",
                "replicates_hash": meta["replicates_hash"],
                "preflight": checked,
            }
            outcomes.append(outcome)
            print("SKIP", json.dumps(outcome, sort_keys=True), flush=True)
            continue

        estimand = (
            f"Legacy aggregate token_delta replication of {meta['replicates_hash']} over 32 wholly fresh "
            f"complete pairs for {meta['construct']}; tiktoken 0.14.0; equal pair mean for cl100k_base, "
            "o200k_base and p50k_base; conservative headline is the maximum tokenizer mean. Preserve the "
            "source's aggregate-only contract and file every finite direction without tuning."
        )
        gates = [
            "fresh authenticated personalized suggestions offer the exact target immediately before mint",
            "the exact target remains in the fresh proposal evidence work items",
            "all 32 complete pairs have zero exact overlap with every prior filed proposal manifest",
            "the target tokenizer roster, tiktoken version and aggregate-only result shape are preserved",
            "the carrier commit is public and the evidence repository is clean before tokenizer import",
            "all finite agreement or disagreement is filed exactly once without retry or item tuning",
        ]
        planned = {
            "items": 32,
            "tokenizers": 3,
            "models": manifest["models"],
            "tiktoken_version": "0.14.0",
            "reader_calls": 0,
        }
        server_preflight = client.preflight_attempt(
            meta["slug"], manifest, estimand, gates, planned, proposal_revision=meta["slug"],
        )
        opened = client.mint_attempt(
            meta["slug"], manifest, estimand, gates, planned, proposal_revision=meta["slug"],
        )["attempt"]
        try:
            # Import only after a successful mint: the tokenizer computation is the measured spend.
            from ainglish.measure import token_delta

            counted = token_delta(
                [(row["english"], row["ainglish"]) for row in manifest["test_set"]],
                manifest["models"],
            )
            if "skipped" in counted:
                raise RuntimeError(str(counted["skipped"]))
            members = [
                {"model": model, "value": counted["by_tokenizer"][model]["mean"]}
                for model in manifest["models"]
            ]
            values = [row["value"] for row in members]
            payload = {
                "attempt_id": opened["attempt_id"],
                "metric": "token_delta",
                "value": max(values),
                "value_lo": min(values),
                "value_hi": max(values),
                "panel_models": manifest["models"],
                "per_member": members,
                "manifest": manifest,
                "replicates_hash": meta["replicates_hash"],
            }
            filed = client.measure(meta["slug"], payload)
        except Exception as exc:
            closure = abort(client, opened["attempt_id"], exc)
            outcome = {
                "campaign": name,
                "state": "aborted",
                "replicates_hash": meta["replicates_hash"],
                "error": f"{type(exc).__name__}: {exc}",
                "closure": closure,
            }
            outcomes.append(outcome)
            print("ABORT", json.dumps(outcome, sort_keys=True), flush=True)
            continue

        outcome = {
            "kind": "dexagon.ainglish.progression-token-settlement-receipt.v2",
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "campaign": name,
            "state": "filed",
            "replicates_hash": meta["replicates_hash"],
            "local_preflight": checked,
            "server_preflight": server_preflight,
            "attempt": opened,
            "result": {
                "value": max(values),
                "value_lo": min(values),
                "value_hi": max(values),
                "per_member": members,
                "manifest_hash": manifest_commitment(manifest),
            },
            "server_measurement": filed,
        }
        (ROOT / f"{name}.receipt.json").write_text(
            json.dumps(outcome, indent=2) + "\n", encoding="utf-8",
        )
        outcomes.append(outcome)
        print("FILED", name, json.dumps(outcome["result"], sort_keys=True), flush=True)

    result = {"kind": "dexagon.ainglish.progression-token-settlement-results.v2", "outcomes": outcomes}
    (ROOT / "results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "outcomes": [
            {"campaign": row["campaign"], "state": row["state"], "result": row.get("result")}
            for row in outcomes
        ]
    }, indent=2))


if __name__ == "__main__":
    main()
