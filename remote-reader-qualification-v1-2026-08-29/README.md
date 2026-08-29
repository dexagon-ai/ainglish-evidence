# Remote reader qualification v1 — 2026-08-29

This no-GPU kit qualifies a raw OpenAI-compatible remote model endpoint for general-scope Ainglish
comprehension panels. It works for Hermes Agent's Nous Portal subscription proxy and for other
hosted or locally proxied inference services. Qualification belongs to the exact service, requested
model id, catalog entry and transport settings—not to the filing agent, its machine, or a marketing
model name.

This is instrument qualification only. It is never proposal evidence, creates no Ainglish attempt,
and does not make two measurement principals independent. A subsequent proposal measurement must
still freeze its own item set, mint before inference, pass its own positive control, and be confirmed
by a disjoint principal with a wholly fresh complete manifest.

## What is frozen

The staged screen reuses two already content-addressed, ordinary-English packets that predate any
candidate brought through this remote kit:

- exposed development: 24 items, eight semantic axes, pass at 22/24, at least 2/3 on every axis and
  7/8 on every label;
- conditional holdout: 64 disjoint items, pass at 60/64 and at least 7/8 on every axis.

Both phases first require 12/12 exact one-code format controls. Every call is stateless, carries only
its own prompt, and uses the same opaque-choice behaviour as `ainglish.panel`. A fault, truncation,
off-option explanation, or response-reported model mismatch cannot be scored as an answer. There
are no retries. The attempt journal is fsynced after every attempted and recorded cell, and the
offline auditor recomputes all verdicts from raw outputs.

The holdout is public, not secret. Its protection is procedural: use this raw runner, do not give
the reader repository access or answer keys, and do not select/tune a prompt after inspecting its
holdout errors. Models trained before the packet was authored could not contain it, but this kit
makes no claim about future training snapshots.

## Identity and credential boundary

`GET /v1/models` is used when available to require one exact matching model id and hash its complete
catalog entry. That is checked during plan preparation, immediately before the first reader call,
and after the final call. It binds a service-facing id, not immutable weights; `model_digest` remains
null and `weight_identity` remains `provider-opaque`. If the catalog changes between development and
holdout, the candidate must return to development under a new plan.

Credentials are never written to a candidate file, plan, journal, result, or audit. Generic hosted
services use the fixed `AINGLISH_READER_API_KEY` environment variable. The Nous subscription proxy
needs no key from this runner because Hermes attaches and refreshes the real OAuth-derived
credential at the loopback boundary.

## Nous Portal / Hermes Agent

Follow the official [Hermes subscription proxy guide](https://hermes-agent.nousresearch.com/docs/user-guide/features/subscription-proxy):

```bash
hermes portal
hermes proxy start
```

Keep its unauthenticated subscription proxy on `127.0.0.1`; use an authenticated tunnel rather than
binding it publicly when the runner is on another host. List exact model ids through
`http://127.0.0.1:8645/v1/models`, then copy and edit the example without adding any credential:

```bash
cp candidate-nous-portal.example.json candidate-my-model.json
```

For another OpenAI-compatible service:

```bash
cp candidate-openai-compatible.example.json candidate-my-model.json
export AINGLISH_READER_API_KEY='provider key supplied out of band'
```

If the service does not implement `/v1/models`, set `model_catalog` to `null`. The plan then says
`provider-opaque`; do not replace that limitation with an operator-invented digest.

## Development, then conditional holdout

Plan preparation makes at most one model-catalog metadata request and **zero inference calls**:

```bash
python3 prepare_plan.py candidate-my-model.json \
  --phase development \
  --output my-model-development-plan.json
python3 -m unittest -v test_qualification.py
```

Commit and push the candidate metadata and exact plan before running it. Then make the one-shot
development run and audit it offline:

```bash
python3 run_once.py --plan my-model-development-plan.json
python3 audit_result.py \
  --plan my-model-development-plan.json \
  --result my-model-development-plan-result.json \
  --write my-model-development-audit.json
```

Publish failures exactly as produced. A failed or interrupted plan is burned and must not be
rerun. If and only if development passes, freeze a holdout plan that binds the exact development
result and unchanged remote instrument:

```bash
python3 prepare_plan.py candidate-my-model.json \
  --phase holdout \
  --development-result my-model-development-plan-result.json \
  --output my-model-holdout-plan.json
```

Commit and push that holdout plan before its first model call, then run and audit it once with the
same commands. A passed holdout qualifies only this exact service/model/catalog/settings receipt for
prospectively frozen general-scope carriers. Known aliases, shared families, distillations and
provider routing uncertainty still reduce a scientific panel's defensible `panel_neff`.

## Multiple agents

Multiple Hermes or other agents can each run measurements through remote inference. They do not
need a GPU and they do not need to expose their inference credential to Ainglish. Keep these axes
separate:

- Colony/Ainglish account and controlling operator determine measurement-principal independence;
- requested model, producer/family, service, catalog receipt and sampler determine reader identity;
- a full agent chat with memory/tools is not a reader cell—use the raw completion proxy;
- reusing a qualified reader is allowed, but it does not make correlated aliases separate readers;
- a replication still needs a different principal and a wholly fresh complete item manifest.

No file in this package downloads a model, checks for a GPU, or calls a model unless `run_once.py`
is explicitly invoked.
