# Interpretation and operational audit

This note interprets the frozen analysis without changing its preregistered scorer, rows, exclusions,
or denominators. The complete generated tables are in `RESULTS.json` and `RESULTS.md`; every raw
response is in `results/responses.jsonl`.

## Bottom line

On these already-installed readers, compact Ainglish usually improved zero-repair task success over
ordinary ambiguous English, but careful English that spelled out the same intent usually remained
better. One prompt-local exposure to each Ainglish definition narrowed that gap substantially without
closing it overall.

For the primary Ainglish-minus-careful comparison:

- prompt-cold reader effects had mean `-0.136364` and median `-0.159091`; 1 reader was positive,
  4 tied, and 17 were negative;
- one-exposure reader effects had mean `-0.035124` and median `-0.0227275`; 5 readers were positive,
  6 tied, and 11 were negative.

For the secondary Ainglish-minus-bare comparison:

- prompt-cold reader effects had mean `+0.074380` and median `+0.045455`; 13 readers were positive,
  7 tied, and 2 were negative;
- one-exposure reader effects had mean `+0.165289` and median `+0.181818`; 19 readers were positive,
  2 tied, and 1 was negative.

The all-row zero-repair rates tell the same descriptive story. Prompt-cold Ainglish reached
`221/484` (`45.7%`), compared with bare English at `185/484` (`38.2%`) and careful English at
`287/484` (`59.3%`). After one prompt-local definition, Ainglish reached `267/484` (`55.2%`),
compared with bare English at `187/484` (`38.6%`) and careful English at `284/484` (`58.7%`).

This is compatible with the project's future-training rationale, but it does not demonstrate it.
These artifacts were selected because they were already installed, their actual pretraining exposure
is unknown, and one prompt-local definition is not tokenizer integration or foundation-model
training. The result supports testing whether real training exposure can retain Ainglish's compactness
while approaching the explicit comparator's reliability.

## Construct diagnostics

The largest persistent weakness was `true-as-worded / false-as-worded`: its Ainglish arm trailed the
careful arm by `23/44` prompt-cold cells and `20/44` one-exposure cells. This is a practical warning
that a superficially transparent label is not enough for unfamiliar machine readers when it scopes
over a negated question.

One exposure produced the largest favourable item shift for `by-withheld` (`+6/22` versus careful),
with smaller favourable shifts for the inclusive-disjunction and distributive-plural items
(`+3/22` each). These are diagnostics, not independent construct-level confirmations: there are only
two items per construct, the project designed the tasks, and reader families may share ancestry.

## Output and transport failures

All 2,904 scheduled rows are present and all failures remain in their frozen denominators.

- `solar-pro:22b` returned HTTP 500 for all 132 cells. It therefore contributes all-failure rows and
  zero reader-level paired effects. The generated report includes it rather than silently excluding
  it; token and latency coverage is consequently `462/484` in each track/arm group.
- `deepseek-v2:16b` returned a receipt on every cell, but 127 of 132 first outputs violated the exact
  JSON decision contract. It is operationally observed but nearly unusable under this protocol.
- Other readers also sometimes returned fenced JSON, action names in the decision field, missing or
  extra keys, or other schema violations. The strict frozen contract counts those as task failures.
  Invalid-output rates were similar across arms, at roughly one quarter of all rows, so these failures
  are not evidence of Ainglish semantics alone.

Excluding `solar-pro:22b` post hoc would not reverse the directional result: among the 21 readers that
returned at least some usable decisions, the mean Ainglish-minus-careful effect was `-0.142857`
prompt-cold and `-0.036797` after one exposure. Those sensitivity figures are descriptive and do not
replace the preregistered all-reader result.

## Efficiency boundary

No present token-efficiency win was observed here. Over rows with provider token counts, mean raw
interaction tokens were 229 for prompt-cold Ainglish versus 223 for careful English, and 246 for
one-exposure Ainglish versus 223 for careful English. The one-exposure reference is correctly charged
to the Ainglish arm. Counts come from different model tokenizers and are descriptive rather than a
single tokenizer-independent efficiency estimate.

This present-day result should not be projected unchanged onto future models trained on Ainglish.
Conversely, hoped-for future tokenizer or training benefits must not be presented as measured current
efficiency. A future-training evaluation should freeze the same task semantics, compare the same base
checkpoint with and without controlled Ainglish exposure, and report task success separately from
token cost.

## Claim boundary

This run supports a narrow claim: for this frozen task set and these project-operated installed
artifacts, compact Ainglish was generally more actionable than ordinary ambiguity, careful explicit
English was generally more actionable than prompt-cold Ainglish, and a single supplied definition
narrowed the latter gap. It does not establish human intuitiveness, independent replication,
pretraining inclusion, external adoption, model-family independence, future token efficiency, or
Ainglish superiority overall.
