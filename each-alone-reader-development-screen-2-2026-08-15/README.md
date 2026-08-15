# `each-alone / as-one` reader development screen 2

Status: **completed; neither candidate qualified**.

The first development screen rejected both Qwen 3.8 27B and Mistral Small 3.2 24B. This second,
still non-evidentiary screen evaluates two different locally available model families:

- Gemma 3 12B, Q4_K_M;
- Qwen 3.5 27B, Q4_K_M.

It reuses only the same six already-exposed generic controls and the frozen screen runner. Neither
candidate may see the fresh held-out calibration bank or proposal-science items unless it passes.
Each candidate must produce 12/12 live exact cells and answer all six explicit-count-arm cells
correctly, including 3/3 `one joint` and 3/3 `three separate`.

Both aliases preserve the source model's native renderer/template and weights while pinning
`num_ctx 4096`. The screen runs sequentially through the dedicated GPU-0-only endpoint, with one
resident model and one request at a time.

The canonical JSON SHA-256 of `screen-spec.json` is
`7ccbe8d94dabbbaabf2b6a3d537d856b4d45391fec6cc5caa17f0dbf435e70fb`.

## Result

The one-shot screen completed on 2026-08-15 with both candidates fully GPU-resident at the frozen
4,096-token context. Neither met the qualification rule:

- Gemma: 12/12 live exact cells and 3/6 correct explicit cells (0/3 `one`, 3/3 `three`);
- Qwen: 4/12 live exact cells and 3/6 correct explicit cells (0/3 `one`, 3/3 `three`).

Gemma chose the plural-agent count in every explicit `one joint` case. Qwen did the same when it
returned an answer and exhausted its output allowance without visible answer text in eight cells.
Neither candidate may read held-out successor controls or proposal-science items. The canonical
JSON SHA-256 of `screen-results.json` is
`4b0f2564db1efc114e52adcf862162d29fb80fdc9bea36895d6986106acbe486`.
