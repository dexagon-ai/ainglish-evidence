# `each-alone / as-one` reader development screen

Status: **frozen before candidate reader calls**.

This is a non-evidentiary reader-selection screen. It uses only the six generic controls already
exposed in the failed attempt and post-abort diagnostic. Those controls are now development data;
they cannot qualify a successor attempt themselves.

Two larger, distinct model families are screened with the exact Ainglish prompt and parser:

- Qwen 3.8 27B, Q4_K_M;
- Mistral Small 3.2 24B Instruct 2506, Q4_K_M.

A candidate qualifies only if all 12 calls are live exact options and all six explicit-count-arm
answers are correct, including 3/3 `one joint` and 3/3 `three separate`. Ambiguous-arm accuracy
is recorded but is not a selection criterion. No scientific item, marker, or held-out successor
control is present.

The screen runs once on a dedicated GPU-0-only endpoint with a 4,096-token context, one loaded
model and one request at a time. It cannot become proposal evidence. The canonical JSON SHA-256
of `screen-spec.json` is
`8eab9beb908d553cb497f2a44aadbb41ec63de7a2eccc757b9bee74f5a996720`.
