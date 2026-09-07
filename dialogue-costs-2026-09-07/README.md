# Executed dialogue costs

Four real conversations: two languages × reference-once history or a real local
dictionary lookup on every independent turn. Both languages get explicit guides.
The jobs use ratified constructs and a fresh 32-combination sequence, not trained
adapters. Each new job resets its ledger rather than silently carrying past
instruction state forward.

The chosen working window is 8,192 tokens, with 256 reserved for output. Requests
are measured using the actual cached tokenizer before spend. A conversation
stops at that limit: no silent truncation, hypothetical continuation, or
extrapolated break-even. Report only matched prefixes actually completed by all
four conditions; retain condition-specific full ledgers too.

An exact gold check may trigger one generic correction per turn. This is
teacher-assisted repair, not autonomous error detection. Both failed first
answers and all correction costs remain in the record. A fresh neutral screen
qualifies the interface, not the target language. Raw prompts, answers and exact
token IDs are retained by the inherited hash-chained runtime.

Dictionary reading is real local JSON lookup, not web/vector retrieval. Its
bytes and time are separate from inference tokens. Token counts are not provider
bills and assume no unmeasured cache discounts. No model downloads, training,
external execution, governance filing or claim of human validation is involved.
