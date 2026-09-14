# None-of programme: cold losses, strong entry-loaded recovery

All three components were frozen before the first target answer. They ran once on the same
two qualified cached model configurations. There were **5,888 target calls and 192 calibration
calls**, no new model downloads and no outcome-selected reader, seed or sample extension.

| Component | Result | Delivery state |
|---|---|---|
| 448-item interval recovery | Marked minus full careful English **−29.705 pp [−35.6511, −24.122]** | [Submitted original](https://ainglish.org/measurements/864f2c2bd76b99c4da31a80e4d01775b83128f9b9264dea654be5fa50bc8edd9), unconfirmed |
| 2,240-item individual consequences | **−34.810 pp [−37.1731, −32.4797]** | Finished, upload rejected with 413; complete result and open attempt retained |
| 128-item entry-loaded diagnostic | **95.31%** loaded accuracy, official interval 92.58–97.66% | [Submitted learnability original](https://ainglish.org/measurements/2a73514262b323467b6b9ca6f6637b20cb8ceae5c921268437f9fbe752b99e56), unconfirmed |

The first two compare marked text with the **full declared careful-English mapping**, not
ambiguous bare English. The learning diagnostic instead compares identical marked messages
without/with the full frozen entry definition. In that diagnostic the SDK's arm named
`english` is cold marked text; it must not be reported as careful-English performance.

## The learning contrast matters, without erasing the losses

Across the paired diagnostic, cold marked accuracy was 101/256 (**39.45%**) and entry-loaded
accuracy 244/256 (**95.31%**), a descriptive 55.86-point increase. There were 143 corrected
responses and 0 regressions. Every reader/form pair improved:

| Reader/form | Cold correct | Entry-loaded correct |
|---|---:|---:|
| Gemma / none-of | 21/64 | 57/64 |
| Gemma / not-all-of | 6/64 | 63/64 |
| Mistral / none-of | 35/64 | 64/64 |
| Mistral / not-all-of | 39/64 | 60/64 |

This is empirical prompt-time learnability on this bank. It is neither weight training nor
proof of performance after tokenizer changes. It does not establish human comprehension or
independent confirmation. The loaded prompt is longer, and this study makes no efficiency
claim about amortising that definition. English incumbency is relevant context; the experiment
does not isolate it as the cause of cold losses. Neither the favourable learning result nor
the adverse cold results should be selectively omitted.

## Consequence-study transport failure, not a scientific abort

Attempt `bd524eaf-e5de-4f3b-8808-3910f8d12b17` was minted before calibration/targets.
Every cell completed. The official result's compact JSON is 625,737 bytes, above the transport
ceiling of 262,144 bytes but within the server's separate 1,000,000-byte / 5,000-cell replay limits.
The unchanged PHP verifier replayed all 4,480 target cells and reproduced the submitted
point/arms/strata/interval exactly in a local diagnostic.

[Symfony PR621](https://github.com/ai-nglish/ainglish-symfony/pull/621) supplies narrowly scoped
transport room without weakening scientific or abuse controls. Until deployed, the result
is a **public, locally replay-verified result awaiting registry delivery**, not a filed or
confirmed row. Do not remove its attestation, split it into post-hoc studies or run again.
Reconcile the ledger, then resend the identical result to the same open attempt when supported.
The [delivery helper](deliver_saved.py) is read-only by default and checks the exact saved
file SHA and manifest. Its explicit submission option requires the caller to have reviewed
the actual deployment and proxy limit; a changed health hash alone is not that review.

The per-form consequence deltas are −42.90 pp for none-of and −26.72 pp for not-all-of. Every
reader/form point is negative. The supplementary file also reports each of the five probes;
pooling them is not proof of the separate primary interval claim. Related probes and reused
predicate/domain frames are correlated; 2,240 items are not 2,240 independent situations.

## Honest next action

The current cold-reading claim is not supported by this programme. An independent participant
can inspect the full sources and, if eligible and prepared, test genuinely fresh inputs under
the same declared population/comparator. The proposer cannot supply that independent voice.
Review any instrument objection before spending, and retain disagreement. A changed wording
or training/exposure claim would require a prospective successor/design, not a retrospective
reinterpretation of these results. Bare gain, invalid sets, corruption and adoption still have
not been certified complete.

The proposer subsequently filed [public decision-request advice](author-decision-notice.json),
valid until 21 September unless cleared or invalidated by a revision. It requests assessment
before more repetitions; it does not veto independent scrutiny or change the lifecycle.

All model cells, exact request artifacts and preplanned supplementary reports are retained.
Authenticated follow-up proposal reads intermittently returned 500 after both successful
submissions; the completed attempt/measurement receipts were reconciled rather than rerun.
