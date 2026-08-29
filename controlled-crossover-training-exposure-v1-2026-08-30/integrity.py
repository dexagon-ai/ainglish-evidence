"""Shared content, public-freeze, and local-adapter integrity checks."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def pretty(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise RuntimeError(f"{path}:{number}: row is not an object")
        rows.append(row)
    return rows


def preregistered_paths() -> list[str]:
    return [line.split("  ", 1)[1] for line in (ROOT / "SHA256SUMS.preregistered").read_text(encoding="utf-8").splitlines() if line.strip()]


def verify_preregistered() -> str:
    failures = []
    for line in (ROOT / "SHA256SUMS.preregistered").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, relative = line.split("  ", 1)
        path = ROOT / relative
        if not path.is_file():
            failures.append(f"missing {relative}")
        elif sha256_file(path) != expected:
            failures.append(f"digest mismatch {relative}")
    audit = subprocess.run([sys.executable, str(ROOT / "audit.py")], cwd=REPO, capture_output=True, text=True)
    if audit.returncode:
        failures.append("input audit failed: " + (audit.stderr.strip() or audit.stdout.strip()))
    relative_root = ROOT.relative_to(REPO)
    paths = [str(relative_root / name) for name in preregistered_paths()] + [str(relative_root / "SHA256SUMS.preregistered")]
    if subprocess.run(["git", "diff", "--quiet", "--", *paths], cwd=REPO).returncode or subprocess.run(["git", "diff", "--cached", "--quiet", "--", *paths], cwd=REPO).returncode:
        failures.append("preregistered files have uncommitted changes")
    for path in paths:
        if subprocess.run(["git", "ls-files", "--error-unmatch", path], cwd=REPO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode:
            failures.append(f"preregistered file is not tracked: {path}")
    commit = subprocess.run(["git", "log", "-1", "--format=%H", "--", str(relative_root)], cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    if subprocess.run(["git", "fetch", "origin", "main", "--quiet"], cwd=REPO).returncode or not commit or subprocess.run(["git", "merge-base", "--is-ancestor", commit, "origin/main"], cwd=REPO).returncode:
        failures.append("preregistering commit is not public on origin/main")
    if failures:
        raise RuntimeError("; ".join(failures))
    return commit


def require_public_file(relative_name: str) -> str:
    path = ROOT / relative_name
    relative = path.relative_to(REPO)
    if not path.is_file() or subprocess.run(["git", "ls-files", "--error-unmatch", str(relative)], cwd=REPO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode:
        raise RuntimeError(f"{relative_name} is not a tracked file")
    if subprocess.run(["git", "diff", "--quiet", "--", str(relative)], cwd=REPO).returncode or subprocess.run(["git", "diff", "--cached", "--quiet", "--", str(relative)], cwd=REPO).returncode:
        raise RuntimeError(f"{relative_name} has uncommitted changes")
    commit = subprocess.run(["git", "log", "-1", "--format=%H", "--", str(relative)], cwd=REPO, check=True, capture_output=True, text=True).stdout.strip()
    subprocess.run(["git", "fetch", "origin", "main", "--quiet"], cwd=REPO, check=True)
    if not commit or subprocess.run(["git", "merge-base", "--is-ancestor", commit, "origin/main"], cwd=REPO).returncode:
        raise RuntimeError(f"{relative_name} commit is not public on origin/main")
    return commit


def artifact_files(directory: Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(p for p in directory.rglob("*") if p.is_file() and p.name != "artifact-manifest.json"):
        if path.is_symlink():
            raise RuntimeError(f"artifact file is a symlink: {path}")
        rows.append({"path": path.relative_to(directory).as_posix(), "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    return rows


def aggregate_files(rows: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for row in rows:
        digest.update(row["path"].encode() + b"\0" + str(row["bytes"]).encode() + b"\0" + row["sha256"].encode() + b"\n")
    return digest.hexdigest()


def validate_artifact(directory: Path, manifest: dict[str, Any]) -> None:
    if directory.resolve() != Path(manifest["directory"]).resolve() or not directory.is_dir():
        raise RuntimeError(f"artifact directory missing or moved: {directory}")
    current = artifact_files(directory)
    if current != manifest["files"] or aggregate_files(current) != manifest["aggregate_sha256"]:
        raise RuntimeError(f"artifact drift: {directory}")
    if sum(row["bytes"] for row in current) != manifest["total_bytes"]:
        raise RuntimeError(f"artifact byte count drift: {directory}")
