#!/usr/bin/env python3
"""Run cross-repository mutation and regression gates for five false-positive paths."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "report.json"


CHECKS = (
    {
        "id": "answer-bearing-target-leakage",
        "risk": "a calibration teaches the target or its answer and certifies a reader on the claim itself",
        "surface": "sdk",
        "file": "src/ainglish/panel.py",
        "anchors": (
            "a relabelled control carrying entry.text must refuse before spend",
            "a control teaching one {separator}-separated target pole must refuse before spend",
            "learnability real items must carry the byte-identical marked",
        ),
    },
    {
        "id": "same-input-pseudo-replication",
        "risk": "a rerun reuses the original metric inputs and receives a settlement voice",
        "surface": "symfony",
        "file": "tests/SameInputReplicationRegressionTest.php",
        "anchors": (
            "same metric inputs build check",
            "overlapping metric inputs build check",
            "settlement_eligible",
        ),
    },
    {
        "id": "incomplete-careful-comparator",
        "risk": "a short or ambiguous English baseline is presented as a complete careful comparator",
        "surface": "symfony",
        "file": "src/Service/FlagshipQualification.php",
        "anchors": (
            "complete-careful-english-v1",
            "complete careful-English comparator not declared",
            "exact preregistered manifest bytes were not retained",
        ),
    },
    {
        "id": "dead-cell-denominator-drift",
        "risk": "transport or parsing loss changes the surviving denominator and manufactures an effect",
        "surface": "sdk",
        "file": "src/ainglish/empty_cell_guard.py",
        "anchors": (
            "max_cell_dead_rate",
            "max_total_dead_rate",
            "pooled dead rate",
        ),
    },
    {
        "id": "pooled-stratum-cancellation",
        "risk": "opposite form-level failures cancel in the pooled scalar and settle a multi-form claim",
        "surface": "symfony",
        "file": "tests/ReplicationSettlementTest.php",
        "anchors": (
            "the pooled scalar cancels exactly",
            "a pooled cancellation must not settle the claim",
            "aggregate_reproduced_ok",
        ),
    },
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True,
    ).stdout.strip()


def run(name: str, command: list[str], cwd: Path, timeout: int = 900) -> dict:
    completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    tail = (completed.stdout + completed.stderr).strip().splitlines()[-20:]
    return {
        "name": name,
        "command": command,
        "exit_code": completed.returncode,
        "passed": completed.returncode == 0,
        "output_tail": tail,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sdk-repo", type=Path, required=True)
    parser.add_argument("--symfony-repo", type=Path, required=True)
    args = parser.parse_args()
    if TARGET.exists():
        raise SystemExit("REFUSING: report.json already exists")
    repos = {"sdk": args.sdk_repo.resolve(), "symfony": args.symfony_repo.resolve()}

    source_checks = []
    for check in CHECKS:
        path = repos[check["surface"]] / check["file"]
        text = path.read_text(encoding="utf-8")
        missing = [anchor for anchor in check["anchors"] if anchor not in text]
        source_checks.append({
            **check,
            "source_sha256": sha256(path),
            "anchors_present": not missing,
            "missing_anchors": missing,
        })

    python = str(repos["sdk"] / ".venv" / "bin" / "python")
    if not Path(python).exists():
        python = "/home/dexagon/codex/dexagon/.venv/bin/python"
    sdk_env = f"PYTHONPATH={repos['sdk'] / 'src'}"
    test_dsn = "DATABASE_URL=mysql://aing:aing@db:3306/ainglish_test?serverVersion=mariadb-10.6.27&charset=utf8mb4"
    executions = [
        run("panel mutation selftest", ["/usr/bin/env", sdk_env, python, "-m", "ainglish.panel", "--selftest"], repos["sdk"]),
        run("dead-cell guard mutation selftest", ["/usr/bin/env", sdk_env, python, "-m", "ainglish.empty_cell_guard", "--selftest"], repos["sdk"]),
        run("client result-contract selftest", ["/usr/bin/env", sdk_env, python, "-m", "ainglish.client"], repos["sdk"]),
        run(
            "server replication and qualification regressions",
            [
                "docker", "compose", "exec", "-T", "-e", "APP_ENV=test", "-e", test_dsn,
                "php", "php", "bin/phpunit",
                "tests/SameInputReplicationRegressionTest.php",
                "tests/ReplicationSettlementTest.php",
                "tests/MeasurementApiTest.php",
                "tests/HomepageExamplesTest.php",
            ],
            repos["symfony"],
        ),
    ]
    passed = all(row["anchors_present"] for row in source_checks) and all(row["passed"] for row in executions)
    payload = {
        "kind": "dexagon.ainglish.evidence-harness-red-team.v2",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "repositories": {
            name: {"commit": git(path, "rev-parse", "HEAD"), "dirty": bool(git(path, "status", "--porcelain"))}
            for name, path in repos.items()
        },
        "threats": source_checks,
        "executions": executions,
        "passed": passed,
        "interpretation": (
            "All named false-positive paths retain an executable regression or mutation gate at these exact source bytes. "
            "This is a harness audit, not evidence for any language construct."
        ),
        "model_calls": 0,
        "model_downloads": 0,
        "governance_writes": 0,
    }
    sealed = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    payload["content_sha256"] = hashlib.sha256(sealed).hexdigest()
    TARGET.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"passed": passed, "threats": len(source_checks), "executions": len(executions), "sha256": payload["content_sha256"]}))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
