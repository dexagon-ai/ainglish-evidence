# Manifest-bound flagship carriers v1

This bundle converts five unspent flagship populations to the new load-bearing settlement shape,
without a reader, tokenizer, governance write, or post-hoc result label.

- `repeat-event / restore-state`: 256 scientific items across 16 equal cells—form × force × probe.
- `one-or-more / exactly-one`: 480 scientific items across 48 equal cells—form × comparator ×
  semantic seam. Ten operational roles independently populate every cell.
- preference valence, directive persistence, and may force: retained fresh populations become new
  stratified-original templates. They deliberately do **not** replicate their legacy pooled
  originals; a legacy estimand cannot acquire strata after seeing its result.

The role carrier makes its semantic scope particularly explicit. The marker counts distinct
principals inside the named role only. It does not say approvals are independent, permit
delegation, or establish that the same principal qualifies for another role. Those four seams are
separate cells in both forms and both comparator campaigns; none can be rescued by the headline.

Every template is sealed but non-runnable while the ordinary-English reader roster remains at
one of the required two independently qualified lineages. After the server and SDK changes deploy
and a second lineage qualifies, supply an exact panel JSON to `activate.py`. It searches only the
deterministic seed until every settlement cell has planned exposure in both arms; it makes no
reader or API call. The templates pin an immutable raw-GitHub URL for each matching
`*.items.json`; pass `@published` to use it (or supply another HTTPS mirror of the exact bytes).
Activation pins the canonical item digest and leaves bulky bytes out of the 20 KB attempt-manifest cap.
It refuses a panel unless every member carries a digest-bound `qualified=true` receipt and at
least two base-model lineages are present. The activated runspec includes the complete `attempt`
block, so `panel.py run <runspec> --submit` mints the exact clean-run manifest before its first
reader call and aborts rather than filing if a transport fault changes that commitment. Commit and
push the activated runspec before invoking that command.

```bash
python3 manifest-bound-flagship-carriers-v1-2026-08-27/build.py
python3 manifest-bound-flagship-carriers-v1-2026-08-27/audit.py

# Later, after both external gates clear:
python3 manifest-bound-flagship-carriers-v1-2026-08-27/activate.py \
  manifest-bound-flagship-carriers-v1-2026-08-27/role-cardinality.template.json \
  qualified-panel.json @published \
  role-cardinality.runspec.json
```
