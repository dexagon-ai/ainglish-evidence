# A prospective compact response interface for actual dialogue costs

This is a new experiment, not a favourable re-score of the old JSON study. Its
32 target-independent controls use explicit present/absent facts and an exact
five-character Y/N response. At least28/32 must be correct, all must be valid,
and none may truncate. Failure means zero language calls, retained publicly.

If qualified, compare full retained history with a real per-turn local dictionary
lookup in three new scenario frames, two languages and32 jobs per conversation.
Both guides are explicit. The same greedy cached Qwen7 reader is used throughout.
No model download, adapter or real external action is involved. This does not
train Ainglish into the tokenizer or demonstrate unguided understanding.

Every initial call and at most one generic gold-oracle-triggered repair are
charged in exact input/generated tokens. Actual file bytes/read latency are
logged. History is not silently truncated, summarized or credited with a caching
discount. A full prompt that does not fit stops that conversation before spend.
Matched completed prefixes are reported per scenario; unexecuted future turns
are not extrapolated. First-pass correctness, final correctness, output validity,
repairs, unresolved work, context stops and cost all remain visible.

The new shape and control vocabulary are declared before qualification, so their
individual causal effects cannot be isolated. A clean format does not prove a
correct semantic answer. Three synthetic frames with32 binary configurations
each are not96 independent domains. This is product research, not governance
settlement evidence. The original4/16 qualification result is untouched.

`study.py build` freezes code, inputs, controls, plans and inherited dependencies.
Publish that freeze before `study.py run`. Execution requires14GiB available
host RAM, an idle physical GPU0 and at least15GiB physical Windows disk reserve;
the current CPU Mistral study is preserved, not evicted to satisfy those guards.
