#!/usr/bin/env python3
"""Execute the still-unspent frozen carriers when the live router offers them."""

from __future__ import annotations

from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import subprocess

from ainglish.client import manifest_commitment
from ainglish.measure import token_delta

from run_all_once import ROOT, EVIDENCE, ainglish_client, abort, preflight


OUTCOME = ROOT / "live-rotation-results.json"
CAMPAIGNS = ("because-ever-since", "replacement-roles")


def main() -> None:
    if importlib.metadata.version("ainglish") != "0.2.52" or importlib.metadata.version("tiktoken") != "0.14.0":
        raise SystemExit("REFUSING: requires ainglish 0.2.52 and tiktoken 0.14.0")
    if OUTCOME.exists():
        raise SystemExit("REFUSING: this live-rotation run already has a complete outcome ledger")
    if subprocess.run(["git", "status", "--porcelain"], cwd=EVIDENCE, check=True, capture_output=True, text=True).stdout.strip():
        raise SystemExit("REFUSING: evidence repository must be clean")
    subprocess.run(["git", "merge-base", "--is-ancestor", "HEAD", "origin/main"], cwd=EVIDENCE, check=True)

    index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    client = ainglish_client()
    outcomes = []
    for name in CAMPAIGNS:
        receipt = ROOT / f"live-rotation-{name}.receipt.json"
        if receipt.exists():
            outcome = json.loads(receipt.read_text(encoding="utf-8"))
            if outcome.get("campaign") != name or outcome.get("state") != "filed":
                raise SystemExit(f"REFUSING: invalid existing receipt for {name}")
            outcomes.append(outcome)
            print("PRESERVED", name, json.dumps(outcome["result"], sort_keys=True), flush=True)
            continue
        meta = index["campaigns"][name]
        manifest = json.loads((ROOT / meta["file"]).read_text(encoding="utf-8"))
        checked = preflight(client, meta, manifest)
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

        opened = client.mint_attempt(
            meta["slug"],
            manifest=manifest,
            estimand=(
                f"Legacy token_delta replication of {meta['replicates_hash']} over ten wholly fresh complete pairs for "
                f"{meta['construct']}; tiktoken 0.14.0; equal pair mean for cl100k_base, o200k_base and p50k_base; "
                "headline is the maximum tokenizer mean. No post-hoc comparison identity or estimand contract is invented."
            ),
            admissibility_gates=[
                "fresh authenticated personalized suggestions offer the exact target immediately before mint",
                "the exact target remains in the fresh proposal evidence work items",
                "all ten complete pairs have zero exact overlap with every prior filed proposal manifest",
                "target roster, sample size, aggregate filing shape, and tiktoken version are preserved",
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
            "kind": "dexagon.ainglish.legacy-token-live-rotation-receipt.v1",
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
        outcomes.append(outcome)
        print("FILED", name, json.dumps(outcome["result"], sort_keys=True), flush=True)

    output = {"kind": "dexagon.ainglish.legacy-token-live-rotation-results.v1", "outcomes": outcomes}
    OUTCOME.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"outcomes": [{"campaign": row["campaign"], "state": row["state"], "result": row.get("result")} for row in outcomes]}, indent=2))


if __name__ == "__main__":
    main()
