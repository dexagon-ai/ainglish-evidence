"""Prospectively frozen report-only frame-cluster analysis. Never files a measurement."""
from collections import Counter, defaultdict
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parent
STEMS = ['mean.careful', 'verdict.careful', 'mean.practical', 'verdict.bare', 'mean.hard']
SEED = 2026090567

def estimate(cells):
    bins = defaultdict(lambda: [0, 0])
    for c in cells:
        bins[c['form'], c['arm']][0] += c['correct']; bins[c['form'], c['arm']][1] += 1
    forms = sorted({c['form'] for c in cells})
    if not forms or any(not bins[f, a][1] for f in forms for a in ['english', 'ainglish']):
        return None
    result = {a: 100*sum(bins[f, a][0]/bins[f, a][1] for f in forms)/len(forms) for a in ['english', 'ainglish']}
    result['delta_pp'] = result['ainglish'] - result['english']
    return result

def percentile(values, q):
    values = sorted(values); index = (len(values)-1)*q; lo = int(index)
    return values[lo] + (values[min(lo+1, len(values)-1)]-values[lo])*(index-lo)

def intervals(cells):
    clusters = defaultdict(list)
    for c in cells:
        clusters[c['cluster']].append(c)
    keys = sorted(clusters); rng = random.Random(SEED)
    draws = [estimate([c for k in rng.choices(keys, k=len(keys)) for c in clusters[k]]) for _ in range(2000)]
    missing = sum(d is None for d in draws)
    return {'point': estimate(cells), 'clusters': len(keys), 'draws': 2000, 'missing_arm_draws': missing,
            'conditional_95_intervals': None if missing else {
                k: [percentile([d[k] for d in draws], .025), percentile([d[k] for d in draws], .975)] for k in draws[0]}}

def read(stem):
    items = {r['id']: r for r in json.loads((ROOT / 'frozen' / (stem+'.items.json')).read_text())}
    path = ROOT / (stem+'.calls.jsonl')
    rows = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    cells, seen, errors = [], set(), defaultdict(Counter)
    invalid = 0
    for r in rows:
        item = items[r['item_id']]; key = r['reader'], r['item_id'], r['arm']
        assert key not in seen, 'Duplicate reader/item/arm cell'; seen.add(key)
        bad = bool(r.get('exception_type') or r.get('absent_reason') or r.get('answer') not in item['options'])
        invalid += int(bad)
        if r['calibration'] or bad:
            continue
        s = item['strata']
        cells.append({'item_id': r['item_id'], 'reader': r['reader'], 'arm': r['arm'], 'form': item['settlement_stratum'],
                      'domain': s['domain'], 'cluster': s['frame_cluster'], 'correct': int(r['answer'].lower() == item['answer'].lower()),
                      'probe': s.get('probe'), 'family': s.get('family')})
        if stem in ['mean.careful', 'mean.practical']:
            answer, gold = r['answer'].split('; use '), item['answer'].split('; use ')
            if answer[0] != gold[0]: errors[r['arm']]['statistic_confusion'] += 1
            if answer[1] != gold[1]: errors[r['arm']]['population_binding_error'] += 1
    expected = 2*sum(not r.get('calibration') for r in items.values())
    complete = (ROOT / (stem+'.result.json')).exists() and len(cells) == expected and invalid == 0
    report = {'calls_retained': len(rows), 'scientific_cells': len(cells), 'invalid_cells': invalid,
              'complete': complete, 'error_counts_can_overlap': dict(errors)}
    if not complete:
        report['interpretation'] = 'No complete admitted estimate; preserve the abort or partial journal, no imputation or retry.'
        return report, None
    report['overall'] = intervals(cells)
    report['forms'] = {f: intervals([c for c in cells if c['form'] == f]) for f in sorted({c['form'] for c in cells})}
    for key in ['domain', 'reader', 'probe', 'family']:
        report[key] = {v: estimate([c for c in cells if c[key] == v]) for v in sorted({c[key] for c in cells if c[key] is not None})}
    report['per_form_ni_established'] = all(v['conditional_95_intervals'] and v['conditional_95_intervals']['delta_pp'][0] >= -5 for v in report['forms'].values())
    report['sdk_filed_result'] = json.loads((ROOT / (stem+'.result.json')).read_text())['value']
    assert abs(report['overall']['point']['delta_pp'] - report['sdk_filed_result']) <= .02, 'Report and official equal-form estimator disagree'
    return report, cells

def main():
    reports, cells = {}, {}
    for stem in STEMS:
        reports[stem], cells[stem] = read(stem)
    paired = {}
    for a, b in [('mean.careful', 'mean.practical'), ('verdict.careful', 'verdict.bare')]:
        key = a+' vs '+b
        if cells[a] is None or cells[b] is None:
            paired[key] = {'available': False}; continue
        identity = lambda rows: {(r['reader'], r['item_id'], r['arm']) for r in rows}
        assert identity(cells[a]) == identity(cells[b]), 'Unmatched assignment; no paired comparison'
        # This contrast is descriptive, not a new filed metric or an independent replication.
        paired[key] = {'available': True, 'second_minus_first_delta_pp': estimate(cells[b])['delta_pp']-estimate(cells[a])['delta_pp'],
                       'scope': 'Matched fixed cases/readers; the complete comparison determines the primary claim.'}
    result = {'report_only': True, 'studies': reports, 'paired_comparisons': paired,
              'interval_scope': 'Fixed readers and authored base-frame population; not all models, humans or future training.',
              'hard_diagnostics': 'Report absolute accuracy and each probe; class imbalance and invalid assertions preclude pooling as a primary benefit.'}
    with (ROOT / 'analysis.json').open('x') as f:
        json.dump(result, f, indent=2); f.write('\n')
    print(json.dumps({s: {'complete': r['complete'], 'point': r.get('overall', {}).get('point')} for s, r in reports.items()}, indent=2))

if __name__ == '__main__':
    main()
