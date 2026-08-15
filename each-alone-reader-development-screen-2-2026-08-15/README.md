# `each-alone / as-one` reader development screen 2

Status: **frozen before candidate calls**.

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
