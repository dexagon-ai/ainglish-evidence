# Bounded instrument review

Please review the actual `draft/items.json` and generator, not only this checklist. Report item IDs
and exact text for a defect. This is design review, not evidence of reader performance.

[Twelve excluded meaning witnesses](SEMANTIC-WITNESSES.md) make the main boundary judgments explicit.

1. Every declared set resolves uniquely, contains 2–8 distinct identities and is frozen before the
   hypothetical draw. No ambiguous/empty input is silently guessed.
2. The outsider is actually absent; criterion scores have one minimum; constant-first and the
   criterion procedure are distinct. Every candidate distribution sums exactly to one.
3. Weighted probabilities are unequal over distinct identities; the equal-probability candidate
   assigns exactly 1/N to each. One observed return is never used to infer the whole distribution.
4. `choose-any` allows first, criterion, weighted and uniform choices. It does NOT ban randomness.
   `draw-uniform` requires the equal-probability procedure, not a specific random-number technology.
5. An allowed implementation's properties are not extra obligations of the instruction itself.
   Neither form specifies replacement, future-draw independence or cryptographic unpredictability.
6. Both surfaces contain the same scenario facts. The English expansion carries all the relevant
   registered commitments and does not add hidden facts or omit inconvenient guarantees. The exact
   English projection remains an author/protocol review item; it is not yet certified verbatim.
7. Questions ask consequences via candidate procedures and auditor claims, not a direct mapping
   label. A complete answer record appears in neither presented surface.
8. Each response record encodes both complete probe answers, allowing all four right/wrong
   combinations. The joint score is not manufactured from marginal averages or unmatched cells.
9. Correct response positions are balanced per form. Check for unintended structural cues, not
   merely lexical equality. Token labels and table order must not reveal the correct record.
10. Wrong-pole and false-inference reports disclose what alternative was actually offered. A
    missing opportunity is not a measured rejection of a misconception.
11. 144 generated cases are not 144 independent semantic families. Name/frame variation cannot
    certify natural-language generalisation. The power sheet is an assumption-based sensitivity.
12. The new instrument is an original. Its broader question and all source/scoring changes must
    remain explicit; old measurements are neither rewritten nor relabelled as testing this design.

Useful contrast examples for an external review: `ca-completion-0001` / `0002` (first domain,
different forms), `0011` / `0012` (resource allocation), `0073` / `0074` (later world), and all
items whose `policy_contrast` is `equal-probability` or `out-of-set`. Reject ambiguous gold instead
of resolving it by the intended answer. No reader calls are requested by this review.
