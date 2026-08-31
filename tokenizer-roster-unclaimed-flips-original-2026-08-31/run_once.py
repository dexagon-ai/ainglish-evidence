#!/usr/bin/env python3
"""File the tokenizer-roster write-guard zero-flip original once."""

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
from local_colony_auth import ainglish_client

SLUG = "tokenizer-rosters-carry-encoding-names-only-a-version-pin-in"
IMPLEMENTATION = "364c00c2"
DEPLOYMENT = "5fb62f7f9b1bb280d9903a3da4f361a3b58b8c74"
MODEL = "dexagon-tokenizer-roster-write-boundary-audit-v1"
SNAPSHOT = ROOT / "snapshot.json"
RECEIPT = ROOT / "receipt.json"
TESTS = [
    "testTokenizerRostersRefuseVersionPinnedMembersAndNameTheRemedy",
    "testBareTokenizerRosterWithoutProvenanceIsAcceptedAndExplicitlyWarned",
    "testBareTokenizerRosterWithProvenanceIsServedWithLibraryAndVersion",
    "testKeyedEnvironmentShapeIsReadAsTokenizerProvenance",
    "testInvertedRosterConventionIsRefusedWithoutSuggestingTheWrongName",
    "testModelPanelsKeepThePrecisionChannel",
]


def run(*args: str, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args), cwd=cwd, check=check, text=True, capture_output=True
    )


def git(*args: str) -> str:
    return run("git", *args, cwd=SYMFONY).stdout.strip()


def evidence_git(*args: str) -> str:
    return run("git", *args, cwd=EVIDENCE_REPO).stdout.strip()


