# Bounded, resumable research calls

This small shared runtime uses cached weights only, isolates physical GPU0, checks
both host and virtual-disk free space, and retains exact input and generated token
IDs. It never unloads another caller's model or changes the shared Ollama service.

Each call has a flushed and fsynced intent before inference and a hash-chained
completion afterward. A restart can reuse verified completed calls only under the
same plan and prompt. A partial row, an unknown in-flight call, changed inputs, or
another writer causes refusal. An interrupted call is **not** silently rerun; it
requires explicit reconciliation and a prospective continuation policy.

Research runs are not governance submissions. The official SDK, live qualification
requirements, mint-before-spend and independent settlement still govern those.

Checks: `python -m unittest discover -s overnight-runtime-2026-09-06`.
