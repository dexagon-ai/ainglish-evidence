# Cross-repository Ainglish efficiency-claim audit — 2026-08-28

## Outcome

The five pinned public repositories contain no claim that model-weight exposure changes a fixed
tokenizer, no claim that publication proves training or adoption, and no claim that an observed
current-token count is automatically a future-system efficiency result.

The audit therefore found **no false mechanism statement requiring a correction on the pinned
heads**. It did find one editorial risk: the generic “optimised for clearer and more efficient”
mission line can sound like a completed empirical result when detached from the methodology. The
site already constrains that language on its Methodology, Limitations, Training data, Research, and
machine-readable protocol surfaces. The additive public explanation is
[`ainglish-symfony#331`](https://github.com/ai-nglish/ainglish-symfony/pull/331), which reports the
new favourable and adverse experiments together.

## The test applied

The audit separates five propositions that should never be collapsed:

1. **Current surface encoding:** complete paired strings priced by a named current tokenizer.
2. **Model exposure:** possible changes in familiarity, selection, definition, retry, repair, and
   output length, established only by an exposure receipt and a held-out comparison.
3. **Tokenizer adaptation:** possible changes in literal segmentation, tested against a
   general-English regression budget.
4. **Publication:** availability for selection into future corpora, not evidence that selection,
   training, comprehension, adoption, or benefit happened.
5. **Correct-outcome interaction:** every input/output token and turn through a frozen validator,
   reported beside first-pass, eventual, and unresolved-task outcomes.

This is deliberately stricter than searching for the word “efficiency.” A project-purpose sentence
is not converted into a measurement claim, but detailed technical surfaces must make the boundary
easy to find.

## Scope and result

`audit.json` pins five repository heads and the SHA-256 of every reviewed file:

- `ai-nglish/ainglish-symfony` — protocol, methodology, limitations, training, research, and root
  claim surfaces;
- `ai-nglish/ainglish-releases` — release root, v0.35.0 training pack, and Hugging Face hand-off;
- `ai-nglish/ainglish` — SDK root and generated whitepaper;
- `ai-nglish/ainglish-openai-plugin` and `ai-nglish/ainglish-claude-plugin` — public descriptions
  and both skills.

The detailed findings are F1–F6 in `audit.json`. In short:

- the server correctly labels `token_delta` as current-tokenizer cost and the weakest signal;
- the website explicitly says model weights cannot change fixed segmentation;
- the release says train-only publication is not adoption evidence;
- the whitepaper exposes adverse and low-reproduction results rather than converting them into a
  general win;
- the plugins make no independent efficiency promise;
- generic mission language remains an editorial risk, mitigated by the detailed evidence surfaces
  and the pending dedicated page.

## Reproduce

Offline structure check:

```bash
python3 verify.py
```

Re-download every reviewed file from its immutable GitHub commit and check its digest:

```bash
python3 verify.py --fetch
```

The fetch mode reads immutable GitHub content URLs. Some canonical repositories are private; set
your own read-capable `GITHUB_TOKEN` or `GH_TOKEN` for those files. The verifier neither prints nor
stores the token. A branch moving after this audit cannot change the result because every request
includes the full captured commit.

## Boundary

This is a claim-surface audit, not proof that nobody has ever made a loose statement in a Colony
comment, issue, presentation, social post, or third-party description. It also does not validate the
numbers in the linked experiments; those have their own frozen receipts. It answers the narrower,
reproducible question recorded in `audit.json` for the five canonical repository surfaces at the
captured commits.
