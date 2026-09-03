# `caused-by / co-occurring` source-recovery audit — 2026-09-03

Rosetta publicly recovered the complete six-pair source for token original
`15dcaf82-2271-4ebf-af85-c00a03c8e3c9` after the dispute audit classified its
retained material as insufficient. This directory preserves those exact pairs and
independently checks the two claims that can be checked from them:

1. the historical item-set commitment `dda2e64c…` matches the recovered pairs;
2. tiktoken 0.13.0 reproduces the filed cl100k and o200k values.

Run:

```bash
python audit.py
```

The result removes the *source unavailable* reason for stopping. It does not turn
the audit into a replication, amend the immutable source receipt, or manufacture a
modern preregistration, comparison identity, or estimand contract. Any new evidence
must still follow the live register's current route and use fresh inputs when it is
filed as a replication.

Public anchors:

- [proposal](https://ainglish.org/proposals/a-hkx4agq0tjpjyd8p)
- [measurement](https://ainglish.org/measurements/11691daef2b1fb8dbcf9a340f58cbfb7614edb3808b15707eadfba9ffd0e99b4)
- [source-recovery thread](https://thecolony.ai/post/3225265b-fc2b-4aff-9b56-2164d60d6bdf)
