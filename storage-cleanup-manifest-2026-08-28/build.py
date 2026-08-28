#!/usr/bin/env python3
"""Derive a conservative cleanup manifest from the storage snapshot."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def human(size: int | None) -> str:
    if size is None:
        return "unknown"
    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024 or unit == "TiB":
            return f"{value:.1f} {unit}"
        value /= 1024
    raise AssertionError("unreachable")


def size_bytes(value: str) -> int:
    match = re.fullmatch(r"([0-9.]+)([KMGT]?B)(?: .*)?", value)
    if not match:
        return 0
    scale = {"B": 1, "KB": 1000, "MB": 1000**2, "GB": 1000**3, "TB": 1000**4}
    return round(float(match.group(1)) * scale[match.group(2)])


def main() -> None:
    snapshot = json.loads((ROOT / "snapshot.json").read_text(encoding="utf-8"))
    worktrees = snapshot["worktrees"]
    candidates = sorted(
        (row for row in worktrees if row["classification"] == "cleanup_candidate_clean_and_reachable"),
        key=lambda row: row["size_bytes"] or 0,
        reverse=True,
    )
    docker_reclaimable = sum(
        size_bytes(row["Reclaimable"])
        for row in snapshot["docker"]["summary"]
    )
    root_fs, windows_fs = snapshot["filesystems"]
    classifications: dict[str, int] = {}
    for row in worktrees:
        classifications[row["classification"]] = classifications.get(row["classification"], 0) + 1

    report = {
        "kind": "dexagon.storage-cleanup-manifest.v1",
        "captured_at": snapshot["captured_at"],
        "source_snapshot_sha256": snapshot["content_sha256"],
        "capacity": {
            "wsl_free_bytes": root_fs["free_bytes"],
            "wsl_used_percent": root_fs["used_percent"],
            "windows_c_free_bytes": windows_fs["free_bytes"],
            "windows_c_used_percent": windows_fs["used_percent"],
            "wsl_inode_free": root_fs["inodes_free"],
        },
        "worktrees": {
            "total": len(worktrees),
            "classifications": classifications,
            "cleanup_candidate_count": len(candidates),
            "cleanup_candidate_bytes": sum(row["size_bytes"] or 0 for row in candidates),
            "candidates": [
                {
                    "path": row["path"],
                    "repository": row["repository"],
                    "head": row["head"],
                    "size_bytes": row["size_bytes"],
                    "reason": "clean and HEAD reachable from captured default remote",
                }
                for row in candidates
            ],
        },
        "docker": {
            "containers_total": len(snapshot["docker"]["containers"]),
            "containers_running": sum(row["state"] == "running" for row in snapshot["docker"]["containers"]),
            "reclaimable_reported_bytes": docker_reclaimable,
            "action": "review by Compose project; never issue a global volume prune from this manifest",
        },
        "temporary_paths": snapshot["temporary_paths"],
        "models": {
            "tag_count": snapshot["ollama"]["tag_count"],
            "unique_list_ids": snapshot["ollama"]["unique_list_ids"],
            "physical_storage": snapshot["ollama"]["physical_storage"],
            "action": "preserve all; do not download more until storage is expanded",
        },
        "mutations_performed": snapshot["mutations_performed"],
        "status": "inventory_complete_no_cleanup_performed",
        "claim_boundary": (
            "Candidate means only clean and reachable from the locally captured default remote. Worktree and PR state can change; "
            "rerun status, reachability and open-PR checks immediately before any removal. Docker reclaimable figures are Docker's "
            "own estimates and do not authorize deletion of a volume."
        ),
    }
    report["content_sha256"] = hashlib.sha256(canonical(report)).hexdigest()
    (ROOT / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    top = candidates[:15]
    lines = [
        "# Storage and worktree cleanup manifest — 2026-08-28",
        "",
        "**Inventory complete; nothing was deleted or pruned.**",
        "",
        f"WSL reports **{human(root_fs['free_bytes'])} free** ({root_fs['used_percent']:.1f}% used); Windows C: reports **{human(windows_fs['free_bytes'])} free** ({windows_fs['used_percent']:.1f}% used). WSL has {root_fs['inodes_free']:,} free inodes, so file-count exhaustion is not the issue.",
        "",
        f"Across the project repositories, Git reports **{len(worktrees)} worktrees**. **{len(candidates)}** are conservative cleanup candidates because they were clean and their HEAD was reachable from the captured default remote; together they occupy **{human(report['worktrees']['cleanup_candidate_bytes'])}**. Dirty, unmerged/unverified and primary worktrees are excluded.",
        "",
        f"Docker reports **{human(docker_reclaimable)} potentially reclaimable** across images, stopped containers and volumes, with {report['docker']['containers_running']} of {report['docker']['containers_total']} containers running. Volume removal requires per-project ownership review; this report does not recommend a global prune.",
        "",
        f"Ollama exposes {report['models']['tag_count']} tags ({report['models']['unique_list_ids']} distinct listed IDs). The service-owned model directory could not be traversed as this user, and tag sizes can double-count shared layers, so no false physical total is reported. **All models are explicitly preserved and no more downloads are planned.**",
        "",
        "## Largest conservative worktree candidates",
        "",
        "| Size | Path |",
        "|---:|---|",
    ]
    lines.extend(f"| {human(row['size_bytes'])} | `{row['path']}` |" for row in top)
    lines.extend([
        "",
        "## Safe next cleanup sequence",
        "",
        "1. Refresh the relevant remote and repeat `git status --porcelain` plus reachability for each exact candidate path; also check that no open PR still uses its branch.",
        "2. Remove selected worktrees through their owning repository with `git worktree remove <exact-path>`. Do not delete the directories directly and do not delete branches in the same operation.",
        "3. For Docker, map each stopped container and volume to its Compose project. Use that project's `docker compose down` only after confirming its database is disposable; do not run a global volume prune.",
        "4. The 553 MiB release-test virtualenv can be recreated; keep it while release-builder PR #3 is under review. The small live-pack download directory is immediately reproducible.",
        "5. Preserve model stores, evidence carriers, dirty worktrees, primary checkouts, and every unmerged or reachability-unknown worktree.",
        "",
        "## Claim boundary",
        "",
        report["claim_boundary"],
        "",
        f"Snapshot digest: `{snapshot['content_sha256']}`. Report digest: `{report['content_sha256']}`.",
    ])
    (ROOT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "worktrees": len(worktrees),
        "cleanup_candidates": len(candidates),
        "candidate_bytes": report["worktrees"]["cleanup_candidate_bytes"],
        "docker_reclaimable_reported_bytes": docker_reclaimable,
        "content_sha256": report["content_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
