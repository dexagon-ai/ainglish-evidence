#!/usr/bin/env python3
"""File the already-completed fidelity result without repeating any model call."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

from ainglish.client import manifest_commitment


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
PROJECT = REPO.parent
SLUG = "evidential-tags-obs-inf-rep-src-with-instrument-recall-and-p-2"
sys.path.insert(0, str(PROJECT / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO, check=True, capture_output=True, text=True
    ).stdout.strip()


def main() -> None:
    receipt_path = ROOT / "fidelity-measurement.json"
    if receipt_path.exists():
        raise SystemExit("REFUSING: the completed outcome already has a filing receipt")
    dirt = [
        line for line in git("status", "--porcelain").splitlines()
        if not line.endswith("evidential-tags-fidelity-and-carrier-2026-08-25/fidelity-partial.json")
    ]
    if dirt:
        raise SystemExit("REFUSING: publish the immutable result and this recovery before filing")
    if git("rev-parse", "HEAD") != git("rev-parse", "origin/main"):
        raise SystemExit("REFUSING: filing recovery is not public at origin/main")

    attempt_record = json.loads((ROOT / "fidelity-attempt.json").read_text(encoding="utf-8"))
    result = json.loads((ROOT / "fidelity-result.json").read_text(encoding="utf-8"))
    attempt_id = attempt_record["attempt"]["attempt_id"]
    manifest = result["manifest"]
    if result["attempt_id"] != attempt_id:
        raise SystemExit("REFUSING: result and attempt ids differ")
    if manifest_commitment(manifest) != attempt_record["manifest_commitment"]:
        raise SystemExit("REFUSING: completed result manifest differs from the minted commitment")

    qualifications = manifest.get("reader_qualifications") or []
    roster_by_name = {
        row["roster_id"].split("@", 1)[0]: row["roster_id"]
        for row in qualifications
    }
    per_member = []
    for row in result["per_member"]:
        roster_id = roster_by_name.get(row["model"])
        if roster_id is None:
            raise SystemExit(f"REFUSING: no frozen roster id for completed reader {row['model']!r}")
        per_member.append({**row, "model": roster_id})

    client = ainglish_client()
    attempt = client.attempt(attempt_id)
    if attempt.get("state") != "open":
        raise SystemExit(f"REFUSING: attempt is {attempt.get('state')!r}, not open")
    proposal = client.proposal(SLUG, authenticated=True)
    if any(row.get("attempt_id") == attempt_id for row in proposal.get("measurements") or []):
        raise SystemExit("REFUSING: server already has a measurement for this attempt")

    payload = {
        "metric": "tag_fidelity",
        "formula_version": 2,
        "value": result["value"],
        "value_lo": min(row["value"] for row in per_member),
        "value_hi": max(row["value"] for row in per_member),
        "panel_models": list(manifest["models"]),
        "per_member": per_member,
        "manifest": manifest,
        "attempt_id": attempt_id,
    }
    filed = client.measure(SLUG, payload)
    receipt_path.write_text(json.dumps({
        "kind": "dexagon.ainglish.completed-fidelity-filing-receipt.v1",
        "filed_at": datetime.now(timezone.utc).isoformat(),
        "reason": (
            "The original one-shot executor completed all frozen cells, then the write validator "
            "rejected display names that omitted the already-declared precision suffix. No model "
            "call, score, manifest field, or attempt was repeated."
        ),
        "request": payload,
        "receipt": filed,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (ROOT / "fidelity-partial.json").unlink(missing_ok=True)
    measurement = filed.get("measurement") or filed
    print(json.dumps({
        "attempt_id": attempt_id,
        "manifest_hash": measurement.get("manifest_hash"),
        "value": measurement.get("value"),
        "state": (measurement.get("attempt") or {}).get("state"),
    }, indent=2))


if __name__ == "__main__":
    main()
