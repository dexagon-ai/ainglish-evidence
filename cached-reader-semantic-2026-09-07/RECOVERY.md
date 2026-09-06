# Shared-service interruption, not a changed experiment

The original run stopped at the pre-request shared-caller guard. A separate
Qwen3.8 model arrived in the shared service; this campaign did not load, download,
unload or use that model. Its process and GPU workload were left untouched.

The journal contains all 16 Mistral neutral controls and the first 3 target
answers, with exactly 19 starts and 19 durable completions. There is no uncertain
in-flight call. Qwen and Gemma's completed failed screens are retained and will
not be rerun. The original study freeze is 37382e6.

`resume_unstarted_calls.py` may continue only after the service is empty and
memory/disk reserves are available. It validates the original hash chain,
complete request hashes and exact planned call order; any changed request,
non-prefix record, uncertain call or concurrent writer is a refusal. Completed
answers are reused verbatim. Only the next unstarted request can be sent.

The 213 remaining target requests, original qualification, model digest,
CPU-only options, 512-token cap, prompts, scoring and stop rules are unchanged.
The continuation code and its tests must be published before resuming. No
selection based on target answers, replacement readers, model downloads,
scientific retries, or qualification reinterpretation is authorised here.

If another caller arrives, stop again before the next request. A transport
failure after a start remains uncertain and cannot be automatically resumed.
An interruption is reported with the final study, not erased from its history.
