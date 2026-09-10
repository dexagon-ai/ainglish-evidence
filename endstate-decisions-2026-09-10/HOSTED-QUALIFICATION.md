# Hosted readers can qualify without a weight digest

Checked against the installed official Ainglish SDK **0.2.59**. This is a software
contract check, not a reader qualification, measurement, paid call or server-side
acceptance test. The eight accompanying hermetic tests use invented observations
and a `.invalid` catalog. They make no network requests and file nothing.

## The distinction that matters for a new original

`reader_qualification.receipt()` makes `model_digest` optional. For an explicitly
labelled hosted reader, `validate_screen()` accepts `precision: provider-served`
and a matching `roster_id`, such as `deepseek-flash@provider-served`, without a
weight digest. `run_screen()` generates `qualified_at` and `valid_until` from the
actual run time and the prospectively declared `validity_days` (1 through 90).
That expiry is the qualification's validity horizon, not a promise by the provider
that its weights will stay unchanged.

The ordinary `prepare_reader_instruments()` path can bind `model_catalog:
openai:/models`. The served catalog-entry hash identifies the service entry, **not
the model weights**: `model_digest` remains null and weight identity remains
provider-opaque. Do not copy the catalog hash into `model_digest` or invent a
weight digest to get through validation. The hosted adapter refuses that.

After a real, frozen, target-independent screen, preserve its observations,
returned instrument and receipt. `reader_qualification.attach()` can add the
receipt to the corresponding manifest. The exact roster and answer-affecting
settings must match the intended study; the normal official preflight and panel
checks still apply. No claim is made here that an arbitrary hand-built manifest
will pass the live server.

```text
ainglish-qualify-reader check your-prospective-screen.json  # no reader calls
ainglish-qualify-reader run your-prospective-screen.json -o qualification.json
```

The second command **does spend inference**. Do not run it until the actual
screen, settings, call budget and intended new study are agreed. Include the same
explicit reader precision label in the screen and future original. A real screen
must vary answer positions and contain adequate planted-effect controls; do not
use the invented software-test fixtures as scientific controls. Preserve failures
without retrying until a pass. Do not backdate qualification to cover targets
already exposed, or retrofit these instructions into older filed results.

## The important legacy/plain-roster exception

SDK 0.2.59 has a distinct branch for a **plain roster name with no precision
field**. That branch requires `receipt_precision` and an explicit bound weight
digest. It therefore cannot serve a digest-unavailable hosted reader in that
shape. The accompanying test confirms this refusal too.

Do not silently add `@provider-served` to an old original's roster and claim an
exact replication. A new, prospectively declared hosted original can choose the
explicit shape above; any change to an existing source's scientific roster needs
its proper source-contract/repair treatment. This note establishes a working
SDK path for a **new** hosted study, not universal portability of legacy rows.

## What this does not solve

- Two provider endpoints are not automatically two independent model lineages.
- A qualified reader is not a second independent measurement principal.
- Control sensitivity is not target accuracy, human validation or future training.
- Access reported by one principal does not establish another principal's access.
- A successful SDK fixture does not count as an actual qualification receipt.

The prepared rent-learning study still needs two genuinely distinct reader
lineages, a shared accessible roster, and separately committed original and
fresh-input replication principals. Those requirements have not been relaxed.

Reproduce the offline checks with the project SDK environment:

```text
python -m unittest discover -s endstate-decisions-2026-09-10 -p 'test_*.py' -v
python -m ainglish.reader_qualification --selftest
```
