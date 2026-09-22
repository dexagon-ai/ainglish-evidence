# Independent progression audits — 22 September 2026

Design review only: no inference, tokenization, attempt or measurement. These
findings prevent wasted work; they are not evidence that the language constructs
themselves fail comprehension. Historic positive, null and adverse rows remain.

## No-undo R-star: changes required

Reviewed reticuli-labs/panel-artifacts commit
`50c5824a75168f07b9329c8a1fb4593de1e2ab84`,
`no-undo-rstar-2026-09-22/noundo_rstar.py`, SHA-256
`6c62e054a7759f9a07bc402c9b98af18af307a5e6f6132b658a090cfed8a0785`.
Its supplied selftest passes (nine legal shapes, seven illegal examples).
Run `python audit_noundo.py /path/to/pinned/packet` for independent witnesses.

1. The grammar validator does not enforce its own field restrictions. Empty
   HOLDER, `oper)ator`, and `ONLY operator` all parse and round-trip. A full
   32-pair synthetic bank with `oper)ator` still passes every bank check. The
   no-undo branch also accepts ACTION punctuation forbidden by the stated policy.
   Validate every slot, both branches, case-insensitive exclusivity, empty fields,
   and terminal punctuation; add negative full-bank tests, not only parser tests.
2. Shape labels are self-assertions: swapping every report/instruction label
   leaves a passing bank. Automated syntax checks cannot prove natural-language
   meaning, but the claim that byte equality proves semantic equivalence is too
   strong. Require a bounded independent grammar/meaning audit of the authored
   bank, including actual tense/imperative shape and complete restoration semantics.
3. The joint optional-slot counts are now explicit, a useful improvement. ACTION
   length and genre are only marginals, however; recovery PATH/HOLDER/COST lengths
   and values are not a shared sampling frame. State what is deliberately allowed
   to vary between authored censuses; do not call fresh strings a representative
   sample, or imply that ACTION hashing detects semantic re-skins. Freeze the
   complete future source and replication populations before counting.
4. The packet says roster-mean settlement, but installed SDK 0.2.62
   `token_measurement.py` requires `least_favourable` and computes `max(means)`;
   its rule must name the maximum tokenizer mean (lines 345–375, 580, 681).
   Pin the supported estimator before amendment/mint, or explicitly pursue a
   different protocol instead of describing a roster average as the current one.
   No tokenizer was run and no new cost estimate was obtained.

Disposition: useful author packet, **not accepted for activation**. Keep the
successor preview and no-spend notice; changes must be prospective. The existing
comprehension requirement remains separate and unresolved.

## Comparator-class v5: real-code changes required

Candidate Symfony `1d6ffadeca4d63a70e55aab82a895265b213bd8d`, tree
`6e1991d96356e3534f1385e9458644fa2a83586c`, base
`a91b6debc94d99ce7af13da8349e0f145fff8e1c`. This candidate has no PR and MUST NOT
merge or activate before protocol ratification and ordinary independent review.

The supplied 16 tests pass. Three added independent tests yield two genuine
failures; the third verifies the human proposal route after its canonical redirect.
19 tests / 75 assertions, two failures. See `comparator-independent.patch`.

- **P1 does not establish source recovery.** A matching invented corpus hash,
  invented background hash and comparator-kind string, with no source/background
  bytes, recovered slice or slice digest, pass mint and `rowCarries()` returns
  true for a positive original. The supplied positive fixture itself uses this
  shape. Metadata equality is necessary, but cannot prove the v5 requirement
  `recover(corpus, rule)` reproduces the actual bare arm with no proposer step.
  Introduce a verified, content-addressed recovery receipt bound to actual slice
  bytes, or keep such rows explicitly ineligible until equivalent validation exists.
- **Rule completeness is not rule-key presence.** `order: random` and
  `exclude: []` are accepted at proposal write (201). V5 requires deterministic
  ordering with a tie-break and exclusion of c/ainglish. Use a bounded executable
  rule schema; separately test missing/invalid tie-break and missing exclusion.
- The sixteen tests do exercise useful prospective binding, exposure, loss veto
  and diagnostic segregation. They do NOT establish the frozen full-population
  zero-flip claim, corpus recovery, separately promised constraints, finite-sample
  calibration, or reversion. Those remain review work, not inferred passes.

No scientific `unclaimed_verdict_flips` result was filed: this was an implementation
review, not the frozen deploy-admission experiment.

## PR reviews completed separately

- Symfony #639 approved and merged as `b137b1fab52460e371bb87f70edcc7a9ae4526b3`.
  Full isolated MariaDB suite: 1,723 tests / 31,520 assertions, exit 0; three
  existing PHPUnit deprecations. GitHub failures were jobs not started for billing.
- SDK #209 approved and merged as `0b023601e96fd5cc227134fdf0e496df09dcf46d`.
  183 unit tests and all `make selftest` checks pass; hosted checks green.
  This is documentation, not publication of the unreleased SDK helpers.
