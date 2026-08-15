# `each-alone / as-one` reader development screen 4

Status: **frozen before screen calls**.

Mistral Small 3.2 24B qualified in screen 3. Gemma 3 12B narrowly failed and was rejected. This
final development-only screen evaluates Qwen 2.5 7B as the second, distinct reader family using
the identical construct-free event-count task instruction and unchanged qualification threshold.

The screen reuses only the same six exposed generic controls and frozen runner. It requires 12/12
live exact cells and 6/6 explicit-count cells, runs on the dedicated GPU-0-only endpoint at a
4,096-token context, and permits no CPU fallback. It cannot become proposal evidence.

The canonical JSON SHA-256 of `screen-spec.json` is
`d104092975acfa69fea95d81e2bdb781f6c489b2761019e66b74f361b8be4be9`.
