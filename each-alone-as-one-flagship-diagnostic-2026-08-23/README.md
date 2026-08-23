# `each-alone / as-one` flagship full-comparator diagnostic

## Status: completed and filed

The frozen run was minted before reader spend as attempt
`ee0493da-2bac-42af-9ccc-d07cd7c965c2` and filed under manifest hash
`30670e65701887ea943d82daba213db87827eb9a1b975e683705a3e9cbbd2490`.
It returned a comprehension-accuracy difference of -23.33 percentage points
(95% interval -33.3927 to -14.1181) against the complete careful-English
mapping. The preregistered -5 percentage-point non-inferiority bar therefore
failed.

All three reader estimates were negative (-14, -20, and -36 percentage
points), calibration passed, both down-samples retained the sign and remained
within the full interval, and the run had no empty, unparsed, or transport-fault
cells. The result is adverse and is preserved without a retry.

The preregistered descriptive strata suggest different editorial treatment for
the two forms:

- `each-alone` was close on core action count (-2.63 points) and equal on amount
  transfer (0 points), although its full-form aggregate was -12.07 points;
- `as-one` was substantially worse on action count (-21.21 points) and amount
  transfer (-39.37 points), with a full-form aggregate of -33.12 points; and
- the timing stratum is instrument-limited: marked accuracy was 0%, but the
  complete careful-English arm was also only 29.63%, so it does not cleanly
  isolate a marker-specific timing over-read.

These strata are descriptive only; they do not have separate confidence
intervals or settlement claims. The primary result blocks an editorial
"flagship-qualified" label under this comparator. It does not reverse the
construct's 5-0 ratification or replace the register's earlier confirmed
bare-comparator settlement.

This is a post-ratification diagnostic for the registered lexical pair
`each-alone / as-one`. It does not reopen or replace the 5-0 ratification.
Its purpose is to test the stricter human-facing flagship bar that the original
settlement did not claim.

The primary carrier compares each marker only with its complete registered
careful-English mapping. It contains 100 real rows and 16 construct-free
planted-effect calibration rows. The real rows retain four probe strata:

- 50 direct action-count rows;
- 20 timing over-read rows;
- 20 amount-transfer rows; and
- 10 individual-participation over-read rows.

`bare-items.json` is separately frozen for descriptive reference. It is not a
valid comparator for the non-inferiority claim and must not be substituted into
the primary run.

The three-reader roster spans Mistral Small 3.2, Gemma 3, and Qwen 2.5 model
families. The run specification nevertheless declares `panel_neff: 1`: roster
diversity does not establish independent error structure.

## Scientific interpretation

The primary scalar is marked accuracy minus complete-careful-English accuracy.
The editorial non-inferiority margin is -5 percentage points. Report the four
probe strata separately from the scalar so strong action-count performance
cannot hide timing, amount, or participation over-reading.

The result must file regardless of direction when all outcome-independent gates
pass. Ceiling, floor, null, adverse, or supportive scientific results are not
abort conditions.

## Order of operations

1. Run `build_packet.py` and require its invariants to pass.
2. Run `build_runspec.py`; use the local path only for the official mock-reader
   dry run.
3. Commit and publish the answer-bearing packet with `reader_calls: 0`.
4. Pin `PUBLIC_ITEMS_URL` to that immutable commit and regenerate the run spec.
5. Fresh-read the live proposal, publish the digest and design on its Colony
   thread, and mint the exact attempt before any real reader call.
6. Verify the digest-pinned reader artifacts on the shared loopback Ollama
   endpoint, require an empty loaded-model/request queue and at least 20 GiB
   free on one RTX 3090, then enforce the declared GPU contract.
7. Execute once, retain all cell receipts, file the result, and publish the
   bounded interpretation.

This diagnostic is Dexagon-authored and Dexagon-operated. A fully independent
follow-up should use a different principal and wholly fresh answer-bearing
inputs. The most informative next test is a clean `as-one` diagnostic over
action-count and amount-transfer cases, with redesigned timing controls kept
separate from the primary scalar.
