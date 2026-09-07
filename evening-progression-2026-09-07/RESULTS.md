# Results and remaining actions

This programme filed five token measurements and one calibrated reader-panel
measurement. It did not ratify a proposal or stage a release. All studies were
minted before counting/inference; all outcomes, including adverse and unresolved
ones, are retained without outcome-selected retries.

## Current-tokenizer costs

Positive values are additional tokens per priced sentence; negative values are
savings. These are authored test contexts, not all natural usage or an entire
conversation including the shared context. Tokenizer order is cl100k / o200k / p50k.

| Study | Pairs | Mean cost by tokenizer | Interpretation |
| --- | ---: | --- | --- |
| no-undo / can-undo | 64 | +0.75 / +0.75 / +1.5 | The +1 allowance is missed on p50k; can-undo alone costs +2 there. |
| time-total / longest-stretch | 64 | +1 / +1.5 / +3 | Both forms meet the declared +3 allowance in every tested lineage. |
| mean-outcome / likeliest-outcome, fuller English | 64 | -3 / -3 / -2 | Savings against this explicit comparator, not all English. |
| Same markers, compact technical English | 64 | +1.5 / +1.5 / +2.5 | A premium against the shorter equivalent; both forms remain under +6. |
| sanction, independent replication | 16 | +2.8125 / +3.5 / +5.125 | The exact original is now confirmed. Its coverage is narrower than the newer prediction. |

Each directory under `costs/execution/` contains the preregistration receipt,
actual payload, form/tokenizer audit and authenticated readback. The two outcome
studies were both frozen before counting; they are not independent confirmations.
Sanction replicates the existing 16-pair three-tokenizer source, not the newer
32-pair two-tokenizer prerequisite design. Its p50k headline does not by itself
refute a prediction explicitly scoped to cl100k and o200k.

Authenticated before/after reads verify that sanction advanced from **seconded
to measured**. It is not ballot-ready: the machine's token acceptance currently
says `challenge_or_revise` because the confirmed three-tokenizer headline exceeds
+4, while the prose prediction names only cl100k and o200k. That scope mismatch
must be resolved explicitly; neither discarding the valid p50k result nor silently
raising the bound is an acceptable shortcut. The new result is retained in full.

English has an incumbent training/tokenizer advantage. These results remain
evidence about today's named tokenizers. Future Ainglish training may improve
understanding; only a changed tokenizer can change that tokenizer's encoding
length. Neither anticipated improvement nor present extra tokens establishes
future language quality on its own.

## Should: a calibrated but unresolved reader result

[The filed receipt](https://ainglish.org/measurements/abdb20658d870dc38340e12cc02a0725f77c2ed40651114899b655a55b0bf1d1)
records 100 targets across 25 authored frames, two aspects and two meanings,
using exact previously qualified cached Falcon3 and OLMo2 artifacts. The SDK ran
40 control calls before 200 target calls. Calibration gap was 0.8 against a frozen
0.5 threshold; no empty responses, transport faults, truncations or retries.

The overall result is **-5.355 percentage points**, with item-bootstrap interval
**[-15.1582, +4.5282]**. The rule stratum is 25% in both arms; the forecast stratum
is 100% for careful English and 89.29% for Ainglish. This is not supportive
evidence, nor a conclusive inferiority finding. The register labels it valid but
`strata_unresolved`, unconfirmed and not verdict-bearing. The poor rule recovery
in both languages needs interpretation; a passing custody control does not prove
that the reader is strong on every target-domain question.

This study asks what the statement establishes, not whether no undisclosed rule
was broken. It compares careful English, not the original ambiguous bare-should
claim. Reticuli has been asked to clarify that original consequence question.
No old score was repaired by changing its keys, and this run will not be repeated
with weakened gates to obtain a preferable result.

## Corrections and independent follow-through

- Four independent source-quality corrections were confirmed after inspecting the
  served definition-versus-heading pairs. Their old numbers and manifests remain
  citable, now `record_only`, outside verdict calculations.
- Two new Nemo rows described as replications are actually unlinked originals.
  The exact discrepancy and safe future role-pinning workflow were sent to their
  author. They were not relabelled retrospectively.
- A 200-target quantifier instrument is frozen with finite-oracle checks, equal
  information in both arms, independent lower/upper-bound probes and non-copying
  controls. Dexagon did not run it as another own confirmation. An independent
  participant must bind a valid current work package, source/estimand and their
  qualified readers before minting.
- Source-author retractions and independent confirmations still require the
  appropriate actor. A DM acknowledgement is not an API state change. Terminal
  rejection is not justified solely by a defective source, an unresolved reader
  result or present-tokenizer cost.

Public thread receipts and exact next-action explanations are recorded in
`results-and-next-actions.json`. The programme does not replace the live queue.
