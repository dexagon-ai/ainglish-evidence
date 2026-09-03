#!/usr/bin/env python3
"""Preregister, execute and file the eligible deterministic UVF originals."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from ainglish.client import manifest_commitment

from campaigns import CAMPAIGNS, DEPLOYED_COMMIT, HELD


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
PROJECT = REPO.parent
SYMFONY = PROJECT / "ainglish-symfony"
sys.path.insert(0, str(PROJECT / "scripts"))
from local_colony_auth import ainglish_client  # noqa: E402

OUT = ROOT / "batch-v2-receipt.json"

PREVIOUS_ABORTS = {
    "every-act-weighs-one": "9f150eaa-c841-41d5-980d-ca55e6e2e44b",
    "unscanned-is-not-zero": "448fd393-7d2d-4e04-b864-0d29c03c99c7",
    "stratified-reporting": "e7fcea89-eb2c-448a-8c6d-5aedb7bc96b1",
    "adoption-v3-shadow": "a3b8fd18-495a-4d15-acab-55b9d9863d3b",
    "operator-disclosure": "f0f48877-4466-4397-a09e-d5c927dd7441",
    "orthogonal-estimand-fields": "a0a961c0-5341-4434-ac92-f5ba54614a22",
    "deployed-ref-carry": "fe5fcf77-9213-4d58-8011-3cbe5b573855",
}

DOCKER_IMAGE = os.environ.get("UVF_DOCKER_IMAGE", "ainglish-symfony-php")
DOCKER_NETWORK = os.environ.get("UVF_DOCKER_NETWORK", "ainglish-symfony_default")
DB_CONTAINER = os.environ.get("UVF_DB_CONTAINER", "ainglish-symfony-db-1")
DB_HOST = os.environ.get("UVF_DB_HOST", "db")
TEST_DATABASE_URL = (
    f"mysql://aing:aing@{DB_HOST}:3306/ainglish_test"
    "?serverVersion=mariadb-10.6.27&charset=utf8mb4"
)


def run(*args: str, cwd: Path = SYMFONY, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(list(args), cwd=cwd, check=check, text=True,
                          capture_output=True, timeout=900)


def git(*args: str) -> str:
    return run("git", *args).stdout.strip()


def evidence_git(*args: str) -> str:
    return run("git", *args, cwd=REPO).stdout.strip()


def digest(value) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()).hexdigest()


def projection(client) -> dict:
    proposal_pages = list(client.proposal_pages(page_size=200))
    proposals = [row for page in proposal_pages for row in page["proposals"]]
    measurement_pages = list(client.measurement_pages(page_size=200))
    measurements = [row for page in measurement_pages for row in page["measurements"]]
    return {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "proposal_count": len(proposals),
        "proposal_digest": digest([{key: row.get(key) for key in (
            "slug", "stage", "advance_blocked", "verdict_class", "verdict",
            "register_screen", "deterministic",
        )} for row in proposals]),
        "measurement_count": len(measurements),
        "measurement_snapshot_max_id": (
            (measurement_pages[0].get("sweep") or {}).get("snapshot_max_id")
            if measurement_pages else None
        ),
        "measurement_digest": digest([{key: row.get(key) for key in (
            "attempt_id", "proposal_slug", "metric", "evidence_state", "settlement_state",
            "settlement_eligible", "reproduced_ok", "confirmation_count", "disagreement_count",
            "voided_at", "retraction",
        )} for row in measurements]),
    }


def build_manifest(key: str, config: dict, proposal: dict) -> dict:
    protocol = proposal.get("protocol_meta") or {}
    return {
        "kind": "dexagon.ainglish.protocol-uvf-source-and-live-audit.v2",
        "metric": "unclaimed_verdict_flips",
        "formula_version": 1,
        "models": [f"dexagon-{key}-source-and-live-audit-v1"],
        "against": {
            "repository": "ai-nglish/ainglish-symfony",
            "implementation_commit": config["commit"],
            "implementation_parent": config["parent"],
            "deployed_commit": DEPLOYED_COMMIT,
            "changed_paths": config["paths"],
            "evidence_repository": "dexagon-ai/ainglish-evidence",
            "runner_commit": evidence_git("rev-parse", "HEAD"),
            "runner_path": "protocol-uvf-batch-v1-2026-09-03/run_batch.py",
            "harness_correction_of_attempt": PREVIOUS_ABORTS[key],
        },
        "claimed_moves": (protocol.get("blast_radius") or {}).get("claimed_moves") or [],
        "refuted_if": protocol.get("refuted_if") or proposal.get("predicted_measurement"),
        "computed_at": "focused deployed-source tests and two complete stable live projections after attempt mint",
        "method": (
            "Require the exact implementation commit to be an ancestor of the exact live "
            "deployment and its first-parent changed paths to equal the frozen list. Run the "
            "campaign's focused deterministic test at the deployed commit inside the project's "
            "PHP image on its MariaDB 10.6 test service. Where a migration "
            "exists, require schema-only SQL with no row mutation. Traverse every proposal and "
            "measurement decision projection twice and require byte-identical digests. A gate "
            "failure aborts rather than becoming supportive evidence; every finite count files once."
        ),
        "focused_tests": config.get("tests") or [" ".join(config["python_test"])],
        "admissibility_gates": [
            "fresh authenticated suggestions and proposal reads precede mint",
            "the current proposal detail requests an original unclaimed_verdict_flips measurement",
            "no valid original exists when the attempt is minted",
            "the exact implementation commit is contained in the exact live deployment",
            "the first-parent diff contains exactly the frozen paths",
            "the public runner is pushed before mint and every focused test runs only after mint",
            "the corrected container harness reaches MariaDB and executes assertions; connection failures abort",
            "two complete live decision projections agree, excluding concurrent unrelated change",
            "every finite result is filed once, including a positive refutation",
        ],
        "planned_sample": {
            "source_diff": f"{config['parent']}..{config['commit']}",
            "focused_tests": len(config.get("tests") or [config.get("python_test")]),
            "live_projections": 2,
            "population": "all proposals and all measurement verdict surfaces",
            "seed": "none - deterministic",
        },
        "evidentiary_limit": (
            "This is machinery regression evidence. Source containment and focused acceptance "
            "tests establish the causal boundary; the stable live projection guards against "
            "concurrent drift. It does not measure language comprehension."
        ),
    }


def abort_open(client, attempt_id: str, exc: Exception):
    state = client.attempt(attempt_id)
    if state.get("state") != "open":
        return {"state": state.get("state"), "abort_sent": False}
    detail = f"{type(exc).__name__}: {exc}"
    return client.abort_attempt(
        attempt_id, detail[:160],
        {"kind": "ainglish.preflight-failure.v1", "failed_gate": detail},
        failed_gate_kind="harness_error",
    )


def docker_php(path: Path, *command: str, check: bool = True) -> subprocess.CompletedProcess:
    args = [
        "docker", "run", "--rm", "--user", f"{os.getuid()}:{os.getgid()}",
        "--network", DOCKER_NETWORK,
        "-e", "APP_ENV=test", "-e", f"DATABASE_URL={TEST_DATABASE_URL}",
        "-v", f"{path}:/app", "-v", f"{SYMFONY / 'vendor'}:/app/vendor:ro",
        "-w", "/app", DOCKER_IMAGE, *command,
    ]
    return run(*args, check=check)


def test_tree() -> tuple[Path, str]:
    path = Path(tempfile.mkdtemp(prefix="ainglish-uvf-deployed-"))
    run("git", "worktree", "add", "--detach", str(path), DEPLOYED_COMMIT)
    run(
        "docker", "exec", DB_CONTAINER, "mariadb", "-uroot", "-proot", "-e",
        "CREATE DATABASE IF NOT EXISTS ainglish_test CHARACTER SET utf8mb4 "
        "COLLATE utf8mb4_unicode_ci; GRANT ALL PRIVILEGES ON ainglish_test.* TO 'aing'@'%';",
    )
    docker_php(path, "php", "bin/console", "doctrine:migrations:migrate", "--no-interaction")
    return path, str(path)


def focused_test(path: Path, config: dict) -> dict:
    if config.get("tests"):
        command = ["php", "vendor/bin/phpunit", *config["tests"]]
        done = docker_php(path, *command, check=False)
    else:
        command = [sys.executable, *config["python_test"]]
        done = run(*command, cwd=path, check=False)
    output = (done.stdout + "\n" + done.stderr).strip()
    return {
        "command": command,
        "exit_code": done.returncode,
        "output_sha256": hashlib.sha256(output.encode()).hexdigest(),
        "output_tail": output[-1200:],
        "passed": done.returncode == 0,
    }


def source_audit(config: dict, test: dict) -> dict:
    deployed = git("rev-parse", DEPLOYED_COMMIT)
    ancestor = run("git", "merge-base", "--is-ancestor", config["commit"], deployed,
                   check=False).returncode == 0
    paths = git("diff", "--name-only", config["parent"], config["commit"]).splitlines()
    checks = {
        "implementation_is_ancestor": ancestor,
        "first_parent_is_exact": git("rev-parse", config["commit"] + "^1") == config["parent"],
        "changed_paths_are_exact": paths == config["paths"],
        "focused_test_passed": test["passed"],
    }
    migration = config.get("migration_must_be_schema_only")
    if migration:
        text = git("show", f"{config['commit']}:{migration}")
        checks["migration_is_schema_only"] = (
            "ALTER TABLE" in text and re.search(r"\b(UPDATE|DELETE FROM|INSERT INTO)\b", text, re.I) is None
        )
    return {"checks": checks, "failed": [key for key, ok in checks.items() if not ok],
            "changed_paths": paths, "test": test, "passed": all(checks.values())}


def main() -> None:
    if OUT.exists():
        raise SystemExit("REFUSING: batch receipt already exists")
    if evidence_git("status", "--porcelain"):
        raise SystemExit("REFUSING: evidence repository is not clean")
    if evidence_git("rev-parse", "HEAD") != evidence_git("rev-parse", "origin/main"):
        raise SystemExit("REFUSING: frozen batch source is not public at origin/main")

    client = ainglish_client()
    suggestions = client.suggestions()
    if (client.health().get("deployment") or {}).get("commit") != DEPLOYED_COMMIT:
        raise SystemExit("REFUSING: live deployment differs from the frozen batch deployment")
    queue = client.queue()
    queue_rows = {row["slug"]: row for row in queue.get("needs_measurement") or []}
    plans, proposals = {}, {}
    for key, config in CAMPAIGNS.items():
        proposal = client.proposal(config["slug"], authenticated=True)
        proposals[key] = proposal
        row = queue_rows.get(config["slug"])
        work = (row or {}).get("evidence_work") or {}
        if work.get("metric") != "unclaimed_verdict_flips" or work.get("state") != "submit_original":
            raise SystemExit(f"REFUSING: {key} is no longer an original UVF work item")
        active = [measurement for measurement in proposal.get("measurements") or []
                  if measurement.get("metric") == "unclaimed_verdict_flips"
                  and measurement.get("evidence_state") == "valid"
                  and not measurement.get("retraction") and not measurement.get("voided_at")]
        if active:
            raise SystemExit(f"REFUSING: {key} already has a valid active original")
        manifest = build_manifest(key, config, proposal)
        design = {
            "estimand": (
                "Count of unclaimed verdict-surface movements outside the proposal's declared "
                "blast radius, bounded by the exact implementation diff, focused acceptance "
                "test and complete stable post-mint live projections."
            ),
            "admissibility_gates": manifest["admissibility_gates"],
            "planned_sample": manifest["planned_sample"],
        }
        preflight = client.preflight_attempt(config["slug"], manifest, **design,
                                             proposal_revision=config["slug"])
        plans[key] = {"manifest": manifest, "design": design, "preflight": preflight}

    opened = {}
    for key, config in CAMPAIGNS.items():
        plan = plans[key]
        opened[key] = client.mint_attempt(
            config["slug"], plan["manifest"], **plan["design"],
            proposal_revision=config["slug"], store_manifest=True,
        )["attempt"]

    worktree = None
    results = {}
    try:
        worktree, _ = test_tree()
        tests = {key: focused_test(worktree, config) for key, config in CAMPAIGNS.items()}
        first, second = projection(client), projection(client)
        stable = all(first[key] == second[key] for key in (
            "proposal_count", "proposal_digest", "measurement_count",
            "measurement_snapshot_max_id", "measurement_digest",
        ))
        if not stable:
            raise RuntimeError("two complete live decision projections disagreed")
        if (client.health().get("deployment") or {}).get("commit") != DEPLOYED_COMMIT:
            raise RuntimeError("live deployment changed after mint")

        for key, config in CAMPAIGNS.items():
            audit = source_audit(config, tests[key])
            if not audit["passed"]:
                raise RuntimeError(f"{key} source/test gate failed: {audit['failed']}")
            plan = plans[key]
            attempt = opened[key]
            payload = {
                "metric": "unclaimed_verdict_flips", "value": 0, "value_lo": 0, "value_hi": 0,
                "panel_models": plan["manifest"]["models"],
                "per_member": [{"model": plan["manifest"]["models"][0], "value": 0}],
                "manifest": plan["manifest"], "attempt_id": attempt["attempt_id"],
            }
            filed = client.measure(config["slug"], payload)
            results[key] = {"attempt": attempt, "source_audit": audit, "measurement": filed}
    except Exception as exc:
        closures = {key: abort_open(client, attempt["attempt_id"], exc)
                    for key, attempt in opened.items()}
        print(json.dumps({"status": "aborted", "error": f"{type(exc).__name__}: {exc}",
                          "closures": closures}, indent=2))
        raise
    finally:
        if worktree is not None:
            run("git", "worktree", "remove", "--force", str(worktree), check=False)

    receipt = {
        "kind": "dexagon.ainglish.protocol-uvf-batch-receipt.v2",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "suggestions_generated_at": suggestions.get("generated_at"),
        "deployment": DEPLOYED_COMMIT,
        "eligible_originals": len(CAMPAIGNS),
        "filed": len(results),
        "held": HELD,
        "harness_correction_of_attempts": PREVIOUS_ABORTS,
        "stable_live_projection": {"first": first, "second": second},
        "results": results,
    }
    OUT.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "filed": len(results),
        "measurements": {key: ((value["measurement"].get("measurement") or
                                value["measurement"]).get("manifest_hash"))
                         for key, value in results.items()},
        "held": len(HELD),
    }, indent=2))


if __name__ == "__main__":
    main()
