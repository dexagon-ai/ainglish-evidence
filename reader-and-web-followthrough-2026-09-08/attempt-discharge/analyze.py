"""Replay filed cells and report prespecified groups; never run inference."""
from collections import Counter
import json
from pathlib import Path
import re
from ainglish import panel
from ainglish.client import manifest_commitment

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'execution'
spec = json.loads((ROOT / 'runspec.json').read_text())
result = json.loads((OUT / 'measurement-after.json').read_text())
paths = [p for p in OUT.glob('attempt-discharge.attempt-*.cells.json') if '.calibration.' not in p.name]
assert len(paths) == 1
cells = json.loads(paths[0].read_text())['rows']
items = [i for i in spec['items'] if not i.get('calibration')]
by_id = {i['id']: i for i in items}
assert len(cells) == 384
assert Counter((r['item_id'], r['reader']) for r in cells) == Counter((i['id'], r['name']) for i in items for r in spec['panel'])
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
for actual, filed in zip(strata, result['stratum_results']):
    assert all(actual[k] == filed[k] for k in ['id', 'value', 'arms'])
lo, hi, attested = panel.attested_bootstrap_accuracy(normalized, items, spec['panel'], contract=contract, seed=spec['seed'])
assert panel._register_round(lo, 4) == result['value_lo']
assert panel._register_round(hi, 4) == result['value_hi']
assert attested == result['interval_provenance_attestation']

def summary(rows):
    counts = {}
    for arm in ['english', 'ainglish']:
        subset = [r for r in rows if r['arm'] == arm]
        tally = Counter()
        for r in subset:
            m = re.fullmatch(r'Obligations discharged: (yes|no); world outcome attained: (yes|no)\.', str(r['answer']))
            assert m
            oracle = by_id[r['item_id']]['oracle']
            discharge, world = (x == 'yes' for x in m.groups())
            tally['discharge_correct'] += discharge == oracle['obligations_discharged']
            tally['world_correct'] += world == oracle['world_success']
            tally['false_discharge'] += discharge and not oracle['obligations_discharged']
            tally['false_non_discharge'] += not discharge and oracle['obligations_discharged']
            tally['false_world_success'] += world and not oracle['world_success']
        counts[arm] = {'n': len(subset), 'exact_correct': sum(r['correct'] is True for r in subset), **tally}
        counts[arm]['accuracy_percent'] = 100 * counts[arm]['exact_correct'] / len(subset) if subset else None
    return counts

groups = {}
for field in ['form', 'exposure', 'framing', 'domain', 'boundary', 'settlement_stratum']:
    groups[field] = {key: summary([r for r in cells if by_id[r['item_id']][field] == key]) for key in sorted({i[field] for i in items})}
groups['reader'] = {r['name']: summary([x for x in cells if x['reader'] == r['name']]) for r in spec['panel']}
groups['form_boundary'] = {form + '/' + boundary: summary([r for r in cells if by_id[r['item_id']]['form'] == form and by_id[r['item_id']]['boundary'] == boundary])
                         for form in ['attempt', 'ensure'] for boundary in sorted({i['boundary'] for i in items})}
form_estimates = {}
for form in ['attempt', 'ensure']:
    subset_items = [i for i in items if i['form'] == form]
    ids = {i['id'] for i in subset_items}
    rows = [r for r in normalized if r[0] in ids]
    sub_spec = dict(spec, settlement_strata=[s for s in spec['settlement_strata'] if s['id'].startswith(form + '-')])
    sub_contract = panel._settlement_contract(sub_spec, subset_items, spec['panel'], spec['seed'])
    sub_value, sub_arms, _ = panel._stratified_accuracy(rows, subset_items, sub_contract)
    sub_lo, sub_hi, _ = panel.attested_bootstrap_accuracy(rows, subset_items, spec['panel'], contract=sub_contract, seed=spec['seed'])
    form_estimates[form] = {'delta_pp': sub_value, 'arms': sub_arms, 'interval_95': [panel._register_round(sub_lo, 4), panel._register_round(sub_hi, 4)]}
audit = {'manifest_hash': result['manifest_hash'], 'official_replay_passed': True, 'target_cells': len(cells),
         'headline': {'value': value, 'arms': arms, 'interval_95': [result['value_lo'], result['value_hi']]},
         'per_form_official_estimates': form_estimates, 'raw_descriptive_counts': groups,
         'limits': 'Prespecified authored diagnostic, two reader families. Subgroup intervals use the same item-bootstrap but no multiplicity or template-cluster correction. Shared definitions, not cold reading. Not an independent replication, a study of real execution success, human validation or evidence of future training benefit. No earlier result or gold is changed.'}
with (OUT / 'analysis.json').open('x') as f:
    json.dump(audit, f, indent=2, ensure_ascii=False)
print(json.dumps({'headline': audit['headline'], 'per_form': form_estimates, 'form_boundary': groups['form_boundary'], 'exposure': groups['exposure'], 'framing': groups['framing']}, indent=2))
