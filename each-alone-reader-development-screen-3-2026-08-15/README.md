# `each-alone / as-one` reader development screen 3

Status: **completed; Mistral qualified and Gemma did not**.

Four candidate readers across two earlier development screens systematically treated the number
of plural participants as the event count, even when an exposed control explicitly stated one
joint event. A development-only prompt audit showed that a neutral event-count decision rule
corrected this interpretation. This screen tests that clarified reader interface before any
held-out or scientific content is exposed.

The committed system instruction is construct-free: it distinguishes participant count from
action-event count, tells the reader to honor explicit joint/separate event totals, and reserves
`cannot_tell` for a message compatible with both readings. It does not mention Ainglish,
`each-alone`, `as-one`, the proposal, or any scientific item. Mistral's alias also stops at the
first newline because its development response gave the correct fixed option on line one and then
violated the exact-output contract with an explanation.

The candidates are Gemma 3 12B and Mistral Small 3.2 24B, both Q4_K_M. The same six exposed
generic controls, frozen runner, strict 12/12 live-exact and 6/6 explicit-correct rule, dedicated
GPU-0 endpoint, 4,096-token context, one resident model, and no-CPU-fallback policy remain.

The canonical JSON SHA-256 of `screen-spec.json` is
`943dc3f6cedf8590f5e9beb305b1567f971a59ee82106ea6d14616df18c5a9f0`.

## Result

The screen completed on 2026-08-15 with both candidates fully GPU-resident at the frozen context.
Mistral qualified with 12/12 live exact cells and 6/6 correct explicit cells (3/3 `one`, 3/3
`three`). Gemma returned 12/12 exact cells but missed one explicit joint-event item, finishing 5/6
(2/3 `one`, 3/3 `three`), so it is not selected. No threshold was relaxed.

The canonical JSON SHA-256 of `screen-results.json` is
`63f4ee561fb914b4497d2a10b4a64390c21ee4884a75e9951ef0e1f62bf61408`.
