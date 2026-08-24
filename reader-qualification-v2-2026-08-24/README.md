# Reader qualification v2

This package separates reader development from a one-shot, untouched holdout. Both stages use
ordinary English only, digest-bound local model editions, balanced answer positions, and the SDK's
`opaque-choice-v1` interface. They qualify an instrument; they are never proposal evidence.

`development.json` is the exposed development set. Its result may guide only the frozen reader
configuration and qualification rule. The holdout is added, committed, and pushed only after the
development result exists; its runner refuses to overwrite a result or duplicate an earlier item.

At least two distinct model lineages must pass the final holdout. If they do not, no new
comprehension attempt is minted: the failure package is published and offered to independent AI
carriers instead.
