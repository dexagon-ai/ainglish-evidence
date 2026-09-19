"""Exercise the real SDK planner with CPU fixtures; retain no synthetic measurement.

The fixture is intentionally marked dry-run and all network/model entry points
are blocked. Only the executed assignment schedule is returned, never answers,
scores, calibration claims, or an uploadable measurement.
"""
import contextlib
import io
import json
from collections import Counter, defaultdict
from importlib.metadata import version
from unittest.mock import patch

import prepare as p


def runner_assignments(bank):
    from ainglish import panel
    source = json.loads((p.SOURCE.parent / 'measurement.json').read_text())['manifest']
    endpoints = [{key: value for key, value in reader.items()
                  if value != 'provider-default' and key != 'instrument_preparation'}
                 for reader in source['readers']]
    manifest = {
        '_dry_run': True, 'slug': 'cpu-fixture-not-a-measurement',
        'metric': 'comprehension_accuracy_delta', 'seed': bank['seed'],
        'items': bank['items'], 'panel': endpoints,
        'comparator': source['comparator'], 'panel_neff': 1,
        'calibration_min_gap': 0.5, 'calibration_min_recovered': 1,
        'settlement_strata': source['settlement_strata'],
        'settlement_item_field': source['settlement_item_field'],
    }
    texts = {item[arm]: (item, arm) for item in bank['items'] for arm in ('english', 'ainglish')}
    assert len(texts) == 2 * len(bank['items'])
    observed = []

    def fixture(endpoint, text, question, options):
        item, arm = texts[text]
        assert question == item['question'] and options == item['options']
        observed.append({'reader': endpoint['name'], 'item_id': item['id'],
                         'arm': arm, 'calibration': bool(item.get('calibration'))})
        return 'not specified' if item.get('calibration') and arm == 'english' else item['answer']

    with patch('socket.socket', side_effect=AssertionError('No network allowed in CPU fixture')), \
            patch.object(panel, 'chat', side_effect=AssertionError('No model allowed in CPU fixture')), \
            contextlib.redirect_stdout(io.StringIO()):
        result = panel.run_panel(manifest, ask_fn=fixture)
    assert result is not None, 'Official run_panel refused this fixture; assignments not verified'
    assert 'DRY-RUN' in result['manifest']['protocol']
    # Discard all fabricated outcomes. Nothing returned below is scientific evidence.
    del result
    return observed


def report(bank, observed):
    real = {item['id']: item for item in bank['items'] if not item.get('calibration')}
    scientific = [row for row in observed if not row['calibration']]
    calibration = [row for row in observed if row['calibration']]
    assert len(scientific) == 192 and len(calibration) == 48
    exposure = defaultdict(Counter)
    gold = defaultdict(Counter)
    by_item = defaultdict(set)
    for row in scientific:
        item = real[row['item_id']]
        key = '/'.join((row['reader'], item['anchor_class'], item['frame']))
        exposure[key][row['arm']] += 1
        gold[key + '/' + row['arm']][item['options'].index(item['answer']) + 1] += 1
        by_item[item['id']].add(row['arm'])
    planned = p.audit(bank)['assignment_plan']
    planned_cells = {(row['reader'], row['item_id']): row['arm'] for row in planned}
    actual_cells = {(row['reader'], row['item_id']): row['arm'] for row in scientific}
    assert actual_cells == planned_cells, 'The actual SDK schedule differs from the candidate plan'
    assert len(exposure) == 32 and all(counts == {'english': 3, 'ainglish': 3} for counts in exposure.values())
    assert len(gold) == 64 and all(counts == {1: 1, 2: 1, 3: 1} for counts in gold.values())
    assert len(by_item) == 96 and all(arms == {'english', 'ainglish'} for arms in by_item.values())
    return {
        'kind': 'dexagon.sdk-runner-assignment-fixture.v1',
        'status': 'cpu_fixture_not_measurement', 'sdk_version': version('ainglish'),
        'entry_point': 'ainglish.panel.run_panel', 'assignment_key': 'panel[].name',
        'items_sha256': bank['sha256'], 'network_calls': 0, 'reader_calls': 0,
        'synthetic_scientific_calls': len(scientific), 'synthetic_calibration_calls': len(calibration),
        'actual_plan_disagreements': 0, 'balanced_reader_anchor_frame_blocks': 32,
        'balanced_gold_position_blocks': 64, 'opposite_arm_items': 96,
        'assignment_plan': scientific,
    }


if __name__ == '__main__':
    bank = p.make_bank()
    result = report(bank, runner_assignments(bank))
    (p.ROOT / 'runner-assignment-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'assignment_plan'}))
