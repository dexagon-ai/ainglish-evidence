# `measure.py --selftest` transform recertification

This packet re-certifies the ratified claim that every transform in the executable pairwise
registry has a transform-specific known-answer anchor: replacing one registry member with the
identity function must make `selftest()` fail and name that member.

The rerun targets the currently served reference harness, Ainglish SDK `0.2.43`. The local
`measure.py` bytes and `https://ainglish.org/measure.py` both have SHA-256
`8790aef7b7fa282249fe9503b59468b2b8929f35e8e1243718191a2b4b9c152f`.

Nine new known-answer pairs are frozen here. They are different from the nine embedded examples
named in the public harness. Each pair must first produce a finding naming its intended transform.
The runner then replaces only that registry member with identity in a fresh process. The fresh
finding must disappear, and the harness selftest must fail with an assertion naming that same
transform. Untouched runs before and after the mutation table must pass.

`run_once.py` performs only read-only preflight until it has minted an attempt. It then executes
the 11-run table once and files every admissible result, including a positive (adverse)
`unclaimed_verdict_flips` count. A failed baseline, source mismatch, timeout, or incomplete table
aborts the attempt with a retained public receipt rather than manufacturing a verdict.

This is a current-version deterministic recertification. It does not claim language
comprehension, token efficiency, or independent operator-level confirmation.

Run the no-measurement preflight after this packet is committed and pushed:

```bash
PYTHONPATH=/home/dexagon/codex/dexagon/worktrees/sdk-remote-inference-readers-20260829/src:/home/dexagon/codex/dexagon/scripts \
  /home/dexagon/codex/dexagon/.venv/bin/python \
  selftest-transform-recertification-v2-2026-08-29/run_once.py --preflight
```

Omit `--preflight` exactly once to mint, execute, and file.