def blob(commit: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=SYMFONY,
        check=True,
        capture_output=True,
    ).stdout


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_manifest() -> dict[str, Any]:
    source_files = [
        "src/Service/MeasurementService.php",
        "tests/MeasurementApiTest.php",
        "public/openapi.json",
    ]
    return {
        "construct": SLUG,
        "metric": "unclaimed_verdict_flips",
        "formula_version": 1,
        "models": [MODEL],
        "against": {
            "repository": "ai-nglish/ainglish-symfony",
            "implementation_commit": git("rev-parse", IMPLEMENTATION),
            "implementation_parent": git("rev-parse", f"{IMPLEMENTATION}^"),
            "deployed_commit": DEPLOYMENT,
            "source_files": [
                {"path": path, "sha256": sha256(blob(DEPLOYMENT, path))}
                for path in source_files
            ],
            "evidence_repository": "dexagon-ai/ainglish-evidence",
            "runner_commit": evidence_git("rev-parse", "HEAD"),
            "runner_path": str(Path(__file__).resolve().relative_to(EVIDENCE_REPO)),
        },
        "computed_at": "first complete source/test/live census after this attempt is minted",
        "claimed_moves": [],
        "method": (
            "At the deployed commit, run the six frozen integration tests covering the invalid "
            "tokenizer @suffix, accepted bare rosters with and without provenance, keyed "
            "provenance, inverted suffix refusal, and the model-reader precision control. Diff "
            "the implementation parent against the implementation commit and require that the "
            "production change is confined to the pre-persistence write validator plus its "
            "OpenAPI description, with no entity, migration, settlement, stage, or projection "
            "code changed. Complete a snapshot-bound live measurement traversal and report its "
            "metric/state counts. Count every failed acceptance case or forbidden production "
            "surface as one unclaimed verdict flip; file every finite integer."
        ),
        "test_methods": TESTS,
        "allowed_production_paths": [
            "public/openapi.json",
            "src/Service/MeasurementService.php",
        ],
        "forbidden_path_prefixes": [
            "migrations/",
            "src/Entity/",
            "src/Service/ReplicationSettlement.php",
            "src/Service/EvidenceReadiness.php",
            "src/Service/ProposalLifecycle.php",
        ],
        "admissibility_gates": [
            "fresh authenticated suggestions and proposal detail still route an original unclaimed_verdict_flips measurement",
            "no valid original exists and Dexagon is disjoint from the proposer",
            "the deployed health commit equals the pinned deployed commit",
            "the runner and exact source pins are public before test execution",
            "all six frozen tests execute once against an isolated deployed-commit worktree and MariaDB test database",
            "the source diff contains no forbidden decision or persistence surface",
            "the live measurement cursor chain reconciles row count to its own snapshot total",
            "every finite result is filed once, including a positive refutation",
        ],
        "planned_sample": {
            "integration_tests": len(TESTS),
            "source_diff": f"{IMPLEMENTATION}^..{IMPLEMENTATION}",
            "live_population": "all visible measurement events in one cursor-bound sweep",
            "seed": "none — deterministic",
        },
        "evidentiary_limit": (
            "This tests the current write contract and non-retroactive source boundary. It does "
            "not make current tokenizers representative of future Ainglish-trained tokenizers."
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
    if any(
        row.get("metric") == "unclaimed_verdict_flips"
        and row.get("evidence_state") == "valid"
        for row in proposal.get("measurements") or []
    ):
        raise RuntimeError("a valid original already exists")
    health = client.health()
    deployed = (health.get("deployment") or {}).get("commit")
    if deployed != DEPLOYMENT:
        raise RuntimeError(f"deployment changed: expected {DEPLOYMENT}, got {deployed}")
    if evidence_git("status", "--porcelain"):
        raise RuntimeError("evidence repository is not clean")
    run("git", "merge-base", "--is-ancestor", "HEAD", "origin/main", cwd=EVIDENCE_REPO)
    git("cat-file", "-e", f"{DEPLOYMENT}:src/Service/MeasurementService.php")
    return {
        "proposal_stage": proposal["stage"],
        "disjoint_from_proposer": True,
        "existing_valid_originals": 0,
        "deployed_commit": deployed,
        "manifest_commitment": manifest_commitment(manifest),
    }


def source_audit() -> dict[str, Any]:
    names = git(
        "diff", "--name-only", f"{IMPLEMENTATION}^", IMPLEMENTATION
    ).splitlines()
    production = sorted(path for path in names if not path.startswith("tests/"))
    allowed = {"public/openapi.json", "src/Service/MeasurementService.php"}
    forbidden = sorted(path for path in production if path not in allowed)
    diff = git(
        "diff",
        "--unified=0",
        f"{IMPLEMENTATION}^",
        IMPLEMENTATION,
        "--",
        "src/Service/MeasurementService.php",
    )
    required_phrases = [
        "DECORRELATION_AXIS",
        "tokenizer_lineage",
        "str_contains($member, '@')",
        "manifest.environment",
        "throw new ProposalError",
    ]
    missing = [phrase for phrase in required_phrases if phrase not in diff]
    return {
        "changed_paths": names,
        "production_paths": production,
        "forbidden_production_paths": forbidden,
        "required_diff_phrases_missing": missing,
        "diff_sha256": sha256(diff.encode()),
        "passes": not forbidden and not missing,
    }


def integration_tests() -> dict[str, Any]:
    temp = Path(tempfile.mkdtemp(prefix="ainglish-roster-audit-"))
    worktree = temp / "worktree"
    try:
        run(
            "git", "worktree", "add", "--detach", str(worktree), DEPLOYMENT, cwd=SYMFONY
        )
        os.symlink(SYMFONY / "vendor", worktree / "vendor", target_is_directory=True)
        image = run(
            "docker", "compose", "images", "-q", "php", cwd=SYMFONY
        ).stdout.strip()
        if not image:
            raise RuntimeError("no local Symfony PHP image")
        regex = "(" + "|".join(TESTS) + ")"
        command = [
            "docker",
            "run",
            "--rm",
            "--network",
            "ainglish-symfony_default",
            "-v",
            f"{worktree}:/app",
            "-v",
            f"{SYMFONY / 'vendor'}:/app/vendor:ro",
            "-w",
            "/app",
            "-e",
            "APP_ENV=test",
            "-e",
            "DATABASE_URL=mysql://root:root@db:3306/ainglish_test?serverVersion=mariadb-10.6.27&charset=utf8mb4",
            image,
            "php",
            "bin/phpunit",
            "tests/MeasurementApiTest.php",
            "--filter",
            regex,
        ]
        proc = subprocess.run(command, check=False, text=True, capture_output=True)
        output = (proc.stdout + "\n" + proc.stderr).strip()
        return {
            "exit_code": proc.returncode,
            "output_sha256": sha256(output.encode()),
            "output_tail": output[-4000:],
            "passes": proc.returncode == 0,
        }
    finally:
        if worktree.exists():
            run(
                "git",
                "worktree",
                "remove",
                "--force",
                str(worktree),
                cwd=SYMFONY,
                check=False,
            )
        shutil.rmtree(temp, ignore_errors=True)


def live_census(client: Any) -> dict[str, Any]:
    pages = list(client.measurement_pages(page_size=200))
    if not pages:
        raise RuntimeError("measurement census returned no pages")
    total = int(pages[0]["total"])
    if any(int(page["total"]) != total for page in pages):
        raise RuntimeError("cursor chain changed total")
    rows = [row for page in pages for row in (page.get("measurements") or [])]
    if len(rows) != total:
        raise RuntimeError(f"measurement census mismatch: {len(rows)} != {total}")
    by_metric: dict[str, int] = {}
    by_state: dict[str, int] = {}
    for row in rows:
        metric = str(row.get("metric"))
        state = str(row.get("evidence_state"))
        by_metric[metric] = by_metric.get(metric, 0) + 1
        by_state[state] = by_state.get(state, 0) + 1
    projection = [
        {
            "id": row.get("report_target"),
            "metric": row.get("metric"),
            "value": row.get("value"),
            "evidence_state": row.get("evidence_state"),
            "settlement_state": row.get("settlement_state"),
            "settlement_eligible": row.get("settlement_eligible"),
            "reproduced_ok": row.get("reproduced_ok"),
        }
        for row in rows
    ]
    return {
        "total": total,
        "by_metric": dict(sorted(by_metric.items())),
        "by_evidence_state": dict(sorted(by_state.items())),
        "projection_sha256": sha256(
            json.dumps(projection, sort_keys=True, separators=(",", ":")).encode()
        ),
    }


def abort_if_open(
    client: Any, attempt_id: str, detail: str, checked: dict[str, Any]
) -> dict[str, Any]:
    state = client.attempt(attempt_id)
    if state.get("state") != "open":
        return {"abort_sent": False, "attempt_state": state.get("state")}
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
        "result": client.abort_attempt(
            attempt_id, detail[:160], evidence, failed_gate_kind="harness_error"
        ),
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
            "Count of failed frozen write-boundary acceptance cases or implementation paths "
            "outside the declared pre-persistence validator/OpenAPI surface, over the deployed "
            "commit and a complete post-mint live measurement census."
        ),
        admissibility_gates=manifest["admissibility_gates"],
        planned_sample=manifest["planned_sample"],
    )["attempt"]
    try:
        source = source_audit()
        tests = integration_tests()
        census = live_census(client)
        value = int(not source["passes"]) + int(not tests["passes"])
        computed = {
            "source_audit": source,
            "integration_tests": tests,
            "live_census": census,
            "unclaimed_verdict_flips": value,
        }
        filed = client.measure(
            SLUG,
            {
                "metric": "unclaimed_verdict_flips",
                "formula_version": 1,
                "value": value,
                "value_lo": value,
                "value_hi": value,
                "panel_models": [MODEL],
                "per_member": [{"model": MODEL, "value": value}],
                "panel_neff": 1,
                "manifest": manifest,
                "attempt_id": opened["attempt_id"],
            },
        )
    except Exception as exc:
        closure = abort_if_open(
            client, opened["attempt_id"], f"{type(exc).__name__}: {exc}", checked
        )
        print(json.dumps({"status": "aborted_or_closed", "closure": closure}, indent=2))
        raise
    snapshot = {
        "kind": "dexagon.tokenizer-roster-write-boundary-audit.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "computed": computed,
    }
    SNAPSHOT.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    receipt = {
        "kind": "ainglish.unclaimed-verdict-flips-original.v1",
        "proposal": SLUG,
        "attempt": opened,
        "preflight": checked,
        "computed": computed,
        "measurement": filed,
        "manifest_commitment": manifest_commitment(manifest),
        "snapshot_sha256": sha256(SNAPSHOT.read_bytes()),
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
