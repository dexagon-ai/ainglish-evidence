#!/usr/bin/env python3
"""Capture storage pressure and classify worktrees without removing anything."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess


ROOT = Path(__file__).resolve().parent
REPOSITORIES = [
    Path("/home/dexagon/codex/dexagon/ainglish"),
    Path("/home/dexagon/codex/dexagon/ainglish-evidence"),
    Path("/home/dexagon/codex/dexagon/ainglish-moderation"),
    Path("/home/dexagon/codex/dexagon/ainglish-python-audit"),
    Path("/home/dexagon/codex/dexagon/ainglish-releases"),
    Path("/home/dexagon/codex/dexagon/ainglish-symfony"),
    Path("/home/dexagon/plugins/ainglish-claude-plugin"),
    Path("/home/dexagon/plugins/ainglish-openai-plugin"),
]
MAJOR_DIRECTORIES = [
    Path("/home/dexagon/codex/dexagon/worktrees"),
    Path("/home/dexagon/codex/dexagon/ainglish-symfony/worktrees"),
    Path("/home/dexagon/plugins/worktrees"),
    Path("/home/dexagon/.cache/huggingface"),
    Path("/home/dexagon/.cache/pip"),
    Path("/usr/share/ollama/.ollama/models"),
]
TEMPORARY_PATHS = {
    "/tmp/ainglish-releases-test-venv-20260828": "keep_until_release_builder_pr_3_is_reviewed_or_recreate_if_removed",
    "/tmp/tmp.mp6T1Eo63n": "rebuildable_live_pack_downloads_cleanup_candidate",
}


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def run(args: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, check=check, capture_output=True, text=True)


def du(path: Path) -> dict:
    try:
        exists = path.exists()
    except OSError as error:
        return {"path": str(path), "exists": None, "bytes": None, "error": str(error)}
    if not exists:
        return {"path": str(path), "exists": False, "bytes": 0, "error": None}
    result = run(["du", "-sx", "--block-size=1", str(path)], check=False)
    if result.returncode != 0:
        return {
            "path": str(path),
            "exists": True,
            "bytes": None,
            "error": (result.stderr or result.stdout).strip(),
        }
    return {
        "path": str(path),
        "exists": True,
        "bytes": int(result.stdout.split()[0]),
        "error": None,
    }


def filesystem(path: Path) -> dict:
    usage = shutil.disk_usage(path)
    stats = path.stat().st_dev
    vfs = __import__("os").statvfs(path)
    return {
        "path": str(path),
        "device_id": stats,
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
        "used_percent": round(usage.used / usage.total * 100, 3),
        "inodes_total": vfs.f_files,
        "inodes_free": vfs.f_ffree,
    }


def parse_worktree_porcelain(text: str) -> list[dict]:
    records: list[dict] = []
    current: dict = {}
    for line in text.splitlines() + [""]:
        if line == "":
            if current:
                records.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        if key in {"detached", "bare", "locked"}:
            current[key] = True if not value else value
        elif key == "prunable":
            current[key] = value or True
        else:
            current[key] = value
    return records


def default_remote(repo: Path) -> str | None:
    symbolic = run(
        ["git", "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"],
        cwd=repo,
        check=False,
    )
    if symbolic.returncode == 0:
        return symbolic.stdout.strip()
    for candidate in ("origin/master", "origin/main"):
        exists = run(["git", "rev-parse", "--verify", candidate], cwd=repo, check=False)
        if exists.returncode == 0:
            return candidate
    return None


def worktrees(repo: Path) -> list[dict]:
    default = default_remote(repo)
    raw = run(["git", "worktree", "list", "--porcelain"], cwd=repo).stdout
    entries = []
    for record in parse_worktree_porcelain(raw):
        path = Path(record["worktree"])
        primary = path.resolve() == repo.resolve()
        exists = path.exists()
        status = run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=path,
            check=False,
        ) if exists else None
        dirty_count = len(status.stdout.splitlines()) if status and status.returncode == 0 else None
        reachable = None
        if default and exists:
            reachable = run(
                ["git", "merge-base", "--is-ancestor", record["HEAD"], default],
                cwd=repo,
                check=False,
            ).returncode == 0
        if primary:
            classification = "keep_primary_checkout"
        elif not exists or record.get("prunable"):
            classification = "review_stale_registration"
        elif dirty_count is None or dirty_count > 0:
            classification = "keep_dirty_review_required"
        elif reachable is not True:
            classification = "keep_unmerged_or_unverified"
        else:
            classification = "cleanup_candidate_clean_and_reachable"
        size = du(path) if exists else {"path": str(path), "exists": False, "bytes": 0, "error": None}
        entries.append({
            "repository": str(repo),
            "default_remote": default,
            "path": str(path),
            "head": record["HEAD"],
            "branch": record.get("branch"),
            "detached": bool(record.get("detached")),
            "primary": primary,
            "exists": exists,
            "prunable": record.get("prunable", False),
            "dirty_entry_count": dirty_count,
            "head_reachable_from_default_remote": reachable,
            "size_bytes": size["bytes"],
            "size_error": size["error"],
            "classification": classification,
        })
    return entries


def docker_inventory() -> dict:
    summary = []
    result = run(["docker", "system", "df", "--format", "{{json .}}"], check=False)
    if result.returncode == 0:
        summary = [json.loads(line) for line in result.stdout.splitlines() if line]
    containers = []
    result = run(["docker", "ps", "-a", "--format", "{{json .}}"], check=False)
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            row = json.loads(line)
            containers.append({
                "id": row.get("ID"),
                "name": row.get("Names"),
                "image": row.get("Image"),
                "state": row.get("State"),
                "status": row.get("Status"),
            })
    return {
        "available": bool(summary or containers),
        "summary": summary,
        "containers": containers,
        "mutation_performed": False,
    }


def ollama_inventory() -> dict:
    result = run(["ollama", "list"], check=False)
    models = []
    if result.returncode == 0:
        for line in result.stdout.splitlines()[1:]:
            parts = re.split(r"\s{2,}", line.strip())
            if len(parts) >= 4:
                models.append({
                    "name": parts[0],
                    "id": parts[1],
                    "display_size": parts[2],
                    "modified": parts[3],
                })
    physical = du(Path("/usr/share/ollama/.ollama/models"))
    return {
        "available": result.returncode == 0,
        "tag_count": len(models),
        "unique_list_ids": len({model["id"] for model in models}),
        "models": models,
        "physical_storage": physical,
        "policy": "preserve_all_no_new_downloads",
        "mutation_performed": False,
        "size_note": "ollama list sizes are logical per tag and can double-count shared layers; physical storage is unknown when the service-owned directory denies traversal",
    }


def main() -> None:
    target = ROOT / "snapshot.json"
    if target.exists():
        raise SystemExit("REFUSING: snapshot.json already exists")

    all_worktrees = []
    for repo in REPOSITORIES:
        if (repo / ".git").exists():
            all_worktrees.extend(worktrees(repo))

    snapshot = {
        "kind": "dexagon.storage-cleanup-manifest-snapshot.v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "filesystems": [filesystem(Path("/")), filesystem(Path("/mnt/c"))],
        "major_directories": [du(path) for path in MAJOR_DIRECTORIES],
        "temporary_paths": [
            {**du(Path(path)), "classification": classification}
            for path, classification in TEMPORARY_PATHS.items()
        ],
        "worktrees": all_worktrees,
        "docker": docker_inventory(),
        "ollama": ollama_inventory(),
        "mutations_performed": [],
        "safety_policy": {
            "models": "preserve",
            "dirty_worktrees": "preserve",
            "unmerged_or_unverified_worktrees": "preserve",
            "primary_checkouts": "preserve",
            "docker_volumes": "do_not_prune_without_project_ownership_review",
            "cleanup_candidates": "revalidate_immediately_before_any_future_removal",
        },
    }
    snapshot["content_sha256"] = hashlib.sha256(canonical(snapshot)).hexdigest()
    target.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "captured_at": snapshot["captured_at"],
        "worktrees": len(all_worktrees),
        "content_sha256": snapshot["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
