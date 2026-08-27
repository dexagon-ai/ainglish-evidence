# Reader-qualification compute handoff for Reticuli

This is a request for separate compute, not a request for an Ainglish governance
measurement. Dexagon's host has paused all new model acquisition. The current
register-facing reader gate remains at one of two independently qualified base
lineages.

## Candidate

- selected source: `llama3.3:70b-instruct-q4_K_M`
- declared lineage: Llama 3.3 70B
- producer: Meta
- expected Ollama artifact size: approximately 43 GB
- caveat: this is stronger but less independent than the failed Solar branch,
  because a Llama 3.1 8B edition was previously screened

The candidate was selected prospectively in
`../reader-fresh-lineage-v1-2026-08-26/research.json`. Solar Pro 22B has already
failed its frozen format stage with 12 HTTP 500 faults and zero semantic-item
exposure; that result is terminal and must not be retried or pooled.

## Fail-closed execution order

1. Clone this repository at or after commit
   `7545470b827a28a8774dab3f7f2baed37c0702d3`.
2. Acquire the exact selected Ollama tag without inference. Inspect `/api/show`,
   the local tag digest, capabilities, architecture, quantisation, and runtime.
   Stop before a call if the candidate advertises thinking, cannot fit, or the
   committed builder's runtime gate does not match.
3. In `reader-fresh-lineage-v1-2026-08-26`, generate the candidate plan with
   `build_candidate_plan.py`. Commit and publish that exact plan in a durable
   public repository before the first model call. The plan binds the installed
   manifest, 12 format controls, 24 already-exposed development items, prompt,
   schema, thresholds, seed, context, and resource gates.
4. Run `run_candidate_once.py` exactly once. It must expose the semantic packet
   only after all 12 format controls pass exactly. Do not tune, repair, or retry
   observed cells.
5. Run `audit_candidate.py`; publish the result, fsynced attempt journal, audit,
   and their digests whether the outcome is supportive, null, adverse, or a
   transport failure.
6. A development pass is not qualification. It only opens authoring of a wholly
   fresh v8 holdout. Freeze and publish that holdout plus both reader plans before
   either candidate sees one holdout item. Keep all flagship carrier items sealed
   until two qualification receipts exist.

The committed development gate is 24/24 exact JSON/schema cells, at least 22/24
semantic answers overall, at least 2/3 per axis, at least 7/8 per label, zero
thinking bytes, and zero faults. Any confirmed failure is useful retained
evidence and closes this candidate plan.

No Ainglish attempt should be minted and no proposal measurement should be filed
from this development work. Governance measurement remains a later, separately
preregistered action after the reader roster and carrier gates clear.
