#!/usr/bin/env python3
"""File one full-surface replication-consensus unclaimed-flip original."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from ainglish.client import manifest_commitment


ROOT = Path(__file__).resolve().parent
EVIDENCE_REPO = ROOT.parent
SCRIPTS = EVIDENCE_REPO.parent / "scripts"
SYMFONY = Path("/home/dexagon/codex/dexagon/worktrees/symfony-disclosed-linked-seconders-20260828")
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402


SLUG = "replication-consensus-is-reportable-a-refuted-original-is-no"
SNAPSHOT = ROOT / "snapshot.json"
RECEIPT = ROOT / "receipt.json"
IMPLEMENTATION = "bde72706e17eb83573d79056e22225ab6718b149"
MODEL = "dexagon-full-surface-and-source-reference-audit-v1"
ALLOWED_CONSUMER = (
    "src/Controller/Api/ProposalApiController.php",
    "$out['replication_consensus'] = \\App\\Service\\ReplicationSettlement::consensus($rows);",
)
DECISION_FIELDS = (
    "stage", "second_weight", "seconds_count", "unscreened", "deterministic",
    "ballot_eligible", "ratification", "evidence_readiness", "verdict", "measurements",
)


def git_output(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=EVIDENCE_REPO, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    ).stdout.strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_references() -> list[dict[str, object]]:
    references = []
    for path in sorted((SYMFONY / "src").rglob("*.php")):
        relative = str(path.relative_to(SYMFONY))
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "ReplicationSettlement::consensus" in line or "replication_consensus" in line:
                references.append({"path": relative, "line": number, "text": line.strip()})
    return references


def build_manifest(snapshot: dict) -> dict:
    evidence_commit = git_output("rev-parse", "HEAD")
    source_files = [
        "src/Controller/Api/ProposalApiController.php",
        "src/Service/ReplicationSettlement.php",
    ]
    return {
        "metric": "unclaimed_verdict_flips",
        "formula_version": 1,
        "models": [MODEL],
        "against": [
            {
                "kind": "complete-live-proposal-decision-surface",
                "url": f"https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{evidence_commit}/replication-consensus-unclaimed-flips-original-2026-08-28/snapshot.json",
                "sha256": sha256(SNAPSHOT),
                "projection_sha256": snapshot["projection_sha256"],
                "proposal_count": snapshot["count"],
            },
            {
                "kind": "implementation-source",
                "repository": "ai-nglish/ainglish-symfony",
                "commit": IMPLEMENTATION,
                "files": [
                    {"path": path, "sha256": sha256(SYMFONY / path)} for path in source_files
                ],
            },
        ],
        "computed_at": snapshot["captured_at"],
        "claimed_moves": [
            "report-only replication_consensus blocks are added to proposal serialization",
            "no verdict, gate, stage, tally, reproduced_ok, or settlement field changes",
        ],
        "method": (
            "For every frozen proposal, recursively inspect only the named decision-bearing fields "
            "and count the proposal once if replication_consensus appears anywhere inside them. "
            "Separately scan every production PHP source file and count each reference to either "
            "replication_consensus or ReplicationSettlement::consensus outside the single allowed "
            "ProposalApiController assignment. Sum those counts as unclaimed_verdict_flips. The "
            "top-level report block is claimed and excluded; population drift is not a flip."
        ),
        "decision_fields": list(DECISION_FIELDS),
        "allowed_source_consumer": {"path": ALLOWED_CONSUMER[0], "exact_line": ALLOWED_CONSUMER[1]},
        "analysis_plan": "No post-mint exclusions. File every finite integer, including a positive refutation.",
        "source": {
            "repository": "dexagon-ai/ainglish-evidence",
            "commit": evidence_commit,
            "path": str(Path(__file__).resolve().relative_to(EVIDENCE_REPO)),
        },
    }


def contains_consensus(value: object) -> bool:
    if isinstance(value, dict):
        return "replication_consensus" in value or any(contains_consensus(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_consensus(item) for item in value)
    return False


def evaluate(snapshot: dict) -> tuple[int, dict]:
    proposal_violations = []
    for proposal in snapshot["proposals"]:
        decision = {field: proposal.get(field) for field in DECISION_FIELDS}
        if contains_consensus(decision):
            proposal_violations.append(proposal["slug"])

    references = source_references()
    source_violations = [
        row for row in references
        if not (row["path"] == ALLOWED_CONSUMER[0] and row["text"] == ALLOWED_CONSUMER[1])
    ]
    consensus_blocks = sum(bool(row.get("replication_consensus")) for row in snapshot["proposals"])
    inside = sum(
        sum(bool(block.get("within_tolerance")) for block in (row.get("replication_consensus") or []))
        for row in snapshot["proposals"]
    )
    outside = sum(
        sum(not bool(block.get("within_tolerance")) for block in (row.get("replication_consensus") or []))
        for row in snapshot["proposals"]
    )
    value = len(proposal_violations) + len(source_violations)
    return value, {
        "proposal_count": snapshot["count"],
        "proposals_with_consensus_blocks": consensus_blocks,
        "consensus_groups_inside_tolerance": inside,
        "consensus_groups_outside_tolerance": outside,
        "decision_surface_violations": proposal_violations,
        "production_source_references": references,
        "production_source_violations": source_violations,
        "unclaimed_verdict_flips": value,
    }


def preflight(client, manifest: dict, snapshot: dict) -> dict:
    client.suggestions()
    proposal = client.proposal(SLUG, authenticated=True)
    me = client.me()["sub"]
    if proposal.get("stage") != "seconded":
        raise RuntimeError(f"proposal stage is {proposal.get('stage')!r}, not seconded")
    if (proposal.get("proposer") or {}).get("sub") == me:
        raise RuntimeError("measurer is not disjoint from the proposer")
    if any(
        row.get("metric") == "unclaimed_verdict_flips" and row.get("evidence_state") == "valid"
        for row in proposal.get("measurements", [])
    ):
        raise RuntimeError("a valid original already exists")
    if snapshot.get("kind") != "dexagon.replication-consensus-decision-surface.v1" or snapshot.get("count") != len(snapshot.get("proposals", [])):
        raise RuntimeError("snapshot schema or count is invalid")
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", IMPLEMENTATION, "HEAD"], cwd=SYMFONY,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    ).returncode != 0:
        raise RuntimeError("implementation commit is not in the audited Symfony tree")
    if git_output("status", "--porcelain"):
        raise RuntimeError("evidence repository is not clean")
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", "HEAD", "origin/main"], cwd=EVIDENCE_REPO,
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    return {
        "proposal_stage": proposal["stage"],
        "disjoint_from_proposer": True,
        "existing_valid_originals": 0,
        "snapshot_count": snapshot["count"],
        "snapshot_sha256": sha256(SNAPSHOT),
        "implementation_commit": IMPLEMENTATION,
        "manifest_commitment": manifest_commitment(manifest),
    }


def abort_if_open(client, attempt_id: str, detail: str, checked: dict) -> dict:
    state = client.attempt(attempt_id)
    if state.get("state") != "open":
        return {"attempt_state": state.get("state"), "abort_sent": False}
    evidence = {
        "kind": "ainglish.preflight-failure.v1",
        "at": datetime.now(timezone.utc).isoformat(),
        "attempt_id": attempt_id,
        "failed_gate_kind": "harness_error",
        "failed_gate": detail,
        "preflight": checked,
    }
    return {
        "abort_sent": True,
        "result": client.abort_attempt(attempt_id, detail[:160], evidence, failed_gate_kind="harness_error"),
    }


def main() -> None:
    client = ainglish_client()
    snapshot = json.loads(SNAPSHOT.read_text())
    manifest = build_manifest(snapshot)
    checked = preflight(client, manifest, snapshot)
    if "--preflight" in sys.argv:
        print(json.dumps(checked, indent=2, sort_keys=True))
        return
    if RECEIPT.exists():
        raise SystemExit(f"REFUSING: {RECEIPT.name} already exists")

    opened = client.mint_attempt(
        SLUG,
        manifest=manifest,
        estimand=(
            "The count of live decision-bearing proposal surfaces or production consumers that "
            "read replication_consensus outside its single claimed top-level report-only serializer "
            "assignment, over the complete frozen 190-proposal population and pinned implementation."
        ),
        admissibility_gates=[
            "fresh authenticated suggestions and proposal detail still route an original on a seconded proposal",
            "no valid original exists and this principal is disjoint from the proposer",
            "the complete bounded projection, source digests, implementation commit, exact allowed consumer, and analysis are published before evaluation",
            "every finite integer is filed once, including a positive refutation",
        ],
        planned_sample={
            "proposals": snapshot["count"],
            "decision_fields": list(DECISION_FIELDS),
            "source_tree": "every production src/**/*.php file",
            "instrument": MODEL,
        },
    )["attempt"]
    try:
        value, computed = evaluate(snapshot)
        filed = client.measure(SLUG, {
            "metric": "unclaimed_verdict_flips",
            "formula_version": 1,
            "value": value,
            "panel_models": [MODEL],
            "per_member": [{"model": MODEL, "value": value}],
            "panel_neff": 1,
            "manifest": manifest,
            "attempt_id": opened["attempt_id"],
        })
    except Exception as exc:
        closure = abort_if_open(client, opened["attempt_id"], f"{type(exc).__name__}: {exc}", checked)
        print(json.dumps({"status": "aborted_or_closed", "closure": closure}, indent=2))
        raise
    receipt = {
        "kind": "ainglish.unclaimed-verdict-flips-original.v1",
        "proposal": SLUG,
        "attempt": opened,
        "preflight": checked,
        "computed": computed,
        "measurement": filed,
        "manifest_commitment": manifest_commitment(manifest),
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
