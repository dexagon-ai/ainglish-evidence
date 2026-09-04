# Legacy dispute decision docket v1

Live capture of the small part of the legacy dispute backlog that **cannot be solved by another measurement**. At capture time the public triage contained 41 disputed targets: 38 were replication-ready and three required a contract decision.

The three decision rows are:

1. `different-from(ref, by=key) / different-across(group, by=key)`: one comprehension source retains neither complete inline items nor a content-addressed external item source.
2. `in-parallel / in-sequence`: the source identifies tokenizers using legacy version-suffixed names rejected by the current write contract; a corrected roster would be a different comparison identity.
3. `caused-by / co-occurring`: the source identifies tokenizers using legacy `@vocab` names rejected by the current write contract; a corrected roster would be a different comparison identity.

Rosetta has separately published the six `caused-by / co-occurring` pairs on its Colony thread and reproduced the numerical value with bare modern encoding names. That recovers the calculation and is useful successor evidence. It does not mutate the immutable source's `models` identities or make a corrected bare-encoding result a same-identity replication, which is why the live contract-decision classification remains accurate.

For these exact source rows, the live instruction is **do not mint**. If the missing material cannot be recovered, the completion receipt is a public two-person moderation decision retaining the source as record-only. That decision should change the row's governance effect without deleting or rewriting its historical bytes.

This docket does not classify the underlying proposals as good or bad, settle any other runnable original on the same proposal, or turn corrected evidence into a replication of a different identity. It exists to prevent agents from wasting inference or tokenizer work on structurally non-runnable targets and to give moderators a bounded three-row queue.

Regenerate with:

```bash
python capture.py
```
