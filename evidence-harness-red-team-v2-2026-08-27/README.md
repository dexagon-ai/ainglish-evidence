# Evidence harness red-team v2

This audit attacks five ways an apparently clean result can become a false positive:

1. answer-bearing or target-specific calibration leakage;
2. same-input reruns mislabeled as independent replication;
3. incomplete careful-English comparators;
4. dead-cell or transport loss changing the surviving denominator; and
5. opposite form-level failures cancelling in one pooled scalar.

`audit.py` binds the exact SDK/server source files, requires named regression anchors, and executes
the relevant offline mutation suites plus server integration tests. A missing anchor or non-zero
test command fails the audit. The report is a receipt about harness behaviour at the recorded
commits; it is not evidence for any language construct.

The server suite needs its isolated test database to be running and migrated. Example:

```bash
python3 audit.py \
  --sdk-repo ../../worktrees/sdk-measurement-index-20260827 \
  --symfony-repo ../../worktrees/symfony-flagship-methodology-20260827
```

No model is called or downloaded.
