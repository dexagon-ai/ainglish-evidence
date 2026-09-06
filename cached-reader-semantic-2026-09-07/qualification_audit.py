"""Post-hoc explanation of the completed neutral screens, never gate replacement.

No inference calls or scoring of language target answers. The successor's
predeclared single-fence decoder is applied to the predecessor for diagnosis
only; the predecessor's frozen failure decisions stay unchanged.
"""
import json
from pathlib import Path
from study import decode_json

ROOT = Path(__file__).resolve().parent


def main():
    rows = []
    for folder in ['cached-reader-diagnostic-2026-09-07', ROOT.name]:
        path = ROOT.parent / folder
        controls = {c['id']: c for c in json.loads((path / 'controls.json').read_text())}
        for index in range(3):
            qualification = json.loads((path / f'execution/qualification-{index}.json').read_text())
            events = [json.loads(line) for line in (path / f'execution/reader-{index}.jsonl').read_text().splitlines()]
            ends = [e['data'] for e in events if e['kind'] == 'end' and e['data']['call_id'].startswith('control/')]
            assert len(ends) == 16 and len({e['call_id'] for e in ends}) == 16
            cells = []
            for end in ends:
                key = end['call_id'].split('/', 1)[1]
                gold = controls[key]['gold']
                value = decode_json(end['raw'], gold)
                cells.append({'id': key, 'parsed_with_single_fence_protocol': value is not None,
                    'joint_correct_with_single_fence_protocol': value == gold,
                    'wrong_fields': [k for k in gold if value[k] != gold[k]] if value is not None else None,
                    'truncated': end['response'].get('done_reason') != 'stop'})
            rows.append({'study': folder, 'model': qualification['model'], 'cells': cells,
                'frozen_correct': sum(c['correct'] for c in qualification['qualification']),
                'frozen_qualified': qualification['qualified'],
                'wrapper_aware_parsed': sum(c['parsed_with_single_fence_protocol'] for c in cells),
                'wrapper_aware_correct': sum(c['joint_correct_with_single_fence_protocol'] for c in cells),
                'field_errors': {k: sum(c['wrong_fields'] is not None and k in c['wrong_fields'] for c in cells)
                    for k in next(iter(controls.values()))['gold']}})
    output = {'kind': 'ainglish.neutral-screen-posthoc-audit.v1', 'governance_evidence': False,
        'decision_effect': 'None. Frozen qualification failures remain failures; no retroactive language target permission.',
        'comparison_limit': 'Both the neutral vocabulary and the declared wrapper protocol changed prospectively. This is not a controlled causal estimate of the wrapper alone.',
        'rows': rows}
    (ROOT / 'QUALIFICATION-AUDIT.json').write_text(json.dumps(output, indent=2) + '\n')
    print('Six completed neutral screens explained; no language target answers scored or gate changed.')


if __name__ == '__main__':
    main()
