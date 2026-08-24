# Reader qualification v2

This package separates reader development from a one-shot, untouched holdout. Both stages use
ordinary English only, digest-bound local model editions, balanced answer positions, and the SDK's
`opaque-choice-v1` interface. They qualify an instrument; they are never proposal evidence.

`development.json` is the exposed development set. Its result may guide only the frozen reader
configuration and qualification rule. The holdout is added, committed, and pushed only after the
development result exists; its runner refuses to overwrite a result or duplicate an earlier item.

Development selected Mistral Small 3.2 and Gemma 3 at 35/36 each. The Qwen 3.5 edition returned
36 bound-exhaustion truncations before a choice code and was excluded without prompt or bound
tuning. `holdout.json` therefore freezes the two developed editions over 48 new items: every cell
must emit an exact code, each reader must score at least 45/48 and at least 7/8 on every axis.

At least two distinct model lineages must pass the final holdout. If they do not, no new
comprehension attempt is minted: the failure package is published and offered to independent AI
carriers instead.

## Outcome

The holdout gate did not pass. Gemma qualified at 47/48 with every output an exact code. Mistral
returned an exact code in every cell but scored 44/48, including 6/8 on the authority axis. The
frozen rule required 45/48 and 7/8 on each axis from at least two lineages, so only one lineage
qualified and `roster_ready` is false. No comprehension attempt was minted and no scientific item
was shown to either reader after this result.

This holdout is now public and burned. Independent carriers should not use it as an allegedly
unseen qualification set. See `CARRIER_REQUEST.md` for the requested clean-room path.
