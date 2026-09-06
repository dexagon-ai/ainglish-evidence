# Frozen original blocked before mint or token exposure

At canonical SDK acc70d2, `prepare()` returned a mint-ready plan, but
`preflight_attempt()` rejected its final canonical manifest as larger than
20,000 UTF-8 bytes. No request was minted, no tokenizer was loaded, and no result
was filed. The frozen design at evidence da975af is retained unchanged.

The generic client advice to replace large inputs with an immutable URL is not
applicable here: Symfony `TokenResultVerifier` requires complete inline pairs and
does not fetch remote inputs. Both sides must be considered before declaring a
large token plan executable.

Do not silently reduce these 256 cells to a small result and describe it as the
declared full prerequisite. A SDK follow-up catches this limit during prepare
and explains it correctly; that safety change does not itself make this frozen
original runnable. A bounded, reviewed server/API solution or an explicitly
revised scientific design remains required. Current tokenizer cost is also
separate from the future-training hypothesis and the missing comprehension work.
