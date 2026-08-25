# Ratified-language cold/reference-loaded census

This census covers the 15 ratified language proposals not included in the earlier eight-form
flagship campaign. Multi-form proposals are kept at form-level resolution, yielding 24 campaigns
and 768 fresh scenarios (32 per form).

Each scenario freezes three answer-bearing arms:

- `cold_ainglish`: the registered form without a supplied definition;
- `reference_loaded_ainglish`: the same message preceded by the exact concise reference frozen in
  the row;
- `careful_english`: a complete ordinary-English rendering of the same facts.

The primary diagnostic is absolute held-out consequence accuracy per form and condition. Cold and
reference-loaded results estimate different deployment conditions and must never be pooled.
Careful English checks item and reader viability; it is not training material for the cold arm.
No positive result is independent confirmation of old ratification evidence, and any adverse result
is retained and reported as a post-ratification diagnostic.

`build_items.py` makes no network, model, tokenizer, or governance calls. `index.json` commits the
canonical packet and exact form counts. Reader spend remains gated on the separately frozen
cross-vendor ordinary-English qualification tournament.
