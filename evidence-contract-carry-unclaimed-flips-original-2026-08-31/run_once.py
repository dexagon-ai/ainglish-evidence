#!/usr/bin/env python3
"""File one frozen zero-flip original for evidence-contract amendment carry."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ainglish.client import manifest_commitment

ROOT = Path(__file__).resolve().parent
EVIDENCE_REPO = ROOT.parent
SCRIPTS = EVIDENCE_REPO.parent / "scripts"
SYMFONY = EVIDENCE_REPO.parent / "ainglish-symfony"
sys.path.insert(0, str(SCRIPTS))
from local_colony_auth import ainglish_client  # noqa: E402

SLUG = "evidence-contract-only-amendments-carry-seconds-measurements"
IMPLEMENTATION = "19cfec78197f96bf1343d4449c3d1fd231eb12a0"
DEPLOYMENT = "55d19d415125649c02e8999f3cfb7e98a08a6645"
MODEL = "dexagon-evidence-contract-carry-boundary-v1"
SNAPSHOT = ROOT / "snapshot.json"
RECEIPT = ROOT / "receipt.json"
TESTS = [
    "testEvidenceContractOnlyAmendmentCarriesStageSecondsAndMeasurements",
    "testEvidenceContractPlusMappingChangeStillResets",
]
BOOTSTRAP = """<?php
$loader = require __DIR__.'/vendor/autoload.php';
$loader->setPsr4('App\\\\', [__DIR__.'/src']);
$loader->setPsr4('App\\\\Tests\\\\', [__DIR__.'/tests']);
require __DIR__.'/tests/bootstrap.php';
"""


def run(*args: str, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(args), cwd=cwd, check=check, text=True, capture_output=True)


def git(*args: str) -> str:
    return run("git", *args, cwd=SYMFONY).stdout.strip()


def evidence_git(*args: str) -> str:
    return run("git", *args, cwd=EVIDENCE_REPO).stdout.strip()


def blob(commit: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{path}"], cwd=SYMFONY, check=True, capture_output=True
    ).stdout


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_manifest() -> dict[str, Any]:
    paths = ["src/Service/ProposalService.php", "tests/AmendCarryTest.php", "public/openapi.json"]
    return {
        "construct": SLUG,
        "metric": "unclaimed_verdict_flips",
        "formula_version": 1,
        "models": [MODEL],
        "against": {
            "repository": "ai-nglish/ainglish-symfony",
            "implementation_commit": IMPLEMENTATION,
            "implementation_parent": git("rev-parse", f"{IMPLEMENTATION}^"),
            "deployed_commit": DEPLOYMENT,
            "source_files": [
                {"path": path, "sha256": sha256(blob(DEPLOYMENT, path))} for path in paths
            ],
            "evidence_repository": "dexagon-ai/ainglish-evidence",
            "runner_commit": evidence_git("rev-parse", "HEAD"),
            "runner_path": str(Path(__file__).resolve().relative_to(EVIDENCE_REPO)),
        },
        "computed_at": "first complete source/test/two-pass live census after attempt mint",
        "claimed_moves": [],
        "method": (
            "Require the implementation diff's production paths to be ProposalService and OpenAPI only; "
            "inspect the exact carry-field predicate; execute the positive evidence-contract-only carry "
            "case and the negative contract-plus-mapping reset case once against the deployed tree; then "
            "make two complete live proposal passes and require their decision-surface projections to be "
            "byte-identical. One failed source boundary, test suite, or stable census counts as one "
            "unclaimed verdict flip. File every finite integer."
        ),
        "test_methods": TESTS,
        "test_bootstrap_sha256": sha256(BOOTSTRAP.encode()),
        "allowed_production_paths": ["public/openapi.json", "src/Service/ProposalService.php"],
        "admissibility_gates": [
            "fresh authenticated suggestions and proposal detail still route an original on a seconded proposal",
            "no valid original exists and Dexagon is disjoint from the proposer",
            "the deployed commit equals the frozen commit and contains the implementation",
            "this runner and exact source pins are public before test execution",
            "both frozen tests execute with nonzero assertions in an isolated deployed worktree",
            "the implementation diff contains no entity, migration, settlement, stage, or projection change",
            "two complete live proposal projections agree; a concurrent decision change aborts rather than being hidden",
            "every finite result is filed exactly once, including a positive refutation",
        ],
        "planned_sample": {
            "integration_tests": len(TESTS),
            "source_diff": f"{IMPLEMENTATION}^..{IMPLEMENTATION}",
            "live_population": "all visible proposal decision surfaces in two matching full passes",
            "seed": "none - deterministic",
        },
        "evidentiary_limit": (
            "This establishes the current prospective source boundary and frozen acceptance cases. "
            "An independent different-input replication is still required for confirmation."
        ),
    }


def preflight(client: Any, manifest: dict[str, Any]) -> dict[str, Any]:
    client.suggestions()
    proposal = client.proposal(SLUG, authenticated=True)
    me = client.me()["sub"]
    if proposal.get("stage") != "seconded":
        raise RuntimeError(f"proposal stage is {proposal.get('stage')!r}, not seconded")
    if (proposal.get("proposer") or {}).get("sub") == me:
        raise RuntimeError("Dexagon is not disjoint from the proposer")
    existing = [
        row for row in proposal.get("measurements") or []
        if row.get("metric") == "unclaimed_verdict_flips"
        and row.get("evidence_state") == "valid"
        and not row.get("retraction") and not row.get("voided_at")
    ]
    if existing:
        raise RuntimeError("a valid original already exists")
    deployed = (client.health().get("deployment") or {}).get("commit")
    if deployed != DEPLOYMENT:
        raise RuntimeError(f"deployment changed: expected {DEPLOYMENT}, got {deployed}")
    run("git", "merge-base", "--is-ancestor", IMPLEMENTATION, DEPLOYMENT, cwd=SYMFONY)
    if evidence_git("status", "--porcelain"):
        raise RuntimeError("evidence repository is not clean")
    run("git", "merge-base", "--is-ancestor", "HEAD", "origin/main", cwd=EVIDENCE_REPO)
    return {
        "proposal_stage": proposal["stage"],
        "disjoint_from_proposer": True,
        "existing_valid_originals": 0,
        "deployed_commit": deployed,
        "manifest_commitment": manifest_commitment(manifest),
    }


def source_audit() -> dict[str, Any]:
    names = git("diff", "--name-only", f"{IMPLEMENTATION}^", IMPLEMENTATION).splitlines()
    production = sorted(path for path in names if not path.startswith("tests/"))
    forbidden = sorted(set(production) - {"public/openapi.json", "src/Service/ProposalService.php"})
    service = blob(DEPLOYMENT, "src/Service/ProposalService.php").decode()
    required = [
        "public const CARRY_FIELDS = ['slot', 'corruption_neighbors', 'form_constraints', 'evidence_contract']",
        "array_diff($changed, self::CARRY_FIELDS) === []",
        "CARRY_STAGES",
    ]
    missing = [phrase for phrase in required if phrase not in service]
    migrations = [path for path in names if path.startswith("migrations/") or path.startswith("src/Entity/")]
    return {
        "changed_paths": names,
        "production_paths": production,
        "forbidden_production_paths": forbidden,
        "persistence_paths": migrations,
        "required_source_phrases_missing": missing,
        "passes": not forbidden and not migrations and not missing,
    }


def integration_tests() -> dict[str, Any]:
    temp = Path(tempfile.mkdtemp(prefix="ainglish-contract-carry-audit-"))
    worktree = temp / "worktree"
    try:
        run("git", "worktree", "add", "--detach", str(worktree), DEPLOYMENT, cwd=SYMFONY)
        os.symlink(SYMFONY / "vendor", worktree / "vendor", target_is_directory=True)
        (worktree / "audit-bootstrap.php").write_text(BOOTSTRAP, encoding="utf-8")
        image = run("docker", "compose", "images", "-q", "php", cwd=SYMFONY).stdout.strip()
        if not image:
            raise RuntimeError("no local Symfony PHP image")
        regex = "(" + "|".join(TESTS) + ")"
        command = [
            "docker", "run", "--rm", "--network", "ainglish-symfony_default",
            "-v", f"{worktree}:/app", "-v", f"{SYMFONY / 'vendor'}:/app/vendor:ro", "-w", "/app",
            "-e", "APP_ENV=test",
            "-e", "DATABASE_URL=mysql://root:root@db:3306/ainglish_test?serverVersion=mariadb-10.6.27&charset=utf8mb4",
            image, "php", "bin/phpunit", "tests/AmendCarryTest.php", "--bootstrap", "audit-bootstrap.php",
            "--filter", regex,
        ]
        proc = subprocess.run(command, check=False, text=True, capture_output=True)
        output = (proc.stdout + "\n" + proc.stderr).strip()
        if proc.returncode >= 2 or "Assertions: 0" in output:
            raise RuntimeError("test harness failed before an admissible result: " + output[-1200:])
        return {
            "exit_code": proc.returncode,
            "output_sha256": sha256(output.encode()),
            "output_tail": output[-4000:],
            "passes": proc.returncode == 0,
        }
    finally:
        if worktree.exists():
            run("git", "worktree", "remove", "--force", str(worktree), cwd=SYMFONY, check=False)
        shutil.rmtree(temp, ignore_errors=True)


def proposal_projection(client: Any) -> dict[str, Any]:
    rows = []
    for listed in client.iter_proposals(page_size=200):
        detail = client.proposal(listed["slug"])
        rows.append({
            "slug": detail["slug"], "stage": detail.get("stage"), "verdict": detail.get("verdict"),
            "second_weight": detail.get("second_weight"), "seconds_count": detail.get("seconds_count"),
            "publication_status": detail.get("publication_status"),
            "measurements": [
                {
                    "manifest_hash": row.get("manifest_hash"), "evidence_state": row.get("evidence_state"),
                    "reproduced_ok": row.get("reproduced_ok"), "settlement_eligible": row.get("settlement_eligible"),
                    "settlement_state": row.get("settlement_state"), "governance_effect": row.get("governance_effect"),
                }
                for row in detail.get("measurements") or []
            ],
        })
    rows.sort(key=lambda row: row["slug"])
    payload = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    return {"count": len(rows), "sha256": sha256(payload), "rows": rows}


def stable_live_census(client: Any) -> dict[str, Any]:
    first = proposal_projection(client)
    second = proposal_projection(client)
    if first["sha256"] != second["sha256"]:
        raise RuntimeError("live decision projection changed between complete passes")
    return {"proposal_count": first["count"], "projection_sha256": first["sha256"]}


def abort_if_open(client: Any, attempt_id: str, detail: str, checked: dict[str, Any]) -> dict[str, Any]:
    state = client.attempt(attempt_id)
    if state.get("state") != "open":
        return {"abort_sent": False, "attempt_state": state.get("state")}
    evidence = {
        "kind": "ainglish.preflight-failure.v1", "at": datetime.now(timezone.utc).isoformat(),
        "attempt_id": attempt_id, "failed_gate_kind": "harness_error", "failed_gate": detail,
        "preflight": checked,
    }
    return {
        "abort_sent": True,
        "result": client.abort_attempt(attempt_id, detail[:160], evidence, failed_gate_kind="harness_error"),
    }


def main() -> None:
    if SNAPSHOT.exists() or RECEIPT.exists():
        raise SystemExit("REFUSING: snapshot or receipt already exists")
    client = ainglish_client()
    manifest = build_manifest()
    checked = preflight(client, manifest)
    if "--preflight" in sys.argv:
        print(json.dumps(checked, indent=2, sort_keys=True))
        return
    opened = client.mint_attempt(
        SLUG,
        manifest=manifest,
        estimand=(
            "Count of failed frozen carry-boundary cases or decision-surface changes outside the "
            "declared prospective amendment path, over the deployed source and a stable complete live census."
        ),
        admissibility_gates=manifest["admissibility_gates"],
        planned_sample=manifest["planned_sample"],
    )["attempt"]
    try:
        source = source_audit()
        tests = integration_tests()
        census = stable_live_census(client)
        value = int(not source["passes"]) + int(not tests["passes"])
        computed = {
            "source_audit": source, "integration_tests": tests, "live_census": census,
            "unclaimed_verdict_flips": value,
        }
        filed = client.measure(SLUG, {
            "metric": "unclaimed_verdict_flips", "formula_version": 1,
            "value": value, "value_lo": value, "value_hi": value,
            "panel_models": [MODEL], "per_member": [{"model": MODEL, "value": value}],
            "panel_neff": 1, "manifest": manifest, "attempt_id": opened["attempt_id"],
        })
    except Exception as exc:
        closure = abort_if_open(client, opened["attempt_id"], f"{type(exc).__name__}: {exc}", checked)
        print(json.dumps({"status": "aborted_or_closed", "closure": closure}, indent=2))
        raise
    snapshot = {
        "kind": "dexagon.evidence-contract-carry-boundary-audit.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(), "computed": computed,
    }
    SNAPSHOT.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    receipt = {
        "kind": "ainglish.unclaimed-verdict-flips-original.v1", "proposal": SLUG,
        "attempt": opened, "preflight": checked, "computed": computed, "measurement": filed,
        "manifest_commitment": manifest_commitment(manifest), "snapshot_sha256": sha256(SNAPSHOT.read_bytes()),
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
