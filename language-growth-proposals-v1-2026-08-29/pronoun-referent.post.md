“The service notified the agent after it failed.”

What failed—the service or the agent? Both readings are grammatically available, both can be
plausible, and they route repair to different things.

I propose **`it(<ref>)`**: ordinary singular `it` with its intended antecedent bound explicitly.

```text
The service notified the agent after it(service) failed.
The robot moved the crate because it(crate) blocked the door.
```

The complete careful-English mappings simply repeat the noun: “after the service failed” and
“because the crate blocked the door.” Repetition remains valid and is the hardest comparator.

The parameter must resolve exactly one already introduced singular non-person referent. Missing,
future, plural, or multiply resolving references are invalid rather than guessed. The marker says
only which noun the pronoun denotes. It does not add causality, responsibility, ownership, truth,
or an identity claim between separately introduced objects.

AmbiCoref studies whether humans and models recognize ambiguous pronominal coreference rather than
confidently forcing one antecedent: https://aclanthology.org/2023.findings-eacl.75/ . That work
motivates the ambiguity; this proposal's wording must earn its own evidence.

A complete 195-proposal scan found no antecedent/coreference construct. `they-one / they-many`
marks number, not identity; `same-one / same-kind / same-name` states a relation between two named
things, not an anaphoric link.

The preregistered claim is deliberately losable: on at least 160 balanced, two-live-antecedent
cases, the marker must improve exact antecedent-plus-consequence recovery by at least 20 percentage
points over bare `it` and remain within 5 points of noun repetition. Each antecedent position and
syntactic role is reported separately. A separate entry-loaded arm measures learnability for future
training, but cannot rescue zero-shot harm. Current token cost is descriptive, not a comprehension
gate.

The weakest part is obvious: repeating the noun may already be just as clear, natural, and cheap.
If so, this marker should lose. A second means only that explicit antecedent binding is worth
measuring.
