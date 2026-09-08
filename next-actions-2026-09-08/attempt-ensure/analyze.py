"""Replay completed cells and expose every prespecified subgroup; no inference."""
from collections import Counter
import json
from pathlib import Path
from ainglish import panel
from ainglish.client import manifest_commitment

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'execution'
spec = json.loads((ROOT / 'runspec.json').read_text())
result = json.loads((OUT / 'measurement-after.json').read_text())
files = list(OUT.glob('attempt-ensure.attempt-*.cells.json'))
assert len(files) == 1
cells = json.loads(files[0].read_text())['rows']
items = [x for x in spec['items'] if not x.get('calibration')]
by_id = {i['id']: i for i in items}
expected = {(i['id'], r['name']) for i in items for r in spec['panel']}
assert len(cells) == 512 and {(r['item_id'], r['reader']) for r in cells} == expected
normalized = []
for r in cells:
    gold = by_id[r['item_id']]['answer']
    assert r['arm'] == panel.arm_for(spec['seed'], r['reader'], r['item_id'])
    assert r['expected'] == gold
    assert r['correct'] == (None if panel.is_absent(r['answer']) else str(r['answer']).casefold() == gold.casefold())
    normalized.append((r['item_id'], r['arm'], r['reader'], r['answer']))
assert manifest_commitment(result['manifest']) == manifest_commitment(json.loads((ROOT / 'planned-manifest.json').read_text()))
contract = panel._settlement_contract(spec, items, spec['panel'], spec['seed'])
value, arms, strata = panel._stratified_accuracy(normalized, items, contract)
assert value == result['value'] and arms == result['arms']
for x, y in zip(strata, result['stratum_results']):
    assert x['id'] == y['id'] and x['value'] == y['value'] and x['arms'] == y['arms']
lo, hi, attested = panel.attested_bootstrap_accuracy(normalized, items, spec['panel'],
                                                   contract=contract, seed=spec['seed'])
assert panel._register_round(lo, 4) == result['value_lo']
assert panel._register_round(hi, 4) == result['value_hi']
assert attested == result['interval_provenance_attestation']


def summarize(subset):
    counts = {arm: {'correct': sum(r['correct'] is True for r in subset if r['arm'] == arm),
                    'n': sum(r['arm'] == arm for r in subset)} for arm in ['english', 'ainglish']}
    for arm in counts.values():
        arm['accuracy_percent'] = 100 * arm['correct'] / arm['n'] if arm['n'] else None
    counts['pooled_descriptive_delta_pp'] = (counts['ainglish']['accuracy_percent'] - counts['english']['accuracy_percent']
                                            if all(counts[x]['n'] for x in ['english', 'ainglish']) else None)
    return counts


groups = {}
for field in ['form', 'context', 'domain', 'probe', 'settlement_stratum']:
    groups[field] = {key: summarize([r for r in cells if by_id[r['item_id']][field] == key])
                     for key in sorted({i[field] for i in items})}
groups['reader'] = {r['name']: summarize([x for x in cells if x['reader'] == r['name']]) for r in spec['panel']}
groups['form_probe'] = {form + '/' + probe: summarize([r for r in cells
                                                     if by_id[r['item_id']]['form'] == form
                                                     and by_id[r['item_id']]['probe'] == probe])
                        for form in ['attempt', 'ensure'] for probe in sorted({i['probe'] for i in items})}
form_estimates = {}
for form in ['attempt', 'ensure']:
    subset_items = [i for i in items if i['form'] == form]
    ids = {i['id'] for i in subset_items}
    subset_rows = [r for r in normalized if r[0] in ids]
    subset_spec = dict(spec, settlement_strata=[s for s in spec['settlement_strata'] if s['id'].startswith(form + '-')])
    sub_contract = panel._settlement_contract(subset_spec, subset_items, spec['panel'], spec['seed'])
    sub_value, sub_arms, sub_strata = panel._stratified_accuracy(subset_rows, subset_items, sub_contract)
    sub_lo, sub_hi, _ = panel.attested_bootstrap_accuracy(subset_rows, subset_items, spec['panel'],
                                                        contract=sub_contract, seed=spec['seed'])
    form_estimates[form] = {'delta_pp': sub_value, 'arms': sub_arms,
                            'interval_95': [panel._register_round(sub_lo, 4), panel._register_round(sub_hi, 4)],
                            'strata': sub_strata, 'interval_scope': 'Official item-bootstrap method applied to prespecified tag subgroup; no multiplicity or template-cluster correction.'}

analysis = {'kind': 'dexagon.attempt-ensure-postrun-audit.v1', 'manifest_hash': result['manifest_hash'],
            'target_cells_checked': len(cells), 'allocation_or_gold_mismatches': 0,
            'official_estimator_and_interval_replayed': True,
            'headline': {'value': value, 'arms': arms, 'value_lo': result['value_lo'], 'value_hi': result['value_hi']},
            'per_tag_equal_context_estimates': form_estimates, 'descriptive_raw_counts': groups,
            'boundary': 'An original from two cached model families on templated authored inputs. Not independent confirmation, proof of equivalence, human validation, a bare-imperative gain test, training-effect evidence or token savings.'}
with (OUT / 'analysis.json').open('x') as out:
    json.dump(analysis, out, indent=2, ensure_ascii=False, allow_nan=False)
print(json.dumps({'headline': analysis['headline'], 'per_tag': form_estimates,
                  'per_probe': groups['probe'], 'form_probe': groups['form_probe']}, indent=2))
