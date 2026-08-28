# Storage and worktree cleanup manifest — 2026-08-28

**Inventory complete; nothing was deleted or pruned.**

WSL reports **511.0 GiB free** (44.2% used); Windows C: reports **90.1 GiB free** (90.3% used). WSL has 64,159,014 free inodes, so file-count exhaustion is not the issue.

Across the project repositories, Git reports **337 worktrees**. **258** are conservative cleanup candidates because they were clean and their HEAD was reachable from the captured default remote; together they occupy **20.7 GiB**. Dirty, unmerged/unverified and primary worktrees are excluded.

Docker reports **19.5 GiB potentially reclaimable** across images, stopped containers and volumes, with 9 of 73 containers running. Volume removal requires per-project ownership review; this report does not recommend a global prune.

Ollama exposes 53 tags (51 distinct listed IDs). The service-owned model directory could not be traversed as this user, and tag sizes can double-count shared layers, so no false physical total is reported. **All models are explicitly preserved and no more downloads are planned.**

## Largest conservative worktree candidates

| Size | Path |
|---:|---|
| 2.0 GiB | `/home/dexagon/codex/dexagon/worktrees/symfony-sync-sdk-0.2.32` |
| 132.9 MiB | `/home/dexagon/codex/dexagon/worktrees/symfony-flagship-publication-20260826` |
| 125.3 MiB | `/home/dexagon/codex/dexagon/worktrees/symfony-adoption-automation-v2-20260825` |
| 123.2 MiB | `/home/dexagon/codex/dexagon/worktrees/symfony-stratified-settlement-20260827` |
| 122.8 MiB | `/home/dexagon/codex/dexagon/worktrees/press-history-20260828` |
| 122.6 MiB | `/home/dexagon/codex/dexagon/worktrees/review-symfony-0121946-20260824` |
| 121.8 MiB | `/home/dexagon/codex/dexagon/worktrees/server-abort-receipts-20260819` |
| 119.4 MiB | `/home/dexagon/codex/dexagon/worktrees/reader-adoption-transparency-20260828` |
| 118.9 MiB | `/home/dexagon/codex/dexagon/worktrees/ainglish-implementation-batch-20260821` |
| 118.4 MiB | `/home/dexagon/codex/dexagon/worktrees/moderation-basics-20260818` |
| 117.8 MiB | `/home/dexagon/codex/dexagon/worktrees/background-collision-honesty` |
| 117.4 MiB | `/home/dexagon/codex/dexagon/worktrees/evidence-explorer-20260827` |
| 116.0 MiB | `/home/dexagon/codex/dexagon/worktrees/symfony-deployment-provenance-20260824` |
| 115.8 MiB | `/home/dexagon/codex/dexagon/worktrees/stable-public-entry-urls` |
| 115.5 MiB | `/home/dexagon/codex/dexagon/worktrees/symfony-sync-sdk-0.2.40` |

## Safe next cleanup sequence

1. Refresh the relevant remote and repeat `git status --porcelain` plus reachability for each exact candidate path; also check that no open PR still uses its branch.
2. Remove selected worktrees through their owning repository with `git worktree remove <exact-path>`. Do not delete the directories directly and do not delete branches in the same operation.
3. For Docker, map each stopped container and volume to its Compose project. Use that project's `docker compose down` only after confirming its database is disposable; do not run a global volume prune.
4. The 553 MiB release-test virtualenv can be recreated; keep it while release-builder PR #3 is under review. The small live-pack download directory is immediately reproducible.
5. Preserve model stores, evidence carriers, dirty worktrees, primary checkouts, and every unmerged or reachability-unknown worktree.

## Claim boundary

Candidate means only clean and reachable from the locally captured default remote. Worktree and PR state can change; rerun status, reachability and open-PR checks immediately before any removal. Docker reclaimable figures are Docker's own estimates and do not authorize deletion of a volume.

Snapshot digest: `403e1650ec09cb509ef75a808c0ed6ed5f2902d2cc4bfd208c68ddf34de59981`. Report digest: `1d93333b5220cb399b2c10e802b6a3eb9b6fcf0d7c8f76ad70761d001e5cd023`.
