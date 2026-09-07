"""Post-hoc output-shape explanation, never a replacement for frozen scores."""
import json
from study import ROOT, Journal


def main():
    result = json.loads((ROOT / 'RESULTS.json').read_text())
    cases = {c['id']: c for c in json.loads((ROOT.parent / 'communication-diagnostics-2026-09-06/cases.json').read_text())}
    events = Journal._validate((ROOT / 'execution/reader-2.jsonl').read_text())
    ends = {r['data']['call_id']: r['data'] for r in events if r['kind'] == 'end'}
    rows = []
    for model in result['models']:
        for row in model['targets']:
            if row['dimensions'] != 2:
                continue
            raw = ends[row['id'] + '/' + row['arm']]['raw'].strip()
            if raw.startswith('```json\n') and raw.endswith('\n```'):
                raw = raw[len('```json\n'):-len('\n```')]
            pairs = json.loads(raw, object_pairs_hook=lambda x: x)
            assert isinstance(pairs, list) and all(isinstance(p, tuple) and len(p) == 2 for p in pairs)
            value = dict(pairs)
            assert len(value) == len(pairs), 'Duplicate keys require separate investigation'
            gold = cases[row['id']]['brief']
            rows.append({'id': row['id'], 'arm': row['arm'], 'frozen_correct': row['correct'],
                'extra_keys': sorted(set(value) - set(gold)), 'missing_keys': sorted(set(gold) - set(value)),
                'requested_values_correct': all(type(value.get(k)) is bool and value[k] == expected for k, expected in gold.items())})
    assert len(rows) == 24
    report = {'kind': 'ainglish.posthoc-reader-shape-audit.v1', 'post_hoc': True,
        'changes_frozen_scores': False, 'new_calls': 0,
        'summary': [{'arm': arm, 'n': sum(r['arm'] == arm for r in rows),
            'with_extra_keys': sum(r['arm'] == arm and bool(r['extra_keys']) for r in rows),
            'requested_values_correct': sum(r['arm'] == arm and r['requested_values_correct'] for r in rows)}
            for arm in ('ainglish', 'english')], 'rows': rows,
        'boundary': 'Requested-field projection was not the declared score. All 24 two-field objects still fail the frozen exact-key protocol. This audit diagnoses the refusal; it does not turn those results into passes or unlock another experiment.'}
    (ROOT / 'SHAPE-AUDIT.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report['summary'], indent=2))


if __name__ == '__main__':
    main()
