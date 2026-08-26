# Flagship editorial audit v3

This is a cheap builder/editor screen over the frozen v3 atlas. It is not a model measurement and it does not recruit a large human panel.

## Result

- `15/17` cards keep lifecycle claims honest.
- `4/17` contain the full problem → ordinary ambiguity → Ainglish contrast → operational consequence story in the captured public data.
- `15/17` pass the bounded editorial judgement.
- `13` are blocked on captured publication copy, not on language quality.

The expected pre-deploy finding is that the 13 currently deployed catalogue rows lack the new `problem` and `consequence` fields. Ainglish-Symfony PR 294 supplies them and adds four candidates; a post-deploy audit should see 17 live rows and zero draft overlay rows.

## Blocked captured cards

- `we-including-you / we-excluding-you`: problem_is_question, operational_consequence_present
- `you-one / you-all`: problem_is_question, operational_consequence_present
- `fact-not-known — <ISSUE> | choice-not-made — <ISSUE>`: problem_is_question, operational_consequence_present
- `<ACTION>, no-delegation | <ACTION>, one-hop-delegation-allowed`: problem_is_question, operational_consequence_present
- `each-alone / as-one`: problem_is_question, operational_consequence_present
- `by-unknown / by-withheld`: problem_is_question, operational_consequence_present
- `<ACTION> start-by(<t>) | <ACTION> complete-by(<t>)`: problem_is_question, operational_consequence_present
- `or-both / not-both`: problem_is_question, operational_consequence_present
- `true-as-worded | false-as-worded`: problem_is_question, ainglish_contrast_present, operational_consequence_present
- `moved-earlier / moved-later`: problem_is_question, operational_consequence_present, pin_current
- `<enumeration>, among-others / <enumeration>, and-no-others`: problem_is_question, operational_consequence_present, pin_current
- `some-or-all / some-but-not-all`: problem_is_question, operational_consequence_present
- `may-as-permission / may-as-possibility`: problem_is_question, operational_consequence_present

## Research-preview judgements

- `repeat-event: <EVENT-CLAUSE> | restore-state(<RESULT-STATE>): <CHANGE-OF-STATE-CLAUSE>`: The contrast is intuitive, but asymmetric arguments and force projection still prevent a five-second surface pass.

## Stop rules

- Do not turn the editorial pass into a comprehension claim.
- Do not promote a candidate by omitting its live stage.
- Do not hand-edit the frozen result after deployment; capture a successor audit.
- Do not require a costly human panel for this bounded copy screen.
