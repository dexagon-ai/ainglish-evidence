"""Replay the five frozen studies; no network, inference, reruns or re-scoring."""
from collections import Counter
import json
import math
from pathlib import Path
import re
from ainglish import panel
from ainglish.client import manifest_commitment

ROOT = Path(__file__).resolve().parent
STUDIES = ['outcome-careful', 'outcome-compact', 'outcome-majority-careful', 'outcome-majority-compact', 'outcome-specification']

def nominal_wilson(k, n):
    if not n:
        return None
    z = 1.959963984540054
    centre = (k/n + z*z/(2*n)) / (1 + z*z/n)
    radius = z * math.sqrt(k/n*(1-k/n)/n + z*z/(4*n*n)) / (1+z*z/n)
    return [round(100*(centre-radius), 4), round(100*(centre+radius), 4)]

def analyze(name):
    folder = ROOT / name
    out = folder / 'execution'
    spec = json.loads((folder / 'runspec.json').read_text())
    filed = json.loads((out / 'measurement-after.json').read_text())
    files = [p for p in out.glob('*.cells.json') if '.calibration.' not in p.name]
    assert len(files) == 1
    cells = json.loads(files[0].read_text())['rows']
    items = [i for i in spec['items'] if not i.get('calibration')]
    by_id = {i['id']: i for i in items}
    assert Counter((r['item_id'], r['reader']) for r in cells) == Counter((i['id'], r['name']) for i in items for r in spec['panel'])
    normalized = []
    for row in cells:
        gold = by_id[row['item_id']]['answer']
        assert row['expected'] == gold
        assert row['arm'] == panel.arm_for(spec['seed'], row['reader'], row['item_id'])
        assert row['correct'] == (None if panel.is_absent(row['answer']) else str(row['answer']).casefold() == gold.casefold())
        normalized.append((row['item_id'], row['arm'], row['reader'], row['answer']))
    assert manifest_commitment(filed['manifest']) == manifest_commitment(json.loads((folder / 'planned-manifest.json').read_text()))
    contract = panel._settlement_contract(spec, items, spec['panel'], spec['seed'])
    value, arms, strata = panel._stratified_accuracy(normalized, items, contract)
    assert value == filed['value'] and arms == filed['arms']
    for actual, saved in zip(strata, filed['stratum_results']):
        assert all(actual[k] == saved[k] for k in ('id', 'value', 'arms'))
    lo, hi, attestation = panel.attested_bootstrap_accuracy(normalized, items, spec['panel'], contract=contract, seed=spec['seed'])
    assert panel._register_round(lo, 4) == filed['value_lo']
    assert panel._register_round(hi, 4) == filed['value_hi']
    assert attestation == filed['interval_provenance_attestation']

    def summary(rows):
        groups = {}
        for arm in ('english', 'ainglish'):
            subset = [r for r in rows if r['arm'] == arm]
            counts = Counter()
            for row in subset:
                answer = row['answer']
                counts['exact_correct'] += row['correct'] is True
                if panel.is_absent(answer):
                    counts['absent'] += 1
                    continue
                if name in ('outcome-careful', 'outcome-compact'):
                    parsed = re.fullmatch(r'Claim true: (yes|no); x possible: (yes|no); x unique most probable: (yes|no); next result guaranteed x: (yes|no)\.', answer)
                    assert parsed, answer
                    predicted = [x == 'yes' for x in parsed.groups()]
                    gold = by_id[row['item_id']]['oracle']['flags']
                    for label, actual, expected in zip(['truth', 'possible', 'unique_mode', 'guarantee'], predicted, gold):
                        counts[label + '_correct'] += actual == expected
                    counts['false_guarantee'] += predicted[3] and not gold[3]
                elif name.startswith('outcome-majority-'):
                    parsed = re.fullmatch(r'Under D, probability of x exceeds one half: (yes|no); statement certifies that D models reality correctly: (yes|no)\.', answer)
                    assert parsed, answer
                    majority, certification = (x == 'yes' for x in parsed.groups())
                    oracle = by_id[row['item_id']]['oracle']
                    counts['majority_correct'] += majority == oracle['majority']
                    counts['certification_correct'] += certification == oracle['certifies_model']
                    counts['false_certification'] += certification and not oracle['certifies_model']
                else:
                    sufficient = answer == 'Enough specification to check the claim, even if it is false.'
                    assert sufficient or answer == 'Clarify or reject the specification before evaluating this registered claim.'
                    gold = by_id[row['item_id']]['oracle']['specification_sufficient']
                    counts['false_sufficient'] += sufficient and not gold
                    counts['false_rejection'] += not sufficient and gold
            n = len(subset)
            groups[arm] = {'n': n, **dict(counts), 'exact_correct': counts['exact_correct'],
                           'exact_accuracy_percent': round(100*counts['exact_correct']/n, 4) if n else None,
                           'nominal_cell_wilson_95': {key: nominal_wilson(k,n) for key,k in counts.items() if key in ('exact_correct', 'false_guarantee', 'false_certification')},
                           'uncertainty_limit': 'Nominal cell-Wilson intervals are descriptive, not corrected for shared templates/items/readers; they cannot certify a population threshold.'}
        return groups

    groups = {}
    for field in ('settlement_stratum', 'domain', 'boundary', 'variant', 'diagnostic_class'):
        if all(field in item for item in items):
            groups[field] = {str(key): summary([r for r in cells if by_id[r['item_id']][field] == key]) for key in sorted({i[field] for i in items})}
    groups['reader'] = {reader['name']: summary([r for r in cells if r['reader'] == reader['name']]) for reader in spec['panel']}
    per_form = {}
    for form in sorted({i['settlement_stratum'] for i in items}):
        selected = [i for i in items if i['settlement_stratum'] == form]
        ids = {i['id'] for i in selected}
        rows = [r for r in normalized if r[0] in ids]
        sub_spec = dict(spec, settlement_strata=[s for s in spec['settlement_strata'] if s['id'] == form])
        sub_contract = panel._settlement_contract(sub_spec, selected, spec['panel'], spec['seed'])
        sub_value, sub_arms, _ = panel._stratified_accuracy(rows, selected, sub_contract)
        lower, upper, _ = panel.attested_bootstrap_accuracy(rows, selected, spec['panel'], contract=sub_contract, seed=spec['seed'])
        per_form[form] = {'delta_pp': sub_value, 'arms': sub_arms,
                          'item_bootstrap_95': [panel._register_round(lower,4), panel._register_round(upper,4)],
                          'lower_bound_exceeds_minus_3': lower > -3,
                          'ainglish_point_at_least_90_percent': sub_arms['ainglish'] >= .9,
                          'ainglish_point_below_85_percent': sub_arms['ainglish'] < .85,
                          'confirmatory_threshold_pass': False,
                          'boundary': 'Separate descriptive predicate analysis; no multiplicity/template-cluster correction or independent experimental confirmation.'}
    journal = [json.loads(line) for line in (out / 'execution-journal.jsonl').read_text().splitlines()]
    assert journal[-1]['event'] == 'finished'
    assert len([row for row in journal if row['event'] == 'begin']) == journal[-1]['calls']
    assert len([row for row in journal if row['event'] == 'end']) == journal[-1]['calls']
    assert not any(row['event'] == 'fault' for row in journal)
    return {'study': name, 'manifest_hash': filed['manifest_hash'], 'attempt_id': filed['attempt_id'],
            'official_replay_passed': True, 'target_items': len(items), 'target_calls': len(cells),
            'calibration_calls': journal[-1]['calls']-len(cells), 'all_calls': journal[-1]['calls'],
            'headline': {'value': value, 'interval_95': [filed['value_lo'], filed['value_hi']], 'arms': arms, 'resolution_bound': filed['resolution_bound']},
            'per_form': per_form, 'raw_counts': summary(cells), 'groups': groups,
            'constant_answer_baseline_percent': 50 if name in ('outcome-careful','outcome-compact') else 75 if name == 'outcome-specification' else 80,
            'limits': ['Frozen shared-definition experiments, not cold comprehension or trained weights.',
                       'Repeated templates and shared worlds are not independent scenario populations.',
                       'The three supplements cannot replace or be pooled into the primary result.',
                       'All guarantee and certification keys are no under supplied cautions; general false-guarantee discrimination is untested.',
                       'Two cached reader families, not humans, broader models or independent confirmation.']}

if __name__ == '__main__':
    results = []
    for name in STUDIES:
        result = analyze(name)
        target = ROOT / name / 'execution' / 'analysis.json'
        if target.exists():
            assert json.loads(target.read_text()) == result
        else:
            with target.open('x') as stream:
                json.dump(result, stream, indent=2, ensure_ascii=False)
        results.append(result)
        print(json.dumps({key: result[key] for key in ('study','official_replay_passed','all_calls','headline','per_form','raw_counts')}, indent=2), flush=True)
    print('Total recorded calls:', sum(result['all_calls'] for result in results))
