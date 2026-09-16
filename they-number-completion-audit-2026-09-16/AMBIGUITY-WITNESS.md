# A stronger, no-inference witness

The source audit above can be strengthened without guessing how a reader interpreted a sentence.

Run the adjacent ambiguity_witness.py with Python. It verifies the same 8417e8bf…6160 item pin
and groups real items by **English text, question and set of answer meanings**.

- The 192 rows contain 96 such semantic tasks.
- Every task occurs twice with two different keyed correct consequences.
- Example: t-001 and t-097 have the same bare message about the incident lead and coordinators
  approving a budget line, the same two-approval workflow question, and the same answer choices.
  One demands another approval; the other says the budget can be released.
- The only relevant number distinction is in the marked/hidden intended form, not the bare text.
- Option **order** differs in all 96 pairs. There are zero conflicts when the ordered option
  array is part of the identity. Thus this is not a claim of 192 byte-identical prompts, or a
  theoretical accuracy ceiling for a system that exploits presentation cues.

Changing choice order cannot change what the same English message entails. A semantic reading
cannot justify both requested definite consequences. This is why “cannot determine” belongs in
the correctness analysis, and why information conveyed should be reported separately. The rows
also do not constitute 192 independent semantic worlds for a precision calculation.

This witness neither recomputes a model result nor establishes the marked form's comprehension.
It makes the needed scoring decision concrete without a new panel.
