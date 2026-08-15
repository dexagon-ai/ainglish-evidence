# `each-alone / as-one` reader development screen

Status: **completed; neither candidate qualified**.

This is a non-evidentiary reader-selection screen. It uses only the six generic controls already
exposed in the failed attempt and post-abort diagnostic. Those controls are now development data;
they cannot qualify a successor attempt themselves.

Two larger, distinct model families are screened with the exact Ainglish prompt and parser:

- Qwen 3.8 27B, Q4_K_M;
- Mistral Small 3.2 24B Instruct 2506, Q4_K_M.

The stock Mistral Ollama manifest contains an assistant-oriented default system prompt, while the
screen's claim requires user-message-only readers. The committed Mistral Modelfile therefore
overrides its chat template with a user/assistant/tool-only template: inherited system-role
content is deliberately not rendered into the model input. The Qwen source already has no default
system text. Both Modelfiles pin `num_ctx 4096`; no weight is changed or copied. The aliases are
the reader identities in the final screen spec.

A candidate qualifies only if all 12 calls are live exact options and all six explicit-count-arm
answers are correct, including 3/3 `one joint` and 3/3 `three separate`. Ambiguous-arm accuracy
is recorded but is not a selection criterion. No scientific item, marker, or held-out successor
control is present.

The screen runs once on a dedicated GPU-0-only endpoint with a 4,096-token context, one loaded
model and one request at a time. It cannot become proposal evidence. The canonical JSON SHA-256
of `screen-spec.json` is
`3ddeb6f9888cb05f1e5a7f4d61f4e7c0ebad2c3d7c9553d9133845b5c48ef740`.

## Result

The one-shot screen completed on 2026-08-15. Both models were loaded with a 4,096-token context,
and Ollama reported every model layer offloaded to GPU 0. Neither candidate met the frozen
qualification rule:

- Qwen: 10/12 live exact cells and 4/6 correct explicit cells (1/3 `one`, 3/3 `three`);
- Mistral: 12/12 live exact cells and 3/6 correct explicit cells (0/3 `one`, 3/3 `three`).

Qwen's two non-exact cells exhausted the output allowance without returning visible answer text.
Mistral returned `three` for all three explicit `one joint` cases. These candidates therefore
must not read the fresh held-out successor calibration bank or any proposal-science item. The
canonical JSON SHA-256 of `screen-results.json` is
`7d1bf35a8f71bdbcd5ebceb2809986e501e72ccc2f3353e2b23c9ce9289c7bc7`.
