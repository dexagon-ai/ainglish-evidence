# Scoring and claim contract

## Unit and primary comparison

The task item is the semantic unit. A model response is a repeated observation from a reader, not an
independent research participant merely because it appears on another row.

For each reader and track, compute the paired item-level difference between:

1. Ainglish zero-repair task success; and
2. careful-English zero-repair task success.

That is the primary comparison. Bare English is a secondary ambiguity baseline. The benchmark does
not define a single composite score and does not let token savings compensate for a wrong action.

Report at least these quantities separately for every arm:

- zero-repair task success;
- final task success after at most one scripted clarification;
- clarification rate;
- wrong-action rate before repair;
- invalid-output rate;
- total input plus output tokens, with coverage and tokenizer/provider named; and
- end-to-end latency, with coverage and hosting arrangement named.

An `act` response succeeds only when its normalized set of action IDs exactly matches one listed
`valid_action_sets` entry. A strict subset, superset or alternative action is wrong. A first-turn
`clarify` response is not success and not wrong action; it consumes a repair turn. Its repair response
must be `act` and exact-match a valid set to count as final success.

## Tracks are different estimands

`cold` estimates immediate compatibility with no definition in the served prompt. It does not prove
absence from training data. Report training exposure as unknown unless a receipt establishes it.

`one_exposure` estimates use after one short task-relevant definition. Its reference-card tokens are
part of input cost. It does not estimate a model trained or tokenized for Ainglish.

Never pool the tracks. Never describe a one-exposure result as zero-shot, cold or pretrained adoption.

## Comparators

Careful English is the load-bearing comparator because it expresses the same source intent without a
project-specific marker. Ainglish beating ambiguous bare English while failing to match careful English
shows ambiguity repair, not a benefit over explicit English.

The bare arm intentionally under-specifies the tested distinction. Its source intent is fixed outside
the message so that a lucky guess can be scored, but bare-arm performance is not a measure of a uniquely
correct English interpretation.

## Analysis

- Publish item-level outcomes; do not treat model calls as independent samples.
- Stratify by construct family and reader family before offering an overall summary.
- Use reader-clustered or reader-level intervals when several models or repeated runs are present.
- Keep model-family, provider, operator, quantization and task-designer linkage distinct.
- Preserve parser failures, timeouts and refusals in the denominator assigned by the preregistered rule.
- State all exclusions and retry rules before the run.
- A different prompt wrapper, task translation or clarification policy is a new instrument and must be
  reported as such.

## Claims this packet cannot support

Even a positive run does not establish human intuitiveness, general model-family benefit, external
adoption, lower future tokenizer cost, independent validation, or superiority of Ainglish overall.
Those require different evidence. A project-operated run on these project-designed tasks is internal
benchmark evidence even when the model identifiers differ.
