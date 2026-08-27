# Flagship surface audit v1

This is a deliberately small, model-only triage of all 17 current flagship candidates. Each
construct receives two balanced forced-choice consequence items in two conditions:

- `surface_only`: the model sees the marked message without an Ainglish definition;
- `one_line_definition`: the same task includes the catalog's plain one-line definition.

It asks two editorial questions: which forms are transparent to three already-installed model
families on first sight, and which become usable after one sentence of teaching? It is **not** human
validation, governance evidence, reader qualification, or an estimate of an Ainglish-versus-English
comprehension effect. Models may know the underlying English ambiguity while lacking Ainglish in
training; that is part of why these results may route editorial work but cannot qualify a construct.

`build.py` refuses missing on-disk model tags and freezes their exact digests before any call.
`run.py` rechecks those digests and has no pull path. The packet must explicitly say downloads are
unauthorised. `summarize.py` verifies both content digests and the complete model/item matrix.

## Result

All 204 preregistered cells completed with no format or transport error. Cold-surface accuracy was
`34/34` for Gemma 3 12B, `33/34` for Qwen 2.5 7B, and `32/34` for Mistral Small 3.2 24B. All three
models reached `34/34` after the catalog's one-line definition. The three cold misses fell on
`may-as-permission`, `you-one`, and `false-as-worded`; each was corrected by the teaching line.

This ceiling-heavy two-item screen is useful mainly as a rejection and copy-debugging gate. It
supports keeping all 17 surfaces in the editorial pool and identifies three captions worth always
showing. It does not distinguish the strongest candidates finely enough to rank them, and it must
not be promoted into a comprehension or human-intuitiveness claim.

```bash
python3 build.py
git commit items.json build.py run.py summarize.py README.md
python3 run.py
python3 summarize.py
```
