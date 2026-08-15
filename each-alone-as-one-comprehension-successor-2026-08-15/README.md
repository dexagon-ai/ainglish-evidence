# `each-alone / as-one` comprehension successor

Status: **runspec frozen and dry-run verified; no selected reader calls made**.

This is the clean successor to aborted attempt `c4ddce0b-eac5-46b4-b1ec-b391e62516cc`.
It retains all 19 scientific rows from Rosetta's committed source without field edits. A fresh
12-item, construct-free held-out calibration bank was authored only after two reader families had
qualified on previously exposed development controls:

- Mistral Small 3.2 24B in screen 3;
- Qwen 2.5 7B in screen 4.

Neither selected reader has seen this bank or any scientific row in its task-configured form.
The bank contains five `one`, five `three`, and two `cannot_tell` answers. Participant counts are
never one or three, preventing a model from passing by copying the grammatical subject's number.
The planted arm explicitly records the action-event total; the comparison arm remains ambiguous.
The two `cannot_tell` controls state non-availability rather than inventing a total.

As before, a positive scientific result can support ambiguity resolution versus bare plural only.
It cannot establish non-inferiority to careful English. The task instruction is transparent,
construct-free, and pinned in each reader's committed Modelfile: count action events rather than
participants, honor explicit totals, and use `cannot_tell` when both readings remain possible.

The held-out bank's canonical document SHA-256 is
`655b616d8fe42ca4ab89d9569bed83f991a9e010364a955b46fe4d781b440c8d`. The combined 31-item
array's canonical SHA-256 is
`0e846004836d73f725c2ae285e07c02d64bf519fe1a43f548236080c79cb6548`.

## Frozen execution

Seed `35` was selected solely from frozen item identities and selected-reader names. For each
reader it assigns exactly four `each-alone` and four `as-one` rows to each arm. The three bare
controls split 2/1 for Mistral and 1/2 for Qwen, so pooled scientific arms are exactly 19/19.

`runspec-dedicated-gpu0.json` points to the immutable item freeze commit
`54d045004603f1d88670e5deef130e0c1d0b3a43`. Its on-disk SHA-256 is
`0e138d04bde0c6cf981438937ac386d458735fe93e74a624e5e602526f2a8be2`, and its canonical JSON
SHA-256 is `0dfcec98d7d65d5acaf85cdab6ca11db072dd5062ef662b9237cc99887ae8ab6`.

The Ainglish 0.2.29 dry run fetched the immutable items, verified commitments, allocation,
calibration-first execution, yield accounting, bootstrap/resample-down logic, attempt payload and
measurement shape with zero API and zero model calls. `dry-run.txt` has on-disk SHA-256
`7963c74230645936484b6d253488b2bd13119fc97451fccf22cf265454116806`; its mock-oracle value is
plumbing output, explicitly stamped non-evidentiary and not submittable.
