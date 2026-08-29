# Plugin ↔ SDK action-surface conformance result

Status: **pass**

The preregistered audit reproduced against three clean frozen checkouts. `RESULT.json` has SHA-256
`34689401068ea7d972a4d24c27b6df382894415a5a6df2b87e63238813849f90`; its canonical content seal is
`288354448a3b8788b08f2eba7896ec7f62f5ac83b8d05a25a1374639a40b77f9`.

## Result

| Surface | Frozen commit | Public/reviewed actions |
|---|---|---:|
| pending SDK source | `b68df2696dba276ddb2f06342d70859a712671fe` | 54 public callable methods |
| OpenAI/Codex plugin | `4bf0f1117d12aa5b3f5ab4d79db305a54a13c790` | 48 allowed actions |
| Claude plugin | `be45fc8fcedbdfb604d5721714b8fb10db7fe10c` | 48 allowed actions |

Both plugins expose exactly the same set. It equals the preregistered category union: 31 public
reads, 3 identity-scoped reads, 3 attempt reads, and 11 reviewed writes. Every exposed name is a
method in the frozen SDK source.

The SDK-minus-plugin complement is exactly the six declared exclusions:

- `get` and `post`: raw transport would bypass semantic action review;
- `amend`: the low-level complete-payload method is replaced by preview-first `amend_current`; and
- `webhooks`, `create_webhook`, and `delete_webhook`: infrastructure configuration is out of scope.

There is no hidden seventh omission. `flagship_evidence_map` and the authenticated,
server-authorised moderator action `rename_proposal_slug` are present in both plugin diffs.

## Version and failure behaviour

Both plugin requirements files contain exactly `ainglish>=0.2.43,<0.3`, and both CI workflows,
READMEs and skills repeat that range. The frozen SDK source still declares `0.2.42`, as expected:
the plugins are staged for a release that does not yet exist rather than claiming the new method is
available now.

During the pre-result code review, both dispatchers were corrected so an `AttributeError` raised
*inside* a valid SDK method is not misreported as a missing SDK method. A genuinely absent method
still returns the typed `SDK_METHOD_MISSING` envelope. The frozen plugin commits include paired
regression tests; the OpenAI/Codex suite passed 18 tests and the Claude suite passed 13 against the
pending SDK source.

## Consequence

The former dynamic OpenAI/Codex discovery behaviour is closed: adding a public method to a future
SDK within the pinned major range now fails the exact-complement test. It cannot silently add a
plugin capability. Conversely, removing a reviewed method also fails rather than shrinking the
surface invisibly.

## Remaining gates

This receipt does not clear the release chain. It does not show that the server evidence-map route
is deployed, SDK 0.2.43 is merged or published, remote MCP discovery is correct, either plugin PR is
merged, or the installed personal plugin was refreshed. Those are intentionally tested by the
separate production conformance packet after server deploy and SDK publication.
