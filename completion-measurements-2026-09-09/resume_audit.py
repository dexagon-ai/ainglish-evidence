"""Post-run deterministic audit and descriptive breakdown; no inference or new evidence."""
import hashlib
import json
import re
from collections import Counter
from ainglish import panel
from reader_campaign import ROOT, load, save

OUT = ROOT / 'resume-comprehension'


def core_gold(item):
    """Derive the key from complete English facts, without importing the renderer."""
    common, directive = item['english'].rsplit('. ', 1)
    marked_common, marked = item['ainglish'].rsplit('. ', 1)
    assert common == marked_common
    units = re.search(r'consists of the four \w+ (.*?), in that order', common).group(1).split(', ')
    completed = re.search(r'previously completed: (.*?)\.', common).group(1)
    completed = [] if completed == 'none' else completed.split(', ')
    assert completed == units[:len(completed)]
    next_unit = re.search(r'next unfinished unit is (\w+)\.', common).group(1)
    assert next_unit == units[len(completed)]
    target, condition = re.search(r'if and only if (\w+) is (performed|left unperformed) during', common).groups()
    assert target in units
    if ', continuing from checkpoint ' in directive:
        action, checkpoint = directive.removesuffix('.').split(', continuing from checkpoint ')
        assert 'Saved record ' + checkpoint + ' belongs to this exact task/version' in common
        assert marked == action + ', resume-from(' + checkpoint + ').'
        will_perform = target in units[len(completed):]
    else:
        assert directive.endswith(' again from the beginning.')
        action = directive.removesuffix(' again from the beginning.')
        assert marked == action + ', redo-from-start.'
        will_perform = target in units
    return 'Yes' if will_perform == (condition == 'performed') else 'No'


def run():
    items = [i for i in load(OUT / 'items.json') if not i.get('calibration')]
    key = {i['id']: i for i in items}
    cell_path = next(p for p in (OUT / 'execution').glob('*.cells.json') if '.calibration.' not in p.name)
    cells = load(cell_path)['rows']
    assert len(cells) == 160 and len(items) == 80
    core = [i for i in items if i['settlement_stratum'] != 'boundary']
    assert len(core) == 64
    assert all(core_gold(i) == i['answer'] for i in core)

    journal = [json.loads(line) for line in (OUT / 'execution/journal.jsonl').read_text().splitlines()]
    begins = [x for x in journal if x['event'] == 'begin' and x['ordinal'] > 32]
    ends = {x['ordinal']: x for x in journal if x['event'] == 'end'}
    assert len(begins) == len(cells)
    for begin, cell in zip(begins, cells):
        item = key[cell['item_id']]
        assert begin['reader'] == cell['reader']
        assert begin['prompt'].split('\n---\n')[1] == item[cell['arm']]
        choices = dict(re.findall(r'^([A-Z]): (.*)$', begin['prompt'], re.M))
        raw = ends[begin['ordinal']]['raw'].strip()
        assert raw in choices and choices[raw] == cell['answer']
        assert cell['expected'] == item['answer']
        assert cell['correct'] == (cell['answer'] == item['answer'])

    groups = {'all': items}
    for stratum in ('resume-core', 'redo-core', 'boundary'):
        groups[stratum] = [i for i in items if i['settlement_stratum'] == stratum]
    for form in ('resume', 'redo'):
        for domain in ('reading', 'review', 'media', 'simulated-workflow'):
            groups[form + '/' + domain] = [i for i in core if i['strata']['form'] == form and i['strata']['domain'] == domain]

    report = {}
    for group, group_items in groups.items():
        ids = {i['id'] for i in group_items}
        selected = [r for r in cells if r['item_id'] in ids]
        tuples = [(r['item_id'], r['arm'], r['reader'], r['answer']) for r in selected]
        arms = {}
        for arm in ('english', 'ainglish'):
            arm_rows = [r for r in selected if r['arm'] == arm]
            arms[arm] = {'correct': sum(r['correct'] for r in arm_rows), 'total': len(arm_rows)}
            arms[arm]['accuracy'] = arms[arm]['correct'] / arms[arm]['total']
        seed = int(hashlib.sha256(('resume-descriptive:' + group).encode()).hexdigest()[:12], 16)
        lo, hi = panel.bootstrap_delta(tuples, group_items, 'comprehension_accuracy_delta', n=2000, seed=seed)
        report[group] = {'items': len(group_items), 'arms': arms,
            'delta_pp': 100 * (arms['ainglish']['accuracy'] - arms['english']['accuracy']),
            'descriptive_item_bootstrap_95': [lo, hi],
            'answer_codes': dict(Counter(chr(65 + i['options'].index(i['answer'])) for i in group_items)),
            'answer_values': dict(Counter(i['answer'] for i in group_items)),
            'always_A_accuracy': sum(i['answer'] == i['options'][0] for i in group_items) / len(group_items)}

    save(OUT / 'post-run-audit.json', {
        'kind': 'ainglish.post-run-instrument-audit.v1',
        'measurement': load(OUT / 'measurement-after.json')['manifest_hash'],
        'scientific_calls_added': 0, 'core_gold_and_literal_comparator_checks': 64,
        'raw_choice_decoding_and_cell_scoring_checks': 160,
        'descriptive_groups': report,
        'limits': [
            'The original frozen weighted aggregate, intervals, golds and filed measurement are unchanged.',
            'The all group below is an unweighted row aggregate, not the official stratum-weighted headline.',
            'Subgroup intervals were calculated after the run for description, are not simultaneous or multiplicity-adjusted, and do not create new settlement tests.',
            'Item bootstrap retains both observed readers per sampled item, but does not account for related renderers or paired indicator-question templates.',
            'Only two fixed present-day readers, not independent model samples or humans. The boundary has eight semantic conditions repeated twice.',
            'Answer values are balanced, but response codes are not: always A wins every redo-core item. This is a deterministic instrument baseline, not observed model accuracy.',
            'Task identifiers expose the policy name in both arms. A future neutral-identifier design would be a new diagnostic, not a hidden edit or exact replication.',
            'Low accuracy on both complete-English and marked arms does not establish a reliable language advantage or intrinsic unlearnability.',
        ]})
    print(json.dumps({'gold_checks': 64, 'cell_checks': 160,
                      'always_A': {k: v['always_A_accuracy'] for k, v in report.items() if '/' not in k}}, indent=2))


if __name__ == '__main__':
    run()
