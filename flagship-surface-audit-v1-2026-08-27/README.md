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

```bash
python3 build.py
git commit items.json build.py run.py summarize.py README.md
python3 run.py
python3 summarize.py
```
