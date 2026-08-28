#!/usr/bin/env python3
"""Run one published manifest-bound panel through Dexagon's local auth helper.

This is deliberately narrower than ``panel.py run``.  A real run must use a
tracked runspec at the public evidence HEAD, perform authenticated suggestions
and proposal reads immediately before minting, and either complete or abort the
minted attempt through the SDK harness.  It never reads or prints credentials.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from ainglish import panel as panel_harness


HERE = Path(__file__).resolve().parent
EVIDENCE_REPO = HERE.parent
PROJECT = EVIDENCE_REPO.parent
sys.path.insert(0, str(PROJECT / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=EVIDENCE_REPO, check=True, capture_output=True, text=True
    ).stdout.strip()


def published_runspec(path: Path) -> tuple[dict, str]:
    resolved = path.resolve()
    try:
        relative = str(resolved.relative_to(EVIDENCE_REPO))
    except ValueError as exc:
        raise SystemExit("REFUSING: runspec is outside the evidence repository") from exc
    spec = json.loads(resolved.read_text(encoding="utf-8"))
    if spec.get("kind") != "ainglish.panel.runspec.v1":
        raise SystemExit("REFUSING: expected an ainglish.panel.runspec.v1 document")
    if not isinstance(spec.get("attempt"), dict):
        raise SystemExit("REFUSING: a real manifest-bound run needs runspec.attempt")
    panel_harness._attempt_settings(spec["attempt"])
    git("ls-files", "--error-unmatch", relative)
    head = git("rev-parse", "HEAD")
    if head != git("rev-parse", "origin/main"):
        raise SystemExit("REFUSING: evidence HEAD is not the published origin/main")
    public_bytes = subprocess.run(
        ["git", "show", f"{head}:{relative}"], cwd=EVIDENCE_REPO,
        check=True, capture_output=True,
    ).stdout
    if public_bytes != resolved.read_bytes():
        raise SystemExit("REFUSING: runspec bytes differ from the published HEAD")
    return spec, head


def validate_live_work(spec: dict, proposal: dict, target: dict | None) -> dict:
    slug = spec.get("slug")
    metric = spec.get("metric")
    if proposal.get("slug") != slug or proposal.get("superseded_by"):
        raise SystemExit("REFUSING: runspec does not name the current proposal surface")
    if proposal.get("stage") not in {"seconded", "measured"}:
        raise SystemExit(
            f"REFUSING: proposal stage {proposal.get('stage')!r} no longer accepts this evidence"
        )
    work_items = (proposal.get("evidence_readiness") or {}).get("work_items") or []
    matching = [row for row in work_items if row.get("metric") == metric]
    target_hash = spec.get("replicates_hash")
    if target_hash:
        if target is None:
            raise SystemExit("REFUSING: replication target was not read")
        if target.get("manifest_hash") != target_hash or target.get("metric") != metric:
            raise SystemExit("REFUSING: replication target identity or metric drift")
        if target.get("settlement_state") != "awaiting":
            raise SystemExit(
                f"REFUSING: replication target is {target.get('settlement_state')!r}, not awaiting"
            )
        eligible = any(
            row.get("state") == "replicate_original"
            and target_hash in (row.get("target_hashes") or [])
            for row in matching
        )
        if not eligible:
            raise SystemExit("REFUSING: the fresh evidence queue no longer requests this replication")
        action = "replicate_original"
    else:
        if not any(row.get("state") == "submit_original" for row in matching):
            raise SystemExit("REFUSING: the fresh evidence queue no longer requests this original")
        action = "submit_original"
    return {
        "proposal": slug,
        "stage": proposal.get("stage"),
        "metric": metric,
        "action": action,
        "replicates_hash": target_hash,
    }


def receipt_stem(path: Path) -> str:
    return path.name


def ensure_unspent(path: Path) -> None:
    stem = receipt_stem(path)
    existing = sorted(path.parent.glob(f"{stem}.attempt-*"))
    if existing:
        raise SystemExit(
            "REFUSING: this runspec already has an attempt receipt; inspect it rather than rerun"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("runspec", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="verify published bytes only; no network")
    mode.add_argument("--dry-run", action="store_true", help="fetch and validate with synthetic answers")
    mode.add_argument("--submit", action="store_true", help="mint, run readers once, and file or abort")
    args = parser.parse_args()

    if git("status", "--porcelain"):
        raise SystemExit("REFUSING: evidence repository is not clean")
    spec, head = published_runspec(args.runspec)
    ensure_unspent(args.runspec.resolve())
    if args.check:
        print(json.dumps({"status": "published-runspec-verified", "commit": head}, indent=2))
        return

    items, digest = panel_harness.fetch_items(spec["items_url"], spec.get("items_sha256"))
    manifest = dict(spec, items=items, items_sha256=digest)
    if args.dry_run:
        manifest["_dry_run"] = True
        result = panel_harness.run_panel(
            manifest, ask_fn=panel_harness.dry_reader(items, manifest)
        )
        if result is None or panel_harness._is_panel_refusal(result):
            raise SystemExit(1)
        print(json.dumps({
            "status": "dry-run-verified",
            "commit": head,
            "manifest_sha256": hashlib.sha256(canonical(result["manifest"])).hexdigest(),
            "reader_calls": 0,
            "governance_writes": 0,
        }, indent=2))
        return

    client = ainglish_client()
    suggestions = client.suggestions()
    proposal = client.proposal(spec["slug"], authenticated=True)
    target = client.measurement(spec["replicates_hash"]) if spec.get("replicates_hash") else None
    preflight = validate_live_work(spec, proposal, target)
    preflight["suggestions_generated_at"] = suggestions.get("generated_at")
    preflight["published_commit"] = head
    print(json.dumps({"fresh_live_preflight": preflight}, indent=2))
    result = panel_harness._run_preregistered_panel(
        manifest,
        spec,
        panel_harness.ask,
        client,
        receipt_dir=str(args.runspec.resolve().parent),
        receipt_stem=receipt_stem(args.runspec.resolve()),
    )
    raise SystemExit(0 if result is not None else 1)


if __name__ == "__main__":
    main()
