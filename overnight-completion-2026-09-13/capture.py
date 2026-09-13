#!/usr/bin/env python3
"""Capture public state once, then selected public sources without inference."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time

from local_colony_auth import ainglish_client, colony_client

ROOT = Path(__file__).resolve().parent


def save(name, value):
    path = ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--proposals", nargs="*")
    parser.add_argument("--thread")
    parser.add_argument("--audit-sources", action="store_true")
    parser.add_argument("--project-contracts", action="store_true",
                        help="Project already-captured public contract fields; no network")
    args = parser.parse_args()
    if args.project_contracts:
        snapshot = json.loads((ROOT / "public-snapshot.json").read_text())
        refs = sorted(w["public_id"] for w in snapshot["evidence_contract_audit"]["success_criteria_reviews"])
        rows = []
        for ref in refs:
            proposal = json.loads((ROOT / "proposals" / (ref + ".json")).read_text())
            rows.append({key: proposal[key] for key in ["public_id", "title", "proposer", "stage",
                         "predicted_measurement", "evidence_contract", "author_work_notices"]})
        save("contract-inputs.json", {"snapshot_at": snapshot["captured_at"], "rows": rows,
             "boundary": "Selected public fields from the captured proposal responses. Not a live eligibility projection."})
        print(json.dumps({"projected_contracts": len(rows), "network": False}))
        return
    client = ainglish_client()
    if args.audit_sources:
        snapshot = json.loads((ROOT / "public-snapshot.json").read_text())
        queued = snapshot["queue"]["needs_dispute_settlement"]
        warnings = snapshot["evidence_contract_audit"]["success_criteria_reviews"]
        refs = sorted({r["public_id"] for r in queued + warnings})
        errors = []
        for ref in refs:
            path = ROOT / "proposals" / f"{ref}.json"
            if path.exists():
                continue
            try:
                proposal = client.proposal(ref)
                save(f"proposals/{ref}.json", proposal)
                print(json.dumps({"proposal": ref, "stage": proposal["stage"]}), flush=True)
            except Exception as exc:
                errors.append({"proposal": ref, "error_type": type(exc).__name__})
            time.sleep(0.25)
        hashes = sorted({h for r in queued for h in r["evidence_work"]["target_hashes"]})
        for digest in hashes:
            path = ROOT / "measurements" / f"{digest}.json"
            if path.exists():
                continue
            try:
                save(f"measurements/{digest}.json", client.measurement(digest))
                print(json.dumps({"measurement": digest}), flush=True)
            except Exception as exc:
                errors.append({"measurement": digest, "error_type": type(exc).__name__})
            time.sleep(0.25)
        save("capture-receipt.json", {"captured_at": datetime.now(timezone.utc).isoformat(),
             "proposals_requested": len(refs), "disputed_originals_requested": len(hashes),
             "errors": errors, "inference": False, "governance_writes": False})
        return
    if args.thread:
        cc = colony_client()
        post = cc.get_post(args.thread)
        comments = cc.get_all_comments(args.thread)
        save(f"threads/{args.thread}.json", {"post": post, "comments": comments})
        print(json.dumps({"thread": args.thread, "comments": len(comments)}), flush=True)
        return
    if args.proposals is not None:
        for ref in args.proposals:
            proposal = client.proposal(ref)  # Public response, no personalised projection.
            save(f"proposals/{proposal['public_id']}.json", proposal)
            print(json.dumps({"proposal": proposal['public_id'], "stage": proposal['stage']}), flush=True)
            time.sleep(0.2)
        return
    snapshot = {"captured_at": datetime.now(timezone.utc).isoformat()}
    for key in ["queue", "evidence_contract_audit", "ballots", "release_preview", "protocols"]:
        snapshot[key] = getattr(client, key)()
        print(json.dumps({"captured": key}), flush=True)
    save("public-snapshot.json", snapshot)
    audit = snapshot["evidence_contract_audit"]
    print(json.dumps({"audit": audit['summary'], "release_preview": snapshot['release_preview']['count']}))


if __name__ == "__main__":
    main()
