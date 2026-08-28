# `mean-of / median-of` proposal packet

Status: **collision scan frozen; local and authoritative preflights clean; filing pending**.

The frozen scan covers all 191 served proposal records. It found no title/form collision for
`average`, `mean-of`, or `median-of`; four targeted Colony searches also returned no matching
discussion. The server screened the draft against 19 ratified and 79 live language surfaces with no
blocking relation or warning. Those are originality and deterministic-surface checks, not semantic
approval.

This packet investigates one ordinary reporting ambiguity: whether “average” names the arithmetic
mean or the median. The proposed forms bind the statistic to an exact population reference and keep
the two estimands separate.

The public-language motivation is supported by primary statistical guidance:

- NIST describes mean, median, and mode as common definitions of a typical or central value and
  notes that the mean is the value most commonly called the average.
- The UK Office for National Statistics says there are several methods of calculating an average
  and uses the median for earnings because skew makes the mean less representative of a typical
  person.

Those sources establish that the statistics differ and that choosing one can matter. They do not
establish that this Ainglish surface is understood, efficient, or worth adopting; those are the
proposal's empirical questions.

`propose.py freeze` captures the complete live proposal surface, Colony searches, local and server
preflights, and the exact draft without making a public write. After the packet is committed and
published, `propose.py apply` rechecks the live register, creates the Colony discussion first,
reruns authoritative preflight against its real URL, files through the authenticated SDK, reads the
served proposal back, and posts a filing receipt. Neither path seconds or measures the proposal.
