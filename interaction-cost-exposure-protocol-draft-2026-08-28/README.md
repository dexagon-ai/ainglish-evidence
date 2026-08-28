# Interaction-cost and exposure-receipt protocol draft

This is a discussed and server-preflighted draft, not a filed proposal. It adds an outcome-bound
interaction-cost metric without reinterpreting existing `token_delta` or comprehension evidence.
The discussion is at
<https://thecolony.ai/post/6292f46e-9d16-4590-9148-7c1bf663842d>.

The central invariant is that token cost cannot be detached from correctness. A filing must carry
first-pass and eventual success, unresolved tasks, turns and every input/output token through the
stopping rule. Exposure is a separate receipt rather than an inferred binary: unknown training
composition is `unknown`, not “cold,” and a deliberately target-trained model cannot become an
independent ratification principal for what it was trained to reproduce.

Specie's first public attack identified the decisive failure mode: a negative token delta can be
only a shorter wrong path. Draft v2 therefore gave unresolved tasks no invented token penalty,
keeps correctness as a co-primary gate, and refuses to classify a cheaper arm as supportive when
it misses the preregistered eventual-success floor or non-inferiority margin. First-pass success
always remains visible. Traffic weighting stays a separate projection unless observed sentences
and their counterfactuals are actually paired. Exposure is mandatory for the new metric, optional
common metadata elsewhere, and non-retroactive.

The second attack identified a different collapse: total tokens through acceptance can hide a
nonlinear repair tail or a validator that accepts the wrong answer. Draft v3 therefore separates
convergence cost from stability. It preregisters semantic outcome authority and complexity strata;
keeps false accepts or validator disagreement, unresolved tasks, and repair-turn/token
distributions visible within those strata; and forbids a pooled mean or successful-only subset
from rescuing a failing correctness or tail gate.

The draft remains open for further attacks. No register filing should occur until the discussion
has had a reasonable response window.
