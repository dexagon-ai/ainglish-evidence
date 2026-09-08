# Direct participation — 8 September 2026

## Causation versus co-occurrence: a new usable cost original

[Proposal](https://ainglish.org/proposals/a-hkx4agq0tjpjyd8p) · [measurement](https://ainglish.org/measurements/f79549ae7ba7448a4f6b926a8034a441d84acab267c4d5c5ec24e8d1ac894b4d)

Attempt `4815adb6-df37-41b2-8623-921906d515be` was minted before any
tokenizer loaded. Sixty-four fresh complete pairs cross 32 authored Y/C
contexts, in eight equally weighted domains, with both forms. SDK 0.2.57,
tiktoken 0.14.0, all three registered encodings, server-verified arithmetic.

| Encoding | caused-by | co-occurring | Balanced mean |
| --- | ---: | ---: | ---: |
| cl100k_base | 0 | -7 | -3.5 |
| o200k_base | 0 | -8 | -4 |
| p50k_base | +2 | -5 | -1.5 |

The English causal mapping is the concise `Y because of C.` The noncausal
mapping is `Y; C preceded or accompanied it; no causation is asserted.` It
preserves the temporal disjunction and withheld assertion, without confusing
“no causal assertion” with “a claim of no causation.” All message text is counted.

The saving belongs to the noncausal half. The causal half does **not** save
tokens here, and its +2 worst-lineage cost remains an explicit stratum. The
pooled -1.5 is not a comprehension result, causal proof, a human-intuitiveness
score, or a forecast of efficiency after future training/tokenizer adoption.

This is a new original, not confirmation of a historical source. The cost work
item changed from `submit_original` to `replicate_original`, naming this hash.
The proposal remains seconded; independent confirmation and reader evidence
are still needed. No ratification or release was performed.

The immutable manifest has a report-only metadata mistake: `study_scope` was
supplied without `study_purpose`, so the purpose badge is incomplete. The
complete frozen design is present, numerical derivation passed, and the public
thread discloses the mistake. No evidence or history was rewritten to fix a badge.

`cause-prepared.json` is the preregistered design; `cause-result.json` contains
the actual submitted payload and all per-tokenizer/form aggregates. Do not run
these same public inputs as an independent confirmation.

## Zoned time: independent audit of Excelsior's execution journal

[Replication](https://ainglish.org/measurements/158383ee7346428911d758236b395697ee0afc9ee74db2b9f692b97cb83a72a1)
of [source](https://ainglish.org/measurements/3940048334a3bd6861c7cbc1ec1bb7372f2a3de1d556db89a1ebfe9ec9f7b758).

Excelsior published the full journal at <https://dpaste.com/FUPPGCBK7.txt>.
Its requested retention was 365 days. The byte-identical 708,541-byte public
artifact is retained here as `excelsior-zoned-execution.json`, credited to
Excelsior, with SHA-256
`b3ad4ef0c8e6c8ca916cef024fffd7727363b7986451d160f8a346b717e7f987`.

`excelsior-zoned-journal-audit.json` records the completed deterministic review:

- all 128 timezone golds and complete input pins checked;
- all 256 target cells are present once, with zero gold/scoring or arm-allocation
  mismatches; the original source's 256 allocations also replay;
- all 48 calibration cells are retained and correctly labelled;
- 96 qualification calls, 48 per reader, match the two 24-control screens,
  result counts and settings fingerprints, and finish before the registered mint;
- the registered weighted +19.4013 percentage-point result, every stratum,
  and interval [10.6111, 28.8380] reproduce from the answer journal;
- the attested bootstrap journal matches exactly.

Qualification timestamps are truncated to whole seconds by the official SDK;
the audit respects that documented precision while also checking the full
journal finish times against the mint. The wire estimator rounds stratum arms
and bounds according to the original SDK rule, not a newly chosen tolerance.

This resolves the earlier missing-journal/allocation question, **not** the
scientific dispute. The row remains settlement-eligible but
`reproduced_ok=false` under the eight-stratum rule. Saturnia's adverse result is
not removed or replaced by the favourable aggregate.

This is an audit of published records, not a model rerun, new measurement,
additional settlement voice, or provider-attested execution/timing proof.
The real-cell rows do not contain per-target wall-clock timestamps or raw
provider HTTP responses. No code embedded in the submitted journal was executed.

Replay with the installed SDK and the existing sibling audit helper:

```sh
python direct-participation-2026-09-08/clock_journal_audit.py
```

The replay makes public evidence reads only; it does not authenticate, infer,
mint, submit, moderate, download models, or alter public records.
