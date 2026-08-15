# `each-alone / as-one` reader development screen 4

Status: **completed; Qwen qualified**.

Mistral Small 3.2 24B qualified in screen 3. Gemma 3 12B narrowly failed and was rejected. This
final development-only screen evaluates Qwen 2.5 7B as the second, distinct reader family using
the identical construct-free event-count task instruction and unchanged qualification threshold.

The screen reuses only the same six exposed generic controls and frozen runner. It requires 12/12
live exact cells and 6/6 explicit-count cells, runs on the dedicated GPU-0-only endpoint at a
4,096-token context, and permits no CPU fallback. It cannot become proposal evidence.

The canonical JSON SHA-256 of `screen-spec.json` is
`d104092975acfa69fea95d81e2bdb781f6c489b2761019e66b74f361b8be4be9`.

## Result

Qwen qualified with 12/12 live exact cells and 6/6 correct explicit cells (3/3 `one`, 3/3
`three`) while fully resident on GPU 0 at the frozen context. Together with the qualified Mistral
reader from screen 3, this supplies two distinct families for the successor attempt without
exposing held-out or scientific items during selection.

The canonical JSON SHA-256 of `screen-results.json` is
`78a9ee3623ae246fddc70940abf11f210a971625f3b6d7dfa17bfe67e1e0d689`.
