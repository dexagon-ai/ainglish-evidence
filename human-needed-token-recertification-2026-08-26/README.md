# `human_needed(<why>)` token recertification

This is a fresh deterministic **price-axis** recertification of the ratified escalation marker. It
does not test whether humans or models understand the marker.

The packet freezes 32 unique complete pairs. Each marked sentence is compared with careful English
that carries both pieces of the proposal's mapping: a human must decide, and the agent must not
resolve the issue itself. The headline is the least-favourable maximum of mean `token_delta` across
`cl100k_base`, `o200k_base`, and `p50k_base`, with tiktoken pinned to 0.13.0.

Declared support requires the least-favourable mean to remain below zero. The packet, digest, and
runner are published before minting; any finite supportive, null, or adverse result must be filed.

## Result

The fresh original was minted as attempt `2ff62bed-52bf-498d-95f9-8068e22445df` and filed under
manifest/measurement hash `ce7400178a0d4fe6dd1e3ddd6ac7884bad6b4ebbdf145520e3d7b1421acc673f`.

| Tokenizer | Mean token delta |
|---|---:|
| `cl100k_base` | -7.625 |
| `o200k_base` | -7.78125 |
| `p50k_base` | -5.3125 |

The least-favourable headline is **-5.3125 tokens**, so this fresh price axis supports the declared
`< 0` prediction. `p50k_base` diverges from the panel median under the protocol's diagnostic; the
least-favourable rule already exposes rather than hides that result. The row is an unconfirmed
recertification original and requires an independent, disjoint, fresh-input replication before it
settles. The earlier confirmed register verdict remains unchanged.
