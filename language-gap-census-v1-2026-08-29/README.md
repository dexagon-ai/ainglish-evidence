# Language-gap census v1

This is the discovery funnel for the six-entry cohort. It screens ten ordinary-English ambiguity
families against all **195** live and historical register proposals, then advances only two.

Selected:

1. **Explicit pronoun antecedent:** `it(<ref>)`. “The service notified the agent after it failed”
   can silently assign failure to either noun. The parameter names the intended antecedent.
2. **Universal-negation scope:** `none(<S>): <P>` / `not-all(<S>): <P>`. “All replicas are not
   healthy” can mean zero healthy replicas or merely fewer than all.

Both pass the five editorial checks and have clean seams with nearby entries. Pronoun number does
not resolve pronoun identity; quantifier force does not resolve the scope of universal negation.

The other eight candidates remain held or rejected. In particular, cancellation retention,
since-time/causal force, and approval/execution authorization are already expressible by composing
current Ainglish. The funnel does not create synonyms merely to increase proposal count.

Primary research anchors used in the proposal rationales are AmbiCoref for ambiguous pronominal
coreference (Yuan, Malaviya, and Yatskar, EACL 2023, DOI 10.18653/v1/2023.findings-eacl.75) and
Attali, Pearl, and Scontras for experimentally variable every-negation readings (ELM 2023, DOI
10.3765/elm.2.5376). References motivate the ambiguity; they do not substitute for Ainglish's own
preregistered evidence.

```bash
/home/dexagon/plugins/ainglish-openai-plugin/.venv/bin/python \
  language-gap-census-v1-2026-08-29/capture.py
python3 language-gap-census-v1-2026-08-29/build.py
python3 language-gap-census-v1-2026-08-29/audit.py
```

The similarity computation is intentionally advisory. Exact and lexical screening is paired with
manual semantic-neighbour review, because a low word overlap cannot establish conceptual novelty.
