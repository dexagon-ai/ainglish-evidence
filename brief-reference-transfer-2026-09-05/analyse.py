"""Report-only paired transfer analysis, frozen before calls; never submits a metric."""
from collections import Counter, defaultdict
import json
from pathlib import Path
import random
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
ARMS = ('english', 'ainglish')
EXPOSURES = ('cold', 'brief-reference')
SEED = 2026090541


def percentile(values, q):
    ordered = sorted(values)
    p = (len(ordered) - 1) * q
    lo = int(p)
    return ordered[lo] + (ordered[min(lo + 1, len(ordered) - 1)] - ordered[lo]) * (p - lo)


def estimate(cells):
    totals = defaultdict(lambda: [0, 0])
    for cell in cells:
        key = cell['exposure'], cell['form'], cell['arm']
        totals[key][0] += cell['correct']; totals[key][1] += 1
    forms = sorted({c['form'] for c in cells})
    result = {}
    for exposure in EXPOSURES:
        for arm in ARMS:
            pairs = [totals[exposure, form, arm] for form in forms]
            if any(n == 0 for _, n in pairs):
                return None  # Do not silently drop a missing arm/form in a bootstrap draw.
            result[exposure + '.' + arm] = 100 * sum(s / n for s, n in pairs) / len(forms)
        result[exposure + '.delta_pp'] = result[exposure + '.ainglish'] - result[exposure + '.english']
    for arm in ARMS:
        result[arm + '.reference_gain_pp'] = result['brief-reference.' + arm] - result['cold.' + arm]
    result['exposure_contrast_pp'] = result['brief-reference.delta_pp'] - result['cold.delta_pp']
    return result


def intervals(cells, draws=2000):
    clusters = defaultdict(list)
    for cell in cells:
        clusters[cell['cluster']].append(cell)
    keys = sorted(clusters)
    rng = random.Random(SEED)
    estimates = []
    missing = 0
    for _ in range(draws):
        value = estimate([c for key in rng.choices(keys, k=len(keys)) for c in clusters[key]])
        if value is None:
            missing += 1
        else:
            estimates.append(value)
    # No outcome-dependent replacement draw or re-normalising away unavailable bootstrap draws.
    return {'point': estimate(cells), 'clusters': len(keys), 'draws': draws,
            'missing_arm_draws': missing,
            'conditional_95_intervals': None if missing else {
                key: [percentile([d[key] for d in estimates], .025),
                      percentile([d[key] for d in estimates], .975)] for key in estimates[0]}}


def error_labels(name, answer, gold):
    a, g = answer.split('; '), gold.split('; ')
    if name == 'fact-choice':
        return (["existence_confusion"] if a[0] != g[0] else []) + (["resolution_confusion"] if a[1] != g[1] else [])
    labels = []
    if a[0] != g[0]:
        labels.append('permission_expansion' if a[0] == '1: yes' else 'over_restriction')
    if a[1] != g[1]:
        labels.append('forbidden_extra_hop')
    if a[2] != g[2]:
        labels.append('transferred_accountability')
    return labels


def analyse_construct(name):
    cells, observed, pair_keys = [], {}, {}
    error_counts = defaultdict(Counter)
    for exposure in EXPOSURES:
        stem = name + '.' + exposure
        items = {i['id']: i for i in json.loads((ROOT / 'frozen-v2' / (stem + '.items.json')).read_text())}
        path = ROOT / (stem + '.calls.jsonl')
        rows = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
        result_path = ROOT / (stem + '.result.json')
        observed[exposure] = {'calls_retained': len(rows), 'result_retained': result_path.exists(),
            'controls': sum(r['calibration'] for r in rows), 'real': sum(not r['calibration'] for r in rows),
            'faults_or_refusals': sum(bool(r.get('exception_type') or r.get('absent_reason')) for r in rows)}
        pair_keys[exposure] = set()
        for row in rows:
            if row['calibration']:
                continue
            item = items[row['item_id']]
            key = row['reader'], row['item_id'], row['arm']
            assert key not in pair_keys[exposure], 'A duplicate cell must not inflate precision'
            pair_keys[exposure].add(key)
            if row.get('exception_type') or row.get('absent_reason') or row.get('answer') not in item['options']:
                continue
            strata = item['strata']
            cell = {'reader': row['reader'], 'item_id': row['item_id'], 'arm': row['arm'],
                    'exposure': exposure, 'form': item['settlement_stratum'], 'domain': strata['domain'],
                    'cluster': strata['frame_cluster'], 'correct': int(row['answer'] == item['answer'])}
            cells.append(cell)
            error_counts[exposure + '.' + row['arm']].update(error_labels(name, row['answer'], item['answer']))
    complete = all(v['result_retained'] and v['real'] == 512 and not v['faults_or_refusals'] for v in observed.values())
    paired = pair_keys['cold'] == pair_keys['brief-reference'] and len(pair_keys['cold']) == 512
    report = {'observed': observed, 'complete_and_paired': complete and paired,
              'error_classes_can_overlap': True, 'error_counts': dict(error_counts)}
    if not complete or not paired:
        report['interpretation'] = 'Paired exposure contrast unavailable; retain partial/aborted condition, no rerun or imputation.'
        return report
    assert len(cells) == 1024
    report['overall'] = intervals(cells)
    report['forms'] = {f: intervals([c for c in cells if c['form'] == f]) for f in sorted({c['form'] for c in cells})}
    report['domains'] = {d: estimate([c for c in cells if c['domain'] == d]) for d in sorted({c['domain'] for c in cells})}
    report['readers'] = {r: estimate([c for c in cells if c['reader'] == r]) for r in sorted({c['reader'] for c in cells})}
    report['interval_scope'] = 'Authored base-frame clusters, fixed readers; not population-model or future-training uncertainty.'
    return report


def overhead():
    import tiktoken
    guides = json.loads((ROOT / 'frozen-v2' / 'guides.json').read_text())
    with patch('tiktoken.load.read_file', side_effect=RuntimeError('No tokenizer downloads')):
        encodings = {n: tiktoken.get_encoding(n) for n in ('cl100k_base', 'o200k_base', 'p50k_base')}
    return {name: {'words': len(guide.split()), 'utf8_bytes': len(guide.encode()),
                   'reference_encoding_tokens': {n: len(e.encode(guide)) for n, e in encodings.items()},
                   'scope': 'Guide alone, repeated in each reference call; excludes full prompt and is not reader billing.'}
            for name, guide in guides.items()}


def main():
    result = {'report_only': True, 'bootstrap_seed': SEED,
              'constructs': {name: analyse_construct(name) for name in ('fact-choice', 'delegation')},
              'guide_overhead': overhead()}
    with (ROOT / 'analysis.json').open('x') as f:
        json.dump(result, f, indent=2); f.write('\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
