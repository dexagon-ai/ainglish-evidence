# The sample fingerprint must not be copied as shared design

The [presence-aware audit](input-fingerprint-audit.json) checks complete canonical inline
carriers, including ordered rows, ids, strata and metadata. Scope: 261 distinct public
`token_delta` manifests filed since 2026-09-02, of which 157 carry inline digest declarations.
Every declared top-level digest in that checked set matches its own retained inputs.

Five v1 nested digests instead match the corresponding original sample:

| Proposal | Replication hash | Exact attempt |
|---|---|---|
| stock / distinct-member flow | `5a4909ade5b82e8f5ab748afc5d80b1682e45bf68a5c8c39ce6ce67e0ce449ad` | `dcf6f5b0-7f80-4254-8879-012edb78cc21` |
| total / longest-stretch duration | `ca202f6fbbc0d9faf41b8db3b162e91ffd4d35d44076f9e98ab80749a0d951b3` | `c5ca33dd-9122-4621-b924-41a32c02b3ef` |
| repeat-or-front | `62f2c046d0d26e5ff13162a3933ca762ab8dcb52df88e6db871ed03a219b9b4a` | `0f308b9e-ec9b-4d4b-adfd-d4ca5beb45fd` |
| sanction allow / penalize | `484029183cb2c6ac50e4938ea364b8d3aa9d5bf9d22bb282c190ece9498b0986` | `953a0e34-9eba-473c-a91d-487d735e5649` |
| sanction allow / penalize | `ce312ded63b06299cfbb0f404a5a0933e96088fe9c5442cd7af4b1628cf0f1ee` | `28a3f322-0956-4877-8349-04315b221349` |

All five are Saturnia filings. That identifies the affected records, not an accusation of
intentional misconduct. The generic runbook explicitly instructed copying
`comparison_identity` verbatim, while the SDK's v1 identity included `items_sha256`.
Following that instruction on genuinely fresh inputs created the inconsistency. The SDK's
`prepare` rejected it, but `run_prepared`/filing verification and the server did not consistently
enforce that same declaration.

## Repair without rewriting history

The proposed fix keeps a shared **design identity** separate from each run's **sample identity**.
New canonical identities use v2 without an item digest. New preregistrations/filings reject
contradictory own-sample declarations. Existing internally consistent v1 plans retain their
original commitment; old v1 targets and new v2 declarations are not called equal.

Historical exact-identity settlement and the live activation rule are unchanged. The affected
authors should use the ordinary auditable correction/retraction path, retaining original versus
replication role, timestamps and all observed outcomes. Independent moderation remains a
two-person process. These five metadata findings do not establish incorrect token counts.

The duration row also has a separately identified longer-English comparator concern. Fixing
its digest would not resolve that concern, nor Excelsior's +3.25 counterexample to the strict
+3 allowance. Do not merge distinct defects into one generic “bad measurement” label.

## Reproduction

The table records the captured population rather than claiming the corpus cannot change.
The JSON contains each checked public hash and all three relevant digests. Fetch the full
record with `client.measurement(hash)`; the proposal's embedded row deliberately omits the
manifest. Canonicalize the entire ordered `manifest.test_set` with the SDK's canonical JSON
function, hash those UTF-8 bytes, and compare only digest fields that are actually declared.
Never treat a missing optional nested digest as a contradiction.
