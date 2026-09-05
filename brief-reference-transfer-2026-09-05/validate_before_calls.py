"""Pure synthetic scorer/assignment checks. No real reader, attempt or registry write."""
from collections import Counter
import contextlib
import hashlib
import io
import json
from pathlib import Path
import subprocess
from ainglish import panel
from analyse import error_labels, estimate, intervals
from build import canonical

ROOT = Path(__file__).resolve().parent


def main():
    reports = []
    for name in ('fact-choice', 'delegation'):
        reference = json.loads((ROOT / 'frozen-v2' / (name + '.brief-reference.items.json')).read_text())
        cold = json.loads((ROOT / 'frozen-v2' / (name + '.cold.items.json')).read_text())
        assert len(reference) == len(cold) == 264
        for left, right in zip(cold, reference):
            assert {k: v for k, v in left.items() if k not in ('english', 'ainglish')} == {k: v for k, v in right.items() if k not in ('english', 'ainglish')}
            assert right['english'].endswith(left['english']) and right['ainglish'].endswith(left['ainglish'])
            assert right['english'][:-len(left['english'])] == right['ainglish'][:-len(left['ainglish'])]
        synthetic_cells = []
        for exposure, items in [('cold', cold), ('brief-reference', reference)]:
            spec = json.loads((ROOT / (name + '.' + exposure + '.runspec.json')).read_text())
            assert hashlib.sha256(canonical(items)).hexdigest() == spec['items_sha256']
            commit = spec['attempt']['planned_sample']['source_commit']
            source = subprocess.run(['git', '-C', str(ROOT.parent), 'show', commit + ':' + ROOT.name + '/frozen-v2/' + name + '.' + exposure + '.items.json'], check=True, capture_output=True).stdout
            assert source == (ROOT / 'frozen-v2' / (name + '.' + exposure + '.items.json')).read_bytes()
            gold = {(r[arm], r['question']): ('the information does not determine who' if r.get('calibration') and arm == 'english' else r['answer']) for r in items for arm in ('english', 'ainglish')}
            calls = []
            def oracle(reader, text, question, options):
                answer = gold[text, question]
                assert answer in options
                calls.append(1)
                return answer
            manifest = dict(spec, items=items, _dry_run=True)
            with contextlib.redirect_stdout(io.StringIO()):
                result = panel.run_panel(manifest, ask_fn=oracle)
            assert result and not panel._is_panel_refusal(result), result
            assert result['value'] == 0 and result['arms']['english'] == result['arms']['ainglish'] == 1
            assert len(calls) == 544
            for form in (r['id'] for r in spec['settlement_strata']):
                selected = [i for i in items if i.get('settlement_stratum') == form]
                positions = Counter(i['options'].index(i['answer']) for i in selected)
                assert max(positions.values()) - min(positions.values()) <= 1
            for item in items:
                if item.get('calibration'):
                    continue
                for reader in spec['panel']:
                    arm = panel.arm_for(spec['seed'], reader['name'], item['id'])
                    synthetic_cells.append({'exposure': exposure, 'form': item['settlement_stratum'],
                        'arm': arm, 'cluster': item['strata']['frame_cluster'], 'correct': 1})
            reports.append({'condition': name + '.' + exposure, 'synthetic_calls': len(calls), 'actual_reader_calls': 0, 'source_bytes_verified': True, 'scorer_value': result['value']})
        assert estimate(synthetic_cells)['exposure_contrast_pp'] == 0
        perfect = intervals(synthetic_cells, draws=40)
        assert perfect['conditional_95_intervals']['exposure_contrast_pp'] == [0, 0]
        degraded = [dict(c, correct=int(not (c['exposure'] == 'cold' and c['arm'] == 'ainglish'))) for c in synthetic_cells]
        assert estimate(degraded)['exposure_contrast_pp'] == 100
    assert error_labels('fact-choice', '1: no; 2: finding out', '1: yes; 2: finding out') == ['existence_confusion']
    assert error_labels('delegation', '1: yes; 2: yes; 3: the external helper', '1: no; 2: no; 3: the original principal or team') == ['permission_expansion', 'forbidden_extra_hop', 'transferred_accountability']
    with (ROOT / 'pre-call-validation.json').open('x') as f:
        json.dump({'synthetic_not_evidence': True, 'checks': reports}, f, indent=2); f.write('\n')
    print('All source, comparator, assignment, option-position, scorer and paired-analysis checks passed; zero reader calls.')


if __name__ == '__main__':
    main()
