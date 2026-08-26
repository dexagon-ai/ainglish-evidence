# Prospective reserve selection

This reserve was selected before observing any LFM2 development output. It is not downloaded and
has received no prompt or qualification item.

## Selected only if LFM2 fails: Yi 1.5 34B

- exact prospective tag: `yi:34b`
- producer/lineage: 01.AI, Yi 1.5 34B
- official Ollama page: <https://ollama.com/library/yi:34b>
- advertised local artifact: 19 GB, 34.4B parameters, Q4_0, 4K context
- independence rationale: a distinct producer and training lineage from Qwen, Liquid LFM2,
  Microsoft Phi, Google Gemma, Mistral, LG EXAONE, Meta Llama, IBM Granite, Cohere Command,
  TII Falcon, Zhipu GLM, AllenAI OLMo, and DeepSeek candidates already screened
- caveat: Ollama labels the underlying model architecture `llama`; this is architectural ancestry,
  not an independent-training receipt. The candidate therefore counts as a new trained lineage,
  not as a novel architecture.

If activated, the exact downloaded manifest and served capabilities must be frozen in a new plan
and committed before the format gate. Any advertised or served `thinking` capability refuses the
candidate before semantics. The unchanged 12-cell format gate and 24-cell exposed development gate
apply; no prompt, wrapper, sampler, or failed cell may be retried after observation.

## Rejected as the immediate reserve

The current 30B Nemotron offerings are not the immediate reserve. Their official Ollama pages
advertise thinking/reasoning modes, and Nemotron 3 Nano also says it was improved using Qwen. Those
properties make them a weaker fit for a clean, no-thinking second lineage even though their local
sizes fit the hardware:

- <https://ollama.com/library/nemotron-3-nano>
- <https://ollama.com/library/nemotron-cascade-2>
- <https://ollama.com/library/nemotron-3.5-lightning:30b-a3b>

This selection is prospective and procedural. It does not predict that Yi will pass, and it does
not authorize a download merely because LFM2 is slow. Activation requires a retained LFM2 failure
or incompatibility result first.
