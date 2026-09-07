# Low-exposure tokenizer adaptation

A prospective offline successor to the earlier high-exposure pilot. It compares
background-only training with paired Ainglish or complete-English teaching at
maximum 0.1%, 1% and 5% of a fixed four-million-byte training budget. Both arms
use the same ordered record IDs and repetition counts. Actual byte fractions,
and the extra background needed to fill the shorter arm, are disclosed.

Two vocabulary sizes and two whitespace-preserving byte-level segmentation
policies yield 28 declared cells. Byte-exact reconstruction is required on every
heldout: English documents, authored code, Unicode/punctuation and a new lexical
set of paired examples. No unknown-token or whitespace-deletion shortcut counts
as efficiency. All cells and collateral costs are reported.

The source background corpus is already cached locally; only its hash, selected
record IDs and checksums are published here, not a new copy or a new rights claim
over other authors' text. No downloads or model-weight training are involved.
The synthetic teaching archive remains separate from evaluation files. The
Ainglish lexical holdout shares known teaching frames, not independent grammar.

This asks whether low exposure can alter a small new tokenizer's costs and at
what collateral cost. It cannot establish what an AI lab will train, whether
Ainglish will be adopted, or that future production efficiency is guaranteed.
