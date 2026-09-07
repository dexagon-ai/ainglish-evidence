# Clearer interface, substantially better five-field reading

All 264 calls completed and are retained: 48 neutral controls and 216 language
targets. Exact requests, raw answers and native input/output token IDs accompany
the declared scores; `audit_results.py` reconstructs them from the hash chain.

| Requested fields | Qualification | Ainglish exact | Careful-English exact |
| --- | --- | --- | --- |
| One | 8/16, failed | Not run | Not run |
| Two | 16/16, passed | 11/12 | 6/12 |
| Five | 16/16, passed | 94/96 | 89/96 |

Every language answer was parsable and no call truncated. The one-field negative
controls emitted `insulated: false` inside a JSON fence, without JSON braces.
That explains a format-specific failure; it does not make those eight answers
pass the declared JSON contract or authorize one-field language targets.

This supports continuing with the more explicit interface. It does not establish
a general Ainglish advantage: the cases were already public and previously used,
there are only three authored contexts, both language guides are supplied, and
only one cached model/configuration was tested. The five-field difference is five
answers on this particular diagnostic population. The old poor results remain
published unchanged; this is a new prospective prompt and qualification study.

No proposal measurement, independent settlement, adapter training or language
release was created by this run. Harder unseen contexts and separate writer
qualification belong to the next, independently frozen research study.
