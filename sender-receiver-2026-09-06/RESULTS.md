# Sender–receiver prose task

Synthetic local research, not language-governance evidence. Every episode includes one prescribed clarification; cost includes all four calls.

|Model condition|Language|First correct|Final correct|Total input tokens|Total output tokens|
|---|---|---:|---:|---:|---:|
|base|ainglish|0/32|0/32|79663|13292|
|base|english|2/32|3/32|75542|13802|
|ainglish-17|ainglish|0/32|0/32|77616|12595|
|ainglish-17|english|0/32|0/32|68633|10426|
|english-17|ainglish|3/32|2/32|76464|11870|
|english-17|english|1/32|1/32|68441|10570|

## Limits

- One base model, one preselected training seed, single-author synthetic instructions.
- Receiver proposes a plan; the runner simulates its correctness without executing external actions.
- Both guides are visible; this does not test unaided reading or external adoption.
- Tokenizers are fixed; learned weights cannot change segmentation.
