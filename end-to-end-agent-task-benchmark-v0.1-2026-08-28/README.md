# Ainglish end-to-end agent-task benchmark v0.1

This is a frozen, transport-neutral benchmark for a harder question than sentence comprehension:
does the wording of a message change what a receiving agent actually does next?

The benchmark compares three meaning-related surfaces:

- `bare`: ordinary English whose relevant distinction is left implicit;
- `careful`: ordinary English that states the source intent explicitly; and
- `ainglish`: the registered compact form expressing that same source intent.

It measures executable task decisions, clarification, repair and wrong action. It does **not** yet
contain model results, establish superiority, count as Ainglish register evidence, or imply that its
task writers are independent of the project. A result becomes informative only when its reader,
operator, transport, prompt wrapper, model digest, item digest and complete output are published.

## What is frozen

- `tasks.json` contains 22 curated task decisions over eleven ratified distinctions from
  `ainglish-core-v0.35.0`.
- `benchmark.py` validates the packet, exports model-ready prompts and scores returned decisions.
- `SCORING.md` defines the estimands, comparison rules and claims that the benchmark cannot support.
- `MANIFEST.json` binds the packet to the source register and records the content digests.

The tasks deliberately include both poles of every distinction. A reader cannot succeed by learning
that one marker always means “act” or always means “wait”. Each task offers a small explicit action
space and one or more valid action sets. A clarification response is allowed; the scorer then accepts
one scripted, source-intent-preserving repair turn.

## Tracks

`cold`
: No Ainglish definition is supplied. This tests immediate compatibility with a reader whose exposure
  is unknown. It is an asymmetric present-day test because ordinary English was in the reader's
  training data and Ainglish may not have been.

`one_exposure`
: The Ainglish arm receives one short definition before the task. The definition and its tokens are
  part of the treatment cost. Bare and careful English receive no project-specific definition. This
  estimates practical use after one explicit teaching exposure; it is not a claim about pretraining.

The tracks must never be pooled. A future adapted-model track needs a new frozen version with training
receipts and held-out tasks; it must not be retrofitted into this packet.

## Use

Requires Python 3.10 or later and no third-party packages.

```bash
python3 benchmark.py validate
python3 benchmark.py export --track cold --arm all --seed 20260828 > prompts.jsonl
```

Feed each record's `prompt` to a fresh model conversation. Preserve `item_id`, `arm`, `track` and
`order`. Store the model's parsed response like this:

```json
{
  "item_id": "clusivity-include-01",
  "arm": "ainglish",
  "track": "cold",
  "reader_id": "provider/model@immutable-digest",
  "first": {
    "decision": "act",
    "actions": ["review-draft"],
    "input_tokens": 121,
    "output_tokens": 12,
    "latency_ms": 742
  }
}
```

If the first response is `clarify`, present the task's `clarification` text in the same conversation
and save the next decision under `repair`. Never give a clarification to only one non-clarifying arm.

```bash
python3 benchmark.py score responses.jsonl
python3 benchmark.py self-test
```

`score` emits descriptive per-arm and overall counts. A parser failure, refusal or non-contract output
must be retained as `{"decision":"invalid","raw":"<complete raw output>"}` rather than dropped. The
scorer refuses unknown items, arms, tracks, actions, duplicate reader/item/arm rows and a repair response
after anything except clarification. It does not manufacture confidence intervals or independence from
repeated cells. Use the frozen item-level records for a reader-clustered analysis as specified in
`SCORING.md`.

## Required publication receipt

A public run should include:

1. this manifest and its digests;
2. the exact prompt export and seed;
3. model and served-artifact identifiers, with digests where available;
4. provider and decoding parameters;
5. complete raw first and repair outputs, including failures;
6. parser code and parsing failures;
7. per-cell token usage and latency, or an explicit statement that either was unavailable;
8. operator, task-designer and model-family linkage as `known`, `linked`, `disjoint` or `unknown` at
   each layer; and
9. any departure from fresh conversations or the scripted clarification rule.

The useful adverse result is a reader that performs worse with Ainglish than with careful English.
Keep it.
