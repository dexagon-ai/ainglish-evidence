"""Prospective supplementary analysis for the exact final package; never files evidence.

Preserves the original diagnostic report and official statistic. Adds explicitly separate
equal-reader within-reader contrasts and world/frame-cluster sensitivities. No model calls.
"""
from collections import defaultdict
import argparse
import hashlib
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent / 'choose-any-completion-2026-09-14/fresh-bank-v2'
sys.path.insert(0, str(OLD))
import report

FORMS = ('choose-any', 'draw-uniform')
READERS = ('gemma3-12b-opaque-choice-q4_k_m', 'mistral-small3.2-24b-opaque-choice-q4_k_m')


def equal_reader_contrast(rows, form=None):
    cells = defaultdict(lambda: [0, 0])
    for r in rows:
        if r.get('absent'):
            continue
        key = (r['form'], r['reader'], r['arm'])
        cells[key][0] += int(r['joint'])
        cells[key][1] += 1
    deltas = []
    for f in (FORMS if form is None else (form,)):
        for reader in READERS:
            a, e = cells[f, reader, 'ainglish'], cells[f, reader, 'english']
            if not a[1] or not e[1]:
                return None
            deltas.append(a[0] / a[1] - e[0] / e[1])
    return 100 * sum(deltas) / len(deltas)


def equal_reader_correlation(rows, draws=20000, seed=2026091463):
    """Resample whole worlds, keeping their reader outcomes together; frames are a sensitivity.

    These empirical intervals can collapse at ceilings. They are NOT a noninferiority test.
    Fixed readers are never resampled or represented as a population of independent agents.
    """
    worlds = defaultdict(list)
    for row in rows:
        worlds[row['world_id']].append(row)
    strata, frames = defaultdict(list), defaultdict(list)
    for wid, group in worlds.items():
        strata[group[0]['form'], group[0]['domain']].append(wid)
        frames[group[0]['frame_family']].extend(group)
    result = {}
    for method in ['world_within_form_domain', 'frame_family']:
        rng = random.Random(f'{seed}:{method}')
        values = {f: [] for f in ['overall', *FORMS]}
        undefined = {f: 0 for f in values}
        for _ in range(draws):
            if method == 'world_within_form_domain':
                sample = [r for ids in strata.values() for wid in rng.choices(ids, k=len(ids))
                          for r in worlds[wid]]
            else:
                sample = [r for frame in rng.choices(sorted(frames), k=len(frames)) for r in frames[frame]]
            for f in values:
                value = equal_reader_contrast(sample, None if f == 'overall' else f)
                if value is None:
                    undefined[f] += 1
                else:
                    values[f].append(value)
        result[method] = {}
        for f, nums in values.items():
            nums.sort()
            result[method][f] = {'accepted_draws': len(nums), 'undefined_draws': undefined[f],
                'percentile_95': [nums[int(.025*len(nums))], nums[int(.975*len(nums))]] if nums else None,
                'not_a_noninferiority_certificate': True}
    result['leave_one_frame_out'] = {f: equal_reader_contrast(
        [r for r in rows if r['frame_family'] != f]) for f in sorted(frames)}
    result['scope'] = 'Separate equal-reader sensitivity, not the official CAD statistic or a new carrier.'
    return result


def validate_journal(cells, plan):
    expected = {(c['world_id'], c['reader']): c['arm'] for c in plan}
    seen = set()
    for c in cells:
        key = (c['item_id'], c['reader'])
        if key in seen:
            raise ValueError('Repeated reader/world cell')
        seen.add(key)
        if expected.get(key) != c['arm']:
            raise ValueError('Cell does not match frozen item/reader/arm assignment')
    return len(seen) == len(expected)


def analyse(items, cells, plan, draws=20000):
    complete = validate_journal(cells, plan)
    result = report.analyse(items, cells, draws=draws)
    rows = report.decode(items, cells)
    result.update(kind='choose-any.supplementary-report.final-20260915',
                  planned_target_cells=len(plan), planned_cells_complete=complete,
                  equal_reader_within_reader_delta_pp=equal_reader_contrast(rows),
                  equal_reader_per_form_delta_pp={f: equal_reader_contrast(rows, f) for f in FORMS},
                  equal_reader_correlation_sensitivity=equal_reader_correlation(rows, draws=draws))
    if not complete:
        result['conditional_ni'] = {'status': 'unavailable_incomplete_run',
            'reason': 'Partial/abort observations retained. No preservation certification.'}
    result['precision_boundary'] = (
        'Conditional per-reader binomial bounds assume exchangeable independent worlds within that '
        'reader, not 288 independent model responses; shared authored frames may violate this. '
        'Both form tests are required for their conjunction, not a simultaneous confidence region. '
        'No observed, synthetic, or zero-width empirical bootstrap interval establishes ratification.')
    return result


def planned_composition(plan):
    counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for c in plan:
        counts[c['form']][c['reader']][c['arm']] += 1
    out = {}
    for f in FORMS:
        total = {a: sum(counts[f][r][a] for r in READERS) for a in ['english', 'ainglish']}
        weights = {r: counts[f][r]['ainglish']/total['ainglish'] -
                      counts[f][r]['english']/total['english'] for r in READERS}
        ni = report.conditional_ni({r: {a: {'correct': n, 'live': n} for a, n in counts[f][r].items()}
                                    for r in READERS})
        eq_lower = 100 * sum(v['ainglish_lower'] - v['english_upper']
                             for v in ni['components'].values()) / len(READERS)
        out[f] = {'reader_arm_counts': counts[f], 'pooled_arm_counts': total,
                  'reader_mixture_weight_difference': weights,
                  'max_absolute_zero_within_reader_effect_composition_pp':
                      100 * sum(max(0, w) for w in weights.values()),
                  'all_correct_hypothetical_official_weight_lower_pp': ni['lower_delta_pp'],
                  'all_correct_hypothetical_equal_reader_lower_pp': eq_lower}
    return {'status': 'PLANNING_ONLY_NO_OBSERVED_READER_OUTCOMES', 'forms': out,
            'distinction': 'The earlier equal-reader planning reference and arm-pooled official-weight '
                'reference use different weights. Neither reference reaches minus 5 pp here. '
                'These conservative all-correct illustrations are not a universal impossibility theorem.'}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--journal', type=Path)
    ap.add_argument('--output', required=True, type=Path)
    args = ap.parse_args()
    if args.output.exists():
        raise SystemExit('Refusing to overwrite an existing analysis')
    plan = json.loads((ROOT/'planned-cells.json').read_text())['cells']
    if args.journal is None:
        value = planned_composition(plan)
    else:
        journal = json.loads(args.journal.read_text())
        if journal.get('kind') != 'ainglish.panel.cell-results.v1' or not journal.get('attempt_id'):
            raise SystemExit('Requires the saved official cell-results journal and its minted attempt ID')
        items = json.loads((ROOT/'items.json').read_text())
        value = analyse(items, journal['rows'], plan)
        value['source_attempt_id'] = journal['attempt_id']
        value['source_journal_raw_sha256'] = hashlib.sha256(args.journal.read_bytes()).hexdigest()
        value['items_sha256'] = hashlib.sha256(json.dumps(items, sort_keys=True, ensure_ascii=False,
                                                        separators=(',', ':')).encode()).hexdigest()
    args.output.write_text(json.dumps(value, indent=2) + '\n')
    print(json.dumps({'status': value.get('status', 'REPORT_ONLY_NOT_A_MEASUREMENT'),
                      'output': str(args.output), 'reader_calls': 0}))
