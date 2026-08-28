# Language release 3 readiness

Snapshot: `2026-08-28T11:09:41.732804+00:00`. Decision: **the current release is complete; release 3 is not yet warranted**.

The live register has **35** ratified rows: **19 language** and **16 protocol**. All 19 language rows are already present, unchanged, in `ainglish-core-v0.35.0`. The live register version and digest exactly match that bundle's cut-off. There are therefore **0 new, 0 changed, and 0 removed language entries** for release 3.

| Check | Current result |
|---|---|
| Latest language bundle | `ainglish-core-v0.35.0` · 19 entries |
| Exact live-head binding | yes · `ee8978f9ab5adb252aa244dc1a0dbb5abaa81f499758ec18c95caf5dcfa863b8` |
| Unreleased language entries | 0 |
| Routine 5–10 entry cadence | not met |
| One-month-with-pending-language cadence | not met · bundle age 3.1 days |
| Release-3 training builder | [PR #3](https://github.com/ai-nglish/ainglish-releases/pull/3) · open · review pending |
| Exact-byte corporate greenlight | not requested; no candidate release-3 bytes exist |

## What happens next

Continue advancing high-quality language proposals to ratification. Recompute this report after every language ratification, deprecation, restoration, or correction. Consider a cut when roughly 5–10 unreleased language entries accumulate, a coherent flagship group becomes a real milestone, or a month passes while eligible language changes remain pending. Protocol-only changes do not count.

The tooling PR can merge now because it removes a known release-3 build blocker, but merging it is preparation—not a reason to publish an empty release.

## Claim boundary

This is a deterministic population and cadence report, not release approval. Any future bundle still requires rights verification, exact-byte inspection, and the explicit greenlight recorded by policy.

Snapshot digest: `81b3fe90268d6d658335d89ff5025e205400f5b314272f2493f19413a90029eb`. Report digest: `6b56d0ec29f6b2f070ccc25ca3624e3c589a0dfed60c357fac71ff5ee05f5f05`.
