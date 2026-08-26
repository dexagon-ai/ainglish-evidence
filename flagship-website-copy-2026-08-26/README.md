# Flagship website copy pack

This package turns the live flagship atlas into publication-ready language without overstating the
evidence. It is editorial material, not a website implementation and not a measurement.

The four homepage cards are ratified, easy to explain in one sentence, and pinned to their current
register rows. Their captions describe the accepted meanings. They do **not** say that human
comprehension superiority has been experimentally established. The gallery and pipeline sections
retain the live evidence and lifecycle cautions that a shorter marketing treatment would otherwise
lose.

Source atlas:

<https://github.com/dexagon-ai/ainglish-evidence/tree/ad876ad/flagship-publication-atlas-v2-2026-08-26>

Live lifecycle refresh: `2026-08-26T20:38Z`. The source atlas supplies the ranking and editorial
guards; the copy pack now records role cardinality's later move from `proposed` to `seconded` and
its supportive price-only token receipt.

`publication-copy.json` is the structured source of truth. `homepage-copy.md` is a rendered copy
draft suitable for editorial review.

Safe global language:

- Ratified means accepted into the governed Ainglish register at the named version.
- A caption may state the ratified meaning of a construct.
- Ratification is not, by itself, a universal human-comprehension result, compliance guarantee, or
  proof that a process behind the words was adequate.
- Measured, seconded, and proposed pipeline cards must display their live stage and must not be
  visually presented as ratified entries.

## Required stale-card gate for integration

At site build or deploy, refetch every pinned slug and fail closed when its current revision,
stage, ratified version, supersession pointer, or evidence-warning class differs from the card.
Rerun the clean-seam collision screen against the current full register because a new neighbour can
invalidate an old editorial decision without modifying the old row. Any adoption wording also
requires a still-current `valid_until`. The JSON is a dated source document, not timeless content.
