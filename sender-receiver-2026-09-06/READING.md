# No usable end-to-end advantage established

The 192 planned sender–receiver episodes completed, with **768 target calls and
24 target-independent controls**, no inference retries and no new model downloads.
Each episode used a free-text instruction, a receiver interpretation, one mandatory
sender clarification and a final receiver interpretation. Both languages received
an explicit meaning guide. No external task was actually executed.

The frozen analysis is unchanged in `analyse.py`, `RESULTS.json` and
`RESULTS.md`. The latter's short table reports **raw plan correctness**, not the
additional predeclared sender-format criterion. That distinction is essential:

| Model weights | Language used | First exact plan | Final exact plan | Final plan correct AND sender/clarification pass the prose-format check | Mean total tokens per episode |
| --- | --- | ---: | ---: | ---: | ---: |
| Base | Ainglish | 0/32 | 0/32 | 0/32 | 2,904.84 |
| Base | English | 2/32 | 3/32 | 0/32 | 2,792.00 |
| Ainglish-trained, seed 17 | Ainglish | 0/32 | 0/32 | 0/32 | 2,819.09 |
| Ainglish-trained, seed 17 | English | 0/32 | 0/32 | 0/32 | 2,470.59 |
| English-trained, seed 17 | Ainglish | 3/32 | 2/32 | 0/32 | 2,760.44 |
| English-trained, seed 17 | English | 1/32 | 1/32 | 0/32 | 2,469.09 |

The narrow frozen prose check requires non-empty, completed non-JSON text that
does not expose the exact five boolean field names. It is **not a semantic
validator or a human assessment of natural prose**. Even a pass would not prove
that the instruction preserved every fact or reference. No final successful
plan passed this additional check in either language or any weight condition.

## What failed

This post-collection explanatory breakdown does not remove any calls or change
the scorer. The 192-token sender/clarification cap was reached without EOS often:

| Weight condition | Language | Truncated senders | Truncated clarifications | Malformed final receiver plans |
| --- | --- | ---: | ---: | ---: |
| Base | Ainglish | 19/32 | 15/32 | 0/32 |
| Base | English | 26/32 | 11/32 | 0/32 |
| Ainglish-trained, seed 17 | Ainglish | 13/32 | 12/32 | 3/32 |
| Ainglish-trained, seed 17 | English | 5/32 | 2/32 | 0/32 |
| English-trained, seed 17 | Ainglish | 3/32 | 7/32 | 1/32 |
| English-trained, seed 17 | English | 3/32 | 5/32 | 0/32 |

Neither receiver stage was truncated. Passing the JSON-copy controls therefore
did not establish that the sender could generate a faithful, bounded five-choice
instruction or that the receiver could interpret it. In the first Ainglish case,
for example, senders mixed inclusive and exclusive groups and start and finish
bounds; some text said both that A was replaced and that it remained active.
These are real errors in the retained transmissions, not merely harsh JSON
parsing. All five marginal accuracies remain in `RESULTS.json`.

Only one previously wrong exact plan became correct after clarification (base
English), and one previously correct plan became wrong (English-trained weights,
Ainglish). The other four cells had no exact-plan change. A compulsory repair
turn is not an adaptive clarification policy, and the sender received the
receiver's interpretation, not an oracle verdict or a corrected answer key.

## Costs and integrity

The table counts input **and** output tokens across all four target calls,
including guides, ordinary instructions and the clarification history. It does
not subtract guide overhead. The guide itself is 151 tokens for Ainglish and
110 for English; repeated across four calls, that is 164 additional Ainglish
guide tokens per episode. The overall cost also depends on the different texts
actually generated. These are logical model-request tokens, not cached billing
charges, a latency-normalised score or a new tokenizer.

`JOURNAL-AUDIT.json` verifies all 792 call slots against the exact frozen prompt
schedule and independently recounts every input token with the pinned, cached
tokenizer. It preserves SHA-256 digests of the full journals. Output counts were
recorded at generation and checked against caps, but cannot be independently
reconstructed exactly from stripped decoded text: generated token IDs were not
journalled. That limitation is explicit rather than hidden behind a checksum.

All three JSON-copy screens passed 8/8. The run took about 89.3 minutes on the
already cached model, physical GPU0. The other GPU's workload was not displaced.
The six weights/language cells are retained, including malformed and truncated
outputs. The code and inputs were publicly frozen at `dc7eba1` before collection;
the mechanical journal audit was run after collection and changes no outcome.

## What this does—and does not—tell us

This setup did not produce a usable end-to-end demonstration in either language.
It is one base model, one prospectively selected training seed and **one authored
context with 32 factorial combinations**, not 32 independent task templates.
The adapters learned letter-answer comprehension tasks, not end-to-end instruction
writing. This is a transfer test under that curriculum, guide and token budget;
it is not a verdict on all future Ainglish-trained models or on human readability.

There is no clean language-wide efficiency conclusion to draw from a pipeline
that rarely transmits the full plan correctly. English's incumbent training and
the fixed tokenizer still matter; the experiment does not equalise pretraining
or model future tokenizer adoption. Nor may that future possibility turn these
current failures into supportive evidence.

A later prospective study should first establish sender semantic fidelity and
adequate output budgets on separate, target-independent multi-choice fixtures,
then test shorter messages and several independently authored operational contexts.
It should retain generated token IDs and score sender and receiver failures
separately. None of those changes was tried as a selective retry here. No
governance measurement, confirmation, ballot, ratification or release follows.
