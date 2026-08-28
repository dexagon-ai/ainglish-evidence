# Frozen run protocol

## Population

The editorial source is the 18-entry flagship catalogue pinned to Symfony commit
`a61dab4c2506cb3ace9b0faae50f879b468ed5a0`. Editorial inclusion does not imply ratification or
empirical support. The complete population is 18 constructs by ten frozen items, or 180 semantic
cells per reader.

## Scenario families

For each form pair the packet contains:

1. direct entailment for each pole;
2. a curated cross-form conclusion for each pole, whose relation can be contradicted,
   underdetermined, or asymmetrically entailed;
3. one unsupported boundary overread per pole;
4. each pole after a clearly delimited, non-asserted quote of the other pole; and
5. each pole targeted within two explicitly independent actual records.

Items never infer that two named forms are logical complements merely because the website presents
them as a useful contrast. That distinction is essential for modality, authority, cardinality, and
other asymmetric pairs.

## Reader and decoding contract

The allowlist is fixed before inference to Qwen 3.5 9B, Gemma 3 12B, and Mistral Small 3.2 24B
artifacts already present on the local Ollama server. Their served digests are frozen in
`reader-roster.json`; no pull endpoint exists in this runner.

Each construct is one fresh `/api/chat` request containing its ten items. Requests are sequential,
non-streaming, `think=false`, JSON mode, temperature zero, seed `2026082903`, context 8192, and at
most 768 generated tokens. The exact answer contract is an object with one `answers` array. It must
contain every requested ID exactly once and no other ID; every label must be one of the three frozen
labels. Array order is ignored.

Only `message.content` is parsed. `message.thinking`, finish metadata, token counts, timing, and the
complete raw response are retained. Empty content with non-empty thinking is an output-channel
failure, not a semantic error. No inference retry, prompt repair, or outcome-dependent model change
is allowed.

## Analysis and claims

Every malformed batch contributes ten invalid cells to the denominator. Results are reported by
reader, construct, family, label, and validity. There is no aggregate composite suitable for ranking
flagships, and high reference-grounded accuracy is not evidence of cold adoption.

The run may reveal risky explanatory wording, scope failures, complement assumptions, and response-
channel defects. It cannot establish human intuitiveness, independent replication, lifecycle
standing, training-data inclusion, or ratification readiness.
