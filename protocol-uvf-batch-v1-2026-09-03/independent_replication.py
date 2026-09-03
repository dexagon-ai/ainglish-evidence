#!/usr/bin/env python3
"""Run one independent fresh UVF replication against the current deployment."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from ainglish.client import AinglishClient

from campaigns import CAMPAIGNS


ROOT = Path(__file__).resolve().parent
TARGETS = {
    "every-act-weighs-one": "157de4300bb4fc958b91c05c0c209520861350291b12f20e5460a90037ab8210",
    "unscanned-is-not-zero": "c6b475d7b4a0559273524a78f8d99576d25c0ebbf2096c373f0baa12866c0e35",
    "stratified-reporting": "59de7d622979f618fabb0607a7723982cec699efc0c4c3c90383dcda9cb78508",
    "adoption-v3-shadow": "fa39e66715dc656192264ce4f2c0b7e13573f91a59b017ed2797b4a5ab50a998",
    "operator-disclosure": "1ab1cf104ffe31b28ea69fb7e3d2a0b32e177adf00d744d5d9079f50c3c189d2",
    "orthogonal-estimand-fields": "23ee8a2cd1b11a814592a1275119290b3c6ba6d7a6d4361d6bcae6a813db6879",
    "deployed-ref-carry": "77bbd8282c7f63b6583d65fce3c2de78ba83d5708c85a0778b8d058b2fb68496",
}


def run(*args: str, cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(list(args), cwd=cwd, check=check, text=True,
                          capture_output=True, timeout=900)


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()).hexdigest()


def projection(client: AinglishClient) -> dict:
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


def main() -> None:
    raise SystemExit(
        "REFUSING: this campaign is suspended pending proposal-specific, "
        "falsifiable UVF estimands; see README.md"
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("key", choices=sorted(TARGETS))
    parser.add_argument("--symfony", type=Path,
                        default=Path(os.environ.get("AINGLISH_SYMFONY_PATH", "ainglish-symfony")))
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    key = args.key
    config = CAMPAIGNS[key]
    symfony = args.symfony.resolve()
    if not (symfony / ".git").exists():
        raise SystemExit("REFUSING: --symfony must name an ai-nglish/ainglish-symfony checkout")
    out = (args.out or ROOT / f"independent-{key}-receipt.json").resolve()
    if out.exists():
        raise SystemExit("REFUSING: output receipt already exists")

    client = AinglishClient()
    suggestions = client.suggestions()
    identity = client.whoami()
    proposal = client.proposal(config["slug"], authenticated=True)
    target_wrap = client.measurement(TARGETS[key])
    target = target_wrap.get("measurement") or target_wrap
    if target.get("evidence_state") != "valid" or target.get("is_replication"):
        raise SystemExit("REFUSING: target is not a valid original")
    if (target.get("submitter") or {}).get("sub") == identity.get("sub"):
        raise SystemExit("REFUSING: a principal cannot independently replicate its own original")
    if any(
        row.get("is_replication") and row.get("replicates_hash") == TARGETS[key]
        and (row.get("submitter") or {}).get("sub") == identity.get("sub")
        for row in proposal.get("measurements") or []
    ):
        raise SystemExit("REFUSING: this principal already supplied a replication voice")

    deployed = (client.health().get("deployment") or {}).get("commit")
    if not isinstance(deployed, str) or len(deployed) != 40:
        raise SystemExit("REFUSING: exact live deployment commit unavailable")
    run("git", "fetch", "origin", "master", cwd=symfony)
    if run("git", "merge-base", "--is-ancestor", config["commit"], deployed,
           cwd=symfony, check=False).returncode != 0:
        raise SystemExit("REFUSING: implementation is not contained in the live deployment")
    paths = run("git", "diff", "--name-only", config["parent"], config["commit"],
                cwd=symfony).stdout.splitlines()
    if paths != config["paths"]:
        raise SystemExit("REFUSING: frozen implementation boundary drifted")

    manifest = {
        "kind": "ainglish.protocol-uvf-independent-source-and-live-audit.v1",
        "metric": "unclaimed_verdict_flips",
        "formula_version": 1,
        "models": [f"independent-{identity['sub'][:8]}-{key}-audit-v1"],
        "replicates_hash": TARGETS[key],
        "against": {
            "repository": "ai-nglish/ainglish-symfony",
            "implementation_commit": config["commit"],
            "implementation_parent": config["parent"],
            "deployed_commit": deployed,
            "changed_paths": config["paths"],
            "runner": "dexagon-ai/ainglish-evidence/protocol-uvf-batch-v1-2026-09-03/independent_replication.py",
        },
        "method": (
            "After mint, run the focused deterministic acceptance test at the exact live deployment; "
            "then traverse every proposal and measurement decision surface twice. A stable census "
            "with no movement outside the declared implementation boundary files zero; every finite "
            "nonzero result is filed unchanged."
        ),
        "focused_tests": config.get("tests") or [" ".join(config["python_test"])],
        "evidentiary_limit": "Protocol regression evidence only; no language-comprehension claim.",
    }
    estimand = (
        "Count of verdict-surface movements outside the target proposal's declared implementation "
        "boundary, over the current complete live proposal and measurement projections."
    )
    gates = [
        "fresh authenticated suggestions and proposal/target reads precede mint",
        "the caller is independent of the target author and has not already replicated it",
        "the implementation commit remains an ancestor of the exact live deployment",
        "the frozen first-parent source paths and focused test are unchanged",
        "the focused test passes after mint",
        "two complete live projections are byte-identical after mint",
        "every finite result is filed exactly once regardless of direction",
    ]
    sample = {
        "source_diff": f"{config['parent']}..{config['commit']}",
        "focused_tests": len(config.get("tests") or [config.get("python_test")]),
        "live_projections": 2,
        "population": "all current proposal and measurement verdict surfaces",
        "seed": "none - deterministic",
    }
    preflight = client.preflight_attempt(config["slug"], manifest, estimand, gates, sample,
                                         proposal_revision=config["slug"])
    attempt = client.mint_attempt(config["slug"], manifest, estimand, gates, sample,
                                  proposal_revision=config["slug"], store_manifest=True)["attempt"]

    worktree = Path(tempfile.mkdtemp(prefix="ainglish-independent-uvf-"))
    compose_project = f"ainglish-uvf-{attempt['attempt_id'][:8]}"
    compose_started = False
    try:
        run("git", "worktree", "add", "--detach", str(worktree), deployed, cwd=symfony)
        if config.get("tests"):
            prefix = ["docker", "compose", "-p", compose_project]
            run(*prefix, "up", "-d", "db", cwd=worktree)
            compose_started = True
            run(*prefix, "run", "--rm", "--user", f"{os.getuid()}:{os.getgid()}",
                "php", "composer", "install", "--no-interaction", "--prefer-dist", cwd=worktree)
            run(*prefix, "exec", "-T", "db", "mariadb", "-uroot", "-proot", "-e",
                "CREATE DATABASE IF NOT EXISTS ainglish_test CHARACTER SET utf8mb4 "
                "COLLATE utf8mb4_unicode_ci; GRANT ALL PRIVILEGES ON ainglish_test.* TO 'aing'@'%';",
                cwd=worktree)
            database_url = (
                "mysql://aing:aing@db:3306/ainglish_test"
                "?serverVersion=mariadb-10.6.27&charset=utf8mb4"
            )
            run(*prefix, "run", "--rm", "--user", f"{os.getuid()}:{os.getgid()}",
                "-e", "APP_ENV=test", "-e", f"DATABASE_URL={database_url}", "php",
                "php", "bin/console", "doctrine:migrations:migrate", "--no-interaction",
                cwd=worktree)
            command = [*prefix, "run", "--rm", "--user", f"{os.getuid()}:{os.getgid()}",
                       "-e", "APP_ENV=test", "-e", f"DATABASE_URL={database_url}", "php",
                       "php", "vendor/bin/phpunit", *config["tests"]]
            tested = run(*command, cwd=worktree, check=False)
        else:
            command = [sys.executable, *config["python_test"]]
            tested = run(*command, cwd=worktree, check=False)
        if tested.returncode != 0:
            raise RuntimeError("focused acceptance test failed: " + (tested.stdout + tested.stderr)[-800:])
        first, second = projection(client), projection(client)
        keys = ("proposal_count", "proposal_digest", "measurement_count",
                "measurement_snapshot_max_id", "measurement_digest")
        if any(first[name] != second[name] for name in keys):
            raise RuntimeError("complete live projections changed during the census")
        payload = {
            "metric": "unclaimed_verdict_flips", "value": 0, "value_lo": 0, "value_hi": 0,
            "panel_models": manifest["models"],
            "per_member": [{"model": manifest["models"][0], "value": 0}],
            "manifest": manifest, "attempt_id": attempt["attempt_id"],
            "replicates_hash": TARGETS[key],
        }
        filed = client.measure(config["slug"], payload)
    except Exception as exc:
        state = client.attempt(attempt["attempt_id"])
        closure = None
        if state.get("state") == "open":
            closure = client.abort_attempt(
                attempt["attempt_id"], str(exc)[:160],
                {"kind": "ainglish.preflight-failure.v1", "failed_gate": str(exc)},
                failed_gate_kind="harness_error",
            )
        raise SystemExit(json.dumps({"status": "aborted", "closure": closure, "error": str(exc)}))
    finally:
        if compose_started:
            run("docker", "compose", "-p", compose_project, "down", "-v",
                cwd=worktree, check=False)
        run("git", "worktree", "remove", "--force", str(worktree), cwd=symfony, check=False)

    receipt = {
        "kind": "ainglish.protocol-uvf-independent-replication-receipt.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "suggestions_generated_at": suggestions.get("generated_at"),
        "identity": {"sub": identity.get("sub"), "display_name": identity.get("display_name")},
        "target": TARGETS[key], "deployment": deployed, "preflight": preflight,
        "attempt": attempt, "test": {"command": command, "exit_code": tested.returncode,
                                      "output_sha256": hashlib.sha256((tested.stdout + tested.stderr).encode()).hexdigest()},
        "projections": {"first": first, "second": second}, "measurement": filed,
    }
    out.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "filed", "key": key, "target": TARGETS[key],
                      "receipt": str(out)}, indent=2))


if __name__ == "__main__":
    main()
