# Resource boundary from the construction source

The prompt-free load check for the already cached plain
`mistral-small3.2:24b-instruct-2506-q4_K_M` reported a **131072-token context** and
37,105,413,652 bytes of GPU allocation. Windows C: free space fell from about
23.28 GiB to 4.55 GiB. The model was unloaded; the service subsequently reported
no resident models, and Windows later recovered to 23.24 GiB free.

No model was downloaded and no construction qualification/target call was made.
The exact operating-system mechanism behind the transient disk allocation is
not established. A later Windows pagefile query showed 4096 MiB allocated and
73 MiB in use, so it would be incorrect to assert that pagefile expansion caused
this event. Linux filesystem capacity is not a substitute for Windows headroom.

This plain source configuration is held on this host. Its safe replacement is
**a capable host running the same declared reader contract**, not quietly forcing
4096 context and calling it the same source configuration. The separately named,
already tested `ctx4k` readers used by rent, resume and verifier are different
contracts and are not substitutions for construction.

The batch runner now requires a successful latest resource probe for every exact
local model before scientific mint/spend. Recovered free space alone cannot waive
the failed Mistral probe. Raw successful and failed probes remain available.
