#!/usr/bin/env python3
"""File the fresh no-charge/available-now token replication once."""

from __future__ import annotations

from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys

from ainglish.client import manifest_commitment
from ainglish.measure import token_delta


ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT.parent
PROJECT = ROOT.parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402

SLUG = "offer-is-no-charge-billing-scope-resource-is-available-now"
TARGET = "c1c90c9d34d06d4852f0ece50413b674fb4c8be70422c7f5d5ffa4bb29e96848"


def pairs(manifest: dict) -> set[tuple[str, str]]:
    return {
        (row["english"], row["ainglish"])
        for row in manifest.get("test_set") or []
        if isinstance(row, dict) and isinstance(row.get("english"), str) and isinstance(row.get("ainglish"), str)
    }


def main() -> None:
    if importlib.metadata.version("ainglish") != "0.2.52" or importlib.metadata.version("tiktoken") != "0.14.0":
        raise SystemExit("REFUSING: requires ainglish 0.2.52 and tiktoken 0.14.0")
    if (ROOT / "result.json").exists() or list(ROOT.glob("*.receipt.json")):
        raise SystemExit("REFUSING: this one-shot directory already has an outcome")
    if subprocess.run(["git", "status", "--porcelain"], cwd=EVIDENCE, check=True, capture_output=True, text=True).stdout.strip():
        raise SystemExit("REFUSING: evidence repository is not clean")
    subprocess.run(["git", "merge-base", "--is-ancestor", "HEAD", "origin/main"], cwd=EVIDENCE, check=True)

    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    client = ainglish_client()
    suggestions = client.suggestions()
    offered = {
        row.get("replicates_hash") for row in suggestions.get("suggestions", [])
        if row.get("tier") == "replications"
    }
    proposal = client.proposal(SLUG, authenticated=True)
    targets = {
        target for item in (proposal.get("evidence_readiness") or {}).get("work_items", [])
        for target in item.get("target_hashes", [])
    }
    if TARGET not in offered or TARGET not in targets:
        raise SystemExit("REFUSING: fresh live state does not offer the exact target")
    target = client.measurement(TARGET)
    if target.get("metric") != "token_delta" or target.get("manifest", {}).get("models") != manifest["models"]:
        raise SystemExit("REFUSING: target metric or tokenizer roster changed")
    if (target.get("manifest", {}).get("environment") or {}).get("version") != "0.14.0":
        raise SystemExit("REFUSING: target tiktoken version changed")

    prior = set()
    for row in proposal.get("measurements") or []:
        prior_manifest = row.get("manifest")
        if not isinstance(prior_manifest, dict) and row.get("manifest_hash"):
            prior_manifest = client.measurement(row["manifest_hash"]).get("manifest")
        if isinstance(prior_manifest, dict):
            prior.update(pairs(prior_manifest))
    overlap = pairs(manifest) & prior
    if overlap:
        raise SystemExit(f"REFUSING: {len(overlap)} complete pairs overlap prior filed manifests")

    opened = client.mint_attempt(
        SLUG,
        manifest=manifest,
        estimand=(
            f"Legacy token_delta replication of {TARGET} over ten wholly fresh complete pairs for no-charge/available-now; "
            "tiktoken 0.14.0; equal pair mean for cl100k_base, o200k_base and p50k_base; headline is the maximum tokenizer mean."
        ),
        admissibility_gates=[
            "fresh authenticated personalized suggestions offer the exact target immediately before mint",
            "the exact target remains in the fresh proposal evidence work items",
            "all ten complete pairs have zero exact overlap with every prior filed proposal manifest",
            "target tokenizer roster, sample size, filing shape, and tiktoken version are preserved",
            "all finite agreement or disagreement is filed exactly once",
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
            "attempt_id": opened["attempt_id"],
            "metric": "token_delta",
            "value": max(values),
            "value_lo": min(values),
            "value_hi": max(values),
            "panel_models": manifest["models"],
            "per_member": members,
            "manifest": manifest,
            "replicates_hash": TARGET,
        }
        filed = client.measure(SLUG, payload)
    except Exception as exc:
        current = client.attempt(opened["attempt_id"])
        if current.get("state") == "open":
            client.abort_attempt(
                opened["attempt_id"], f"{type(exc).__name__}: {exc}"[:160],
                {"kind": "dexagon.ainglish.no-charge-token-abort.v1", "failed_gate": f"{type(exc).__name__}: {exc}"},
                failed_gate_kind="harness_error",
            )
        raise

    result = {
        "kind": "dexagon.ainglish.no-charge-token-settlement-result.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "state": "filed",
        "suggestions_generated_at": suggestions.get("generated_at"),
        "replicates_hash": TARGET,
        "manifest_hash": manifest_commitment(manifest),
        "fresh_complete_pair_overlap": 0,
        "value": max(values),
        "value_lo": min(values),
        "value_hi": max(values),
        "per_member": members,
        "attempt": opened,
        "server_measurement": filed,
    }
    (ROOT / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("state", "replicates_hash", "manifest_hash", "value", "value_lo", "value_hi", "per_member")}, indent=2))


if __name__ == "__main__":
    main()
