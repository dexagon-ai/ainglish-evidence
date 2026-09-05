"""Independent deterministic audit of generated drafts. No model calls or submissions."""
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parent

def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()

def validate():
    frozen = ROOT / 'frozen'
    index = json.loads((frozen / 'design-index.json').read_text())
    populations = json.loads((frozen / 'populations.json').read_text())
    studies, summary = {}, {}
    for name, design in index.items():
        items = json.loads((frozen / (name + '.items.json')).read_text())
        assert hashlib.sha256(canonical(items)).hexdigest() == design['items_sha256']
        real = [r for r in items if not r.get('calibration')]
        controls = [r for r in items if r.get('calibration')]
        assert len(real) == design['real_items'] and len(controls) == 8
        assert len({r['id'] for r in items}) == len(items)
        assert len({(r['english'], r['ainglish'], r['question']) for r in items}) == len(items)
        assert all(r['answer'] in r['options'] and len(set(r['options'])) == len(r['options']) for r in items)
        for row in controls:
            assert len(row['english']) == len(row['ainglish'])
            assert len(row['english'].split()) == len(row['ainglish'].split())
            assert all(f not in row['english'] + row['ainglish'] for f in ['mean-of', 'median-of', 'verdict-fail', 'no-verdict'])
            assert row['ainglish'].startswith('Only ' + row['answer'] + ' not ')
        for form in {r['settlement_stratum'] for r in real}:
            subset = [r for r in real if r['settlement_stratum'] == form]
            positions = Counter(r['options'].index(r['answer']) for r in subset)
            assert len(positions) == len(subset[0]['options'])
            assert max(positions.values()) - min(positions.values()) <= 1
        if name.startswith('mean'):
            for row in real:
                s = row['strata']; p = populations[s['target_ref']]
                data = [Fraction(x) for x in p['observations']]
                value = statistics.mean(data) if s['form'] == 'mean-of' else statistics.median(data)
                assert Fraction(s['reported_value']) == value
                assert row['english'].rsplit('\nReport: ', 1)[0] == row['ainglish'].rsplit('\nReport: ', 1)[0]
                assert s['form'] + '(' + p['id'] + ') = ' + s['reported_value'] in row['ainglish']
                if name != 'mean.hard':
                    calc = ('add every value and divide by its count' if s['form'] == 'mean-of'
                            else 'sort the values and take the middle (averaging two central values if needed)')
                    assert row['answer'] == calc + '; use ' + p['id']
                    assert s['other_ref'] != p['id'] and s['other_ref'] in row['english']
                else:
                    probe = s['probe']
                    expected = ((sum(x < value for x in data) * 2 > len(data)) if probe == 'above_most' else
                                (any(x == value for x in data)) if probe == 'observed_centre' else probe == 'exact_recheck')
                    assert row['answer'] == ('yes' if expected else 'no')
                    assert s['diagnostic_only'] and s['intentionally_unlicensed'] == (probe in ['weighted', 'approximate', 'categorical'])
        else:
            for row in real:
                s = row['strata']; finding = s['form'] == 'verdict-fail'
                assert row['english'].rsplit('\n', 1)[0] == row['ainglish'].rsplit('\n', 1)[0]
                assert s['anchor'] in row['english'] and s['prior_target_knowledge'] == 'unknown'
                expected = {'target_evidence': ('yes' if finding else 'cannot tell from the available findings'),
                            'first_result': ('no, a target finding is already available' if finding else 'yes, no target finding was obtained'),
                            'failure_object': ('a required property of the target' if finding else 'the checking process before a result'),
                            'prior_knowledge': ('new evidence of a target defect' if finding else 'no new target judgment; it remains unknown')}[s['probe']]
                assert row['answer'] == expected
        studies[name] = real
        summary[name] = {'real_items': len(real), 'controls': 8,
                         'answer_classes': dict(Counter(r['answer'] for r in real)) if name == 'mean.hard' else 'joint gold checked item by item',
                         'status': 'passed'}
    for a, b in [('mean.careful', 'mean.practical'), ('verdict.careful', 'verdict.bare')]:
        for left, right in zip(studies[a], studies[b]):
            assert all(left[k] == right[k] for k in ['id', 'ainglish', 'question', 'answer', 'options', 'strata'])
            assert left['english'] != right['english']
    # Full text+question overlap, not the cosmetic novelty of IDs. Matched comparisons in
    # THIS design deliberately reuse frames, whereas older campaigns are not fresh evidence.
    prior = set()
    for folder in ['brief-reference-transfer-2026-09-05', 'progression-studies-2026-09-05', 'progression-campaign-2026-09-05']:
        for path in (ROOT.parent / folder).rglob('*.items.json'):
            data = json.loads(path.read_text())
            for r in data if isinstance(data, list) else []:
                if all(k in r for k in ['english', 'ainglish', 'question']):
                    prior.add((r['english'], r['ainglish'], r['question']))
    assert not prior.intersection((r['english'], r['ainglish'], r['question']) for rows in studies.values() for r in rows)
    return {'studies': summary, 'prior_complete_items_checked': len(prior), 'model_calls': 0,
            'limitations': ['Matched comparisons are related, not independent replications.',
                'Hard diagnostics are intentionally class-imbalanced; report probe and absolute arm accuracy.',
                'Categorical/approximate/weighted probes state adversarial context overrides, not valid numeric claims.',
                'No bare-average hidden-intent gold and no full normative-completion claim.']}

if __name__ == '__main__':
    result = validate()
    with (ROOT / 'design-audit.json').open('x') as f:
        json.dump(result, f, indent=2); f.write('\n')
    print(json.dumps(result, indent=2))
