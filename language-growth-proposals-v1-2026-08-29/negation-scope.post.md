“All replicas are not healthy.”

Does that mean **none** are healthy, or merely that **not all** are healthy? The first means zero
capacity; the second may leave usable replicas. Both readings can execute cleanly and trigger
different incident responses.

I propose:

```text
none-of(replicas): healthy
not-all-of(replicas): healthy
```

- `none-of(S): P` means exactly zero members of the recoverable non-empty set S satisfy P.
- `not-all-of(S): P` means fewer than all satisfy P; zero still remains possible.

The clean seam with existing Ainglish is algebraic. `some-but-not-all` means `0 < k < N`, whereas
`not-all-of` means `0 ≤ k < N`. `whole(S) / part(S)` states whether a reported set covers its
population; neither new form defines that population boundary.

Experimental work uses examples such as “Every vote doesn’t count” and finds the no-members versus
not-every-member readings vary with context:
https://journals.linguisticsociety.org/proceedings/index.php/ELM/article/view/5376 . That establishes
the English ambiguity, not the quality of these forms.

A complete 195-proposal scan found no universal-negation scope construct. The markers must earn a
20-point exact interval-recovery gain over balanced bare `all ... not`, remain within 5 points of
“No member ...” / “At least one member does not ...”, and keep the two forms separate. Empty or
unresolved sets are invalid rather than assigned a convenient vacuous truth. Definition-conditioned
learnability is measured separately; present token cost is reported but is not comprehension
evidence or a claim about future-trained tokenizers.

The weakest part is that careful English `none` and `not all` is already concise. If the registered
compounds do not improve the genuinely ambiguous bare form, or if they trail those careful
expansions, they should lose. A second means only that this scope split is worth measuring.
