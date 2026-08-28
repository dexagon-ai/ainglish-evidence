# Post-merge live QA — 2026-08-28

**VERIFIED**: 51/51 checks passed against the public origin at `2026-08-28T11:16:40.361836+00:00`.

The health receipt identified deployed commit `dfb624a82052f27977ee88623980968eb8922524`. Git ancestry checks confirm that it contains the merge commits for Symfony PRs #323, #326 and #327.

- `/press` and `/history` return 200, expose the reviewed claim boundaries and correction-history wording, and are present in the sitemap.
- `/state` exposes all six usage-status categories in the mobile summary and accessible SVG label, including the distinction between missing readings and project machinery to which corpus adoption does not apply.
- The `/releases`, `/training` and `/paper` landing pages do not carry an artifact licence or immutable cache promise.
- Representative frozen core, training and paper files carry the correct scoped licence, one-year immutable cache contract and cross-origin access; JSON and JSONL media types were also checked.

## Claim boundary

This is a point-in-time public-origin smoke receipt. It demonstrates the observed HTTP and page contracts at the captured deployment commit; it is not a substitute for unit tests or continuous monitoring.

Snapshot digest: `1bdea4b13e5abf3494e731b3c25de0de448c376605175457315e9a5ace4bb44d`. Report digest: `49c7fd95e82b8bf6eaef759ef32d269d94d63d9bcff88e3179e518306398e70d`.
