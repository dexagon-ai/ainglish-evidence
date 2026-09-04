#!/usr/bin/env python3
"""Mint, count, and file each still-offered legacy token replication once."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys

from ainglish.client import manifest_commitment
from ainglish.measure import token_delta


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
EVIDENCE = ROOT.parent
sys.path.insert(0, str(PROJECT / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402


def pairs(manifest: dict) -> set[tuple[str, str]]:
    return {
        (row["english"], row["ainglish"])
        for row in manifest.get("test_set") or []
        if isinstance(row, dict) and isinstance(row.get("english"), str) and isinstance(row.get("ainglish"), str)
    }


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=EVIDENCE, check=True, text=True, capture_output=True).stdout.strip()


def abort(client, attempt_id: str, exc: Exception) -> dict:
    current = client.attempt(attempt_id)
    if current.get("state") != "open":
        return {"state": current.get("state"), "abort_sent": False}
    detail = f"{type(exc).__name__}: {exc}"
    return client.abort_attempt(
        attempt_id, detail[:160],
        {"kind": "dexagon.ainglish.legacy-token-run-abort.v1", "failed_gate": detail},
        failed_gate_kind="harness_error",
    )


def preflight(client, meta: dict, manifest: dict) -> dict:
    suggestions = client.suggestions()
    offered = {row.get("replicates_hash") for row in suggestions.get("suggestions", []) if row.get("tier") == "replications"}
    if meta["replicates_hash"] not in offered:
        return {"offered": False, "suggestions_generated_at": suggestions.get("generated_at")}
    proposal = client.proposal(meta["slug"], authenticated=True)
    live_targets = {target for item in (proposal.get("evidence_readiness") or {}).get("work_items", []) for target in (item.get("target_hashes") or [])}
    if meta["replicates_hash"] not in live_targets:
        return {"offered": False, "suggestions_generated_at": suggestions.get("generated_at"), "reason": "target left evidence work items"}
    target = client.measurement(meta["replicates_hash"])
    target_manifest = target.get("measurement", target).get("manifest") or {}
    if target_manifest.get("models") != manifest["models"]:
        raise RuntimeError("target tokenizer roster changed or was not preserved")
    if (target_manifest.get("environment") or {}).get("version") != "0.14.0":
        raise RuntimeError("target no longer declares tiktoken 0.14.0")
    if manifest_commitment(manifest) != meta["manifest_sha256"]:
        raise RuntimeError("published manifest commitment mismatch")
    prior = set()
    for row in proposal.get("measurements") or []:
        prior_manifest = row.get("manifest")
        if not isinstance(prior_manifest, dict) and row.get("manifest_hash"):
            detail = client.measurement(row["manifest_hash"])
            prior_manifest = detail.get("measurement", detail).get("manifest")
        if isinstance(prior_manifest, dict):
            prior.update(pairs(prior_manifest))
    overlap = pairs(manifest) & prior
    if overlap:
        raise RuntimeError(f"fresh-input gate found {len(overlap)} complete pair overlaps")
    if git("status", "--porcelain"):
        raise RuntimeError("evidence repository must be clean before mint")
    git("merge-base", "--is-ancestor", "HEAD", "origin/main")
    return {
        "offered": True, "suggestions_generated_at": suggestions.get("generated_at"),
        "proposal_stage": proposal.get("stage"), "fresh_complete_pair_overlap": 0,
        "target_value": target.get("measurement", target).get("value"),
        "target_tiktoken_version": "0.14.0", "pair_count": len(manifest["test_set"]),
    }


def main() -> None:
    if importlib.metadata.version("ainglish") != "0.2.52" or importlib.metadata.version("tiktoken") != "0.14.0":
        raise SystemExit("REFUSING: this wave requires ainglish 0.2.52 and tiktoken 0.14.0")
    if list(ROOT.glob("*.receipt.json")) or (ROOT / "results.json").exists():
        raise SystemExit("REFUSING: this one-shot directory already contains outcomes")
    index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    client = ainglish_client()
    outcomes = []
    for name, meta in index["campaigns"].items():
        manifest = json.loads((ROOT / meta["file"]).read_text(encoding="utf-8"))
        checked = preflight(client, meta, manifest)
        if not checked["offered"]:
            outcome = {"campaign": name, "state": "not_currently_offered", "replicates_hash": meta["replicates_hash"], "preflight": checked}
            outcomes.append(outcome); print("SKIP", json.dumps(outcome, sort_keys=True), flush=True)
            continue
        opened = client.mint_attempt(
            meta["slug"], manifest=manifest,
            estimand=(
                f"Legacy token_delta replication of {meta['replicates_hash']} over ten wholly fresh complete pairs for "
                f"{meta['construct']}; tiktoken 0.14.0; equal pair mean for cl100k_base, o200k_base and p50k_base; "
                "headline is the maximum tokenizer mean. No post-hoc comparison identity or estimand contract is invented."
            ),
            admissibility_gates=[
                "fresh authenticated personalised suggestions still offer the exact replication target immediately before mint",
                "the exact target remains in the fresh proposal evidence work items",
                "all ten complete pairs have zero exact overlap with every prior filed manifest on the proposal",
                "target roster, ten-pair sample size, aggregate filing shape and tiktoken 0.14.0 environment are preserved",
                "all three encodings load; every finite agreement or disagreement is filed exactly once",
            ],
            planned_sample={"items": 10, "tokenizers": 3, "models": manifest["models"], "tiktoken_version": "0.14.0"},
        )["attempt"]
        try:
            counted = token_delta([(row["english"], row["ainglish"]) for row in manifest["test_set"]], manifest["models"])
            if "skipped" in counted:
                raise RuntimeError(counted["skipped"])
            members = [{"model": model, "value": counted["by_tokenizer"][model]["mean"]} for model in manifest["models"]]
            values = [row["value"] for row in members]
            payload = {
                "attempt_id": opened["attempt_id"], "metric": "token_delta",
                "value": max(values), "value_lo": min(values), "value_hi": max(values),
                "panel_models": manifest["models"], "per_member": members,
                "manifest": manifest, "replicates_hash": meta["replicates_hash"],
            }
            filed = client.measure(meta["slug"], payload)
        except Exception as exc:
            closure = abort(client, opened["attempt_id"], exc)
            outcome = {"campaign": name, "state": "aborted", "replicates_hash": meta["replicates_hash"], "error": f"{type(exc).__name__}: {exc}", "closure": closure}
            outcomes.append(outcome); print("ABORT", json.dumps(outcome, sort_keys=True), flush=True)
            continue
        outcome = {
            "kind": "dexagon.ainglish.legacy-token-settlement-receipt.v1",
            "captured_at": datetime.now(timezone.utc).isoformat(), "campaign": name,
            "state": "filed", "replicates_hash": meta["replicates_hash"], "preflight": checked,
            "attempt": opened, "result": {"value": max(values), "value_lo": min(values), "value_hi": max(values), "per_member": members, "manifest_hash": manifest_commitment(manifest)},
            "server_measurement": filed,
        }
        path = ROOT / f"{name}.receipt.json"
        path.write_text(json.dumps(outcome, indent=2) + "\n", encoding="utf-8")
        outcome["receipt_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        outcomes.append(outcome); print("FILED", json.dumps(outcome["result"], sort_keys=True), flush=True)
    result = {"kind": "dexagon.ainglish.legacy-token-settlement-results.v1", "outcomes": outcomes}
    (ROOT / "results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

