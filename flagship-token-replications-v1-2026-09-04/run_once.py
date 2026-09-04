#!/usr/bin/env python3
"""Mint, count, and file each still-routed token replication once."""

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
EVIDENCE = ROOT.parent
PROJECT = EVIDENCE.parent
sys.path.insert(0, str(PROJECT / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=EVIDENCE, check=True, text=True, capture_output=True).stdout.strip()


def complete_pairs(manifest: dict) -> set[tuple[str, str]]:
    return {(row["english"], row["ainglish"]) for row in manifest["test_set"]}


def target_payload(client, target: str) -> dict:
    detail = client.measurement(target)
    return detail.get("measurement", detail)


def preflight(client, meta: dict, manifest: dict) -> dict:
    suggestions = client.suggestions()
    offered = {row.get("replicates_hash") for row in suggestions.get("suggestions", []) if row.get("tier") == "replications"}
    if meta["replicates_hash"] not in offered:
        return {"offered": False, "suggestions_generated_at": suggestions.get("generated_at")}
    proposal = client.proposal(meta["slug"], authenticated=True)
    live_targets = {
        target
        for item in (proposal.get("evidence_readiness") or {}).get("work_items", [])
        for target in (item.get("target_hashes") or [])
    }
    if meta["replicates_hash"] not in live_targets:
        return {"offered": False, "reason": "target left the live evidence work items"}
    target = target_payload(client, meta["replicates_hash"])
    target_manifest = target.get("manifest") or {}
    if target_manifest.get("models") != manifest["models"]:
        raise RuntimeError("target tokenizer roster was not preserved")
    source_version = (
        (target_manifest.get("environment") or {}).get("version")
        or (target_manifest.get("tokenizer_provenance") or {}).get("library_version")
    )
    if source_version != "0.14.0":
        raise RuntimeError("target tiktoken version was not preserved")
    if manifest_commitment(manifest) != meta["manifest_sha256"]:
        raise RuntimeError("published manifest commitment mismatch")
    prior = set()
    for row in proposal.get("measurements") or []:
        prior_manifest = row.get("manifest")
        if not isinstance(prior_manifest, dict) and row.get("manifest_hash"):
            prior_manifest = target_payload(client, row["manifest_hash"]).get("manifest")
        if isinstance(prior_manifest, dict) and isinstance(prior_manifest.get("test_set"), list):
            prior.update(complete_pairs(prior_manifest))
    overlap = complete_pairs(manifest) & prior
    if overlap:
        raise RuntimeError(f"fresh-input gate found {len(overlap)} complete pair overlaps")
    if git("status", "--porcelain"):
        raise RuntimeError("evidence repository must be clean before mint")
    git("merge-base", "--is-ancestor", "HEAD", "origin/main")
    return {
        "offered": True,
        "suggestions_generated_at": suggestions.get("generated_at"),
        "proposal_stage": proposal.get("stage"),
        "fresh_complete_pair_overlap": 0,
        "target_value": target.get("value"),
        "pair_count": len(manifest["test_set"]),
    }


def abort(client, attempt_id: str, exc: Exception) -> dict:
    current = client.attempt(attempt_id)
    if current.get("state") != "open":
        return {"state": current.get("state"), "abort_sent": False}
    detail = f"{type(exc).__name__}: {exc}"
    return client.abort_attempt(
        attempt_id,
        detail[:160],
        {"kind": "dexagon.ainglish.flagship-token-run-abort.v1", "failed_gate": detail},
        failed_gate_kind="harness_error",
    )


def main() -> None:
    if importlib.metadata.version("ainglish") != "0.2.52" or importlib.metadata.version("tiktoken") != "0.14.0":
        raise SystemExit("REFUSING: requires ainglish 0.2.52 and tiktoken 0.14.0")
    if (ROOT / "results.json").exists():
        raise SystemExit("REFUSING: this packet already has a complete result ledger")
    if git("status", "--porcelain"):
        raise SystemExit("REFUSING: evidence repository must be clean")
    git("merge-base", "--is-ancestor", "HEAD", "origin/main")
    index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    client = ainglish_client()
    outcomes = []
    for name, meta in index["campaigns"].items():
        receipt = ROOT / f"{name}.receipt.json"
        if receipt.exists():
            outcome = json.loads(receipt.read_text(encoding="utf-8"))
            if outcome.get("campaign") != name or outcome.get("state") != "filed":
                raise SystemExit(f"REFUSING: invalid existing receipt for {name}")
            outcome["receipt_sha256"] = hashlib.sha256(receipt.read_bytes()).hexdigest()
            outcomes.append(outcome)
            print("PRESERVED", name, json.dumps(outcome["result"], sort_keys=True), flush=True)
            continue
        manifest = json.loads((ROOT / meta["file"]).read_text(encoding="utf-8"))
        checked = preflight(client, meta, manifest)
        if not checked["offered"]:
            outcomes.append({"campaign": name, "state": "not_currently_offered", "preflight": checked})
            continue
        count = len(manifest["test_set"])
        opened = client.mint_attempt(
            meta["slug"],
            manifest=manifest,
            estimand=(
                f"Fresh-input token_delta replication of {meta['replicates_hash']} over {count} complete pairs for "
                f"{meta['construct']}; tiktoken 0.14.0; equal item mean per tokenizer; maximum tokenizer mean headline"
            ),
            admissibility_gates=[
                "fresh authenticated personalised suggestions offer the exact target immediately before mint",
                "the exact target remains in live evidence work items",
                "zero exact complete-pair overlap with every filed proposal manifest",
                "target sample size, tokenizer roster, environment and aggregate-only result shape are preserved",
                "every finite agreement or disagreement is filed exactly once",
            ],
            planned_sample={"items": count, "tokenizers": 3, "models": manifest["models"], "tiktoken_version": "0.14.0"},
        )["attempt"]
        try:
            counted = token_delta([(row["english"], row["ainglish"]) for row in manifest["test_set"]], manifest["models"])
            if "skipped" in counted:
                raise RuntimeError(counted["skipped"])
            members = [{"model": model, "value": counted["by_tokenizer"][model]["mean"]} for model in manifest["models"]]
            values = [row["value"] for row in members]
            filed = client.measure(meta["slug"], {
                "attempt_id": opened["attempt_id"],
                "metric": "token_delta",
                "value": max(values),
                "value_lo": min(values),
                "value_hi": max(values),
                "panel_models": manifest["models"],
                "per_member": members,
                "manifest": manifest,
                "replicates_hash": meta["replicates_hash"],
            })
        except Exception as exc:
            outcome = {"campaign": name, "state": "aborted", "error": f"{type(exc).__name__}: {exc}", "closure": abort(client, opened["attempt_id"], exc)}
            outcomes.append(outcome)
            continue
        outcome = {
            "kind": "dexagon.ainglish.flagship-token-replication-receipt.v1",
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "campaign": name,
            "state": "filed",
            "replicates_hash": meta["replicates_hash"],
            "preflight": checked,
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
        receipt.write_text(json.dumps(outcome, indent=2) + "\n", encoding="utf-8")
        outcome["receipt_sha256"] = hashlib.sha256(receipt.read_bytes()).hexdigest()
        outcomes.append(outcome)
    result = {"kind": "dexagon.ainglish.flagship-token-replication-results.v1", "outcomes": outcomes}
    (ROOT / "results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"outcomes": [{"campaign": row["campaign"], "state": row["state"], "result": row.get("result")} for row in outcomes]}, indent=2))


if __name__ == "__main__":
    main()
