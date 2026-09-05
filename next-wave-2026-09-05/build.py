"""Freeze authored comparison cases and exact finite population bytes; no reader calls."""
from collections import Counter
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import random
import statistics

ROOT = Path(__file__).resolve().parent
FROZEN = ROOT / 'frozen'
DOMAINS = [('temperature offset', 'degC'), ('payment adjustment', 'GBP'),
           ('balance change', 'EUR'), ('schedule shift', 'minutes'),
           ('energy balance', 'kWh'), ('distance offset', 'cm'),
           ('inventory adjustment', 'units'), ('pressure offset', 'Pa')]
FAMILIES = {
    'one_high_outlier': [1, 1, 1, 1, 101],
    'equal_centres_skew_cue': [0, 2, 3, 3, 7],
    'even_unobserved_median': [1, 2, 8, 9],
    'duplicate_middle': [-9, 3, 3, 8],
    'negative_values': [-13, -8, -5, -2, 3],
    'symmetric_odd': [-5, -2, 0, 2, 5],
    'symmetric_even': [-4, -1, 1, 4],
    'two_tied_modes': [1, 1, 4, 4, 20],
}

def canonical(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()

def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        json.dump(obj, f, indent=2, ensure_ascii=False); f.write('\n')

def centre(values, form):
    ordered = sorted(Fraction(x) for x in values)
    if form == 'mean-of':
        return sum(ordered) / len(ordered)
    mid = len(ordered) // 2
    return ordered[mid] if len(ordered) % 2 else (ordered[mid-1] + ordered[mid]) / 2

def number(value):
    value = Fraction(value)
    return str(value.numerator) if value.denominator == 1 else str(float(value))

def positioned(options, answer, index, seed):
    options = list(options)
    position = random.Random(seed + index).randrange(len(options))
    shift = (options.index(answer) - position) % len(options)
    return options[shift:] + options[:shift]

def controls(name):
    rows = []
    for i, (a, b) in enumerate([('Mira', 'Sana'), ('Neri', 'Olan'), ('Vela', 'Tari'), ('Nola', 'Kavi'),
                              ('Fara', 'Leni'), ('Eran', 'Ravi'), ('Suri', 'Toma'), ('Zena', 'Iven')]):
        ref = f'NWC-{name}-{i}'
        e = f'Either {a} or {b} holds sealed parcel {ref}; its holder remains unspecified.'
        m = f'Only {a} not {b} holds sealed parcel {ref}; its holder is specified.'
        assert len(e.split()) == len(m.split())
        size = max(len(e), len(m)); e, m = e.ljust(size), m.ljust(size)
        options = [a, b, 'not determined by the text', 'neither of them']
        rows.append({'id': f'{name}-control-{i}', 'calibration': True,
            'english': e, 'ainglish': m, 'question': f'Who holds parcel {ref}?', 'answer': a,
            'options': options[i % 4:] + options[:i % 4],
            'control_note': 'Equal word count and character length; final spaces are padding, not added information. Native model-token equality is not asserted.'})
    return rows

def population(ref, values, unit, window, sample=False):
    return {'id': ref, 'observations': values, 'unit': unit,
        'window': window, 'inclusion': 'every recorded numeric observation in this finite file',
        'exclusion': 'none', 'missing_value_policy': 'no missing observations',
        'transformation': 'identity', 'boundary': 'a named sample, not its wider target population' if sample else 'the exact named finite collection'}

def record_text(p):
    return f"{p['id']} ({p['unit']}; {p['window']}): observations " + ', '.join(map(str, p['observations'])) + '.'

def assertion(form, ref, value, unit, practical=False, variant=0):
    marked = f'{form}({ref}) = {value} {unit}.'
    if practical:
        name = 'arithmetic mean' if form == 'mean-of' else 'median'
        short = 'mean' if form == 'mean-of' else 'median'
        english = (f'{name} of {ref} = {value} {unit}.' if variant % 2 == 0 else
                   f'{short}({ref}) = {value} {unit}.')
    else:
        name = 'unweighted arithmetic mean' if form == 'mean-of' else 'median'
        english = f'The {name} of every numeric observation in the exact finite population {ref} is {value} {unit}.'
    return english, marked

def mean_primary():
    rows, populations = [], {}
    frames = list(itertools.product(range(8), list(FAMILIES), range(2)))
    for i, (domain, family, window) in enumerate(frames):
        unit = DOMAINS[domain][1]
        refs = [f'N{7100+i}A', f'N{7100+i}B']
        base = FAMILIES[family]
        values = [[x * (domain+1) + 2*window for x in base],
                  [x * (domain+1) + 2*window + 17 for x in base]]
        pair = [population(refs[k], values[k], unit, f'2026-09-0{3+k}T09:00/10:00Z', sample=(i % 3 == 0)) for k in range(2)]
        populations.update({p['id']: p for p in pair})
        chosen = (domain + window) % 2; active = pair[chosen]
        common = (f'Frozen {DOMAINS[domain][0]} records follow. Each named file is complete for its stated finite boundary, '
                  'includes all listed observations, excludes none, contains no missing values, and uses no transformation. '
                  'Values have equal weight. These records alone make no claim about any wider population.\n' +
                  '\n'.join(record_text(p) for p in pair) + '\nReport: ')
        for f, form in enumerate(['mean-of', 'median-of']):
            result = centre(active['observations'], form)
            english, marked = assertion(form, active['id'], number(result), unit)
            computations = ['add every value and divide by its count', 'sort the values and take the middle (averaging two central values if needed)']
            options = [f'{op}; use {ref}' for op, ref in itertools.product(computations, refs)]
            answer = f'{computations[f]}; use {active["id"]}'
            rows.append({'id': f'mean-primary-{i:03}-{f}', 'english': common+english,
                'ainglish': common+marked, 'question': 'Which procedure and which stored collection would check exactly the reported quantity? Select the complete pair.',
                'options': options, 'answer': answer, 'settlement_stratum': form,
                'strata': {'form': form, 'domain': DOMAINS[domain][0], 'family': family,
                    'frame_cluster': i, 'target_ref': active['id'], 'other_ref': refs[1-chosen],
                    'statistic_index': f, 'reported_value': number(result), 'unit': unit,
                    'window': window, 'sample_boundary': active['boundary']}})
    practical = json.loads(json.dumps(rows))
    for row in practical:
        s = row['strata']; head = row['english'].rsplit('Report: ', 1)[0] + 'Report: '
        e, _ = assertion(s['form'], s['target_ref'], s['reported_value'], s['unit'], True, s['frame_cluster'])
        row['english'] = head + e
    return rows, practical, populations

def mean_hard(populations):
    rows = []
    probes = ['above_most', 'observed_centre', 'sample_scope', 'exclusion_change', 'weighted',
              'approximate', 'categorical', 'uncertainty', 'causation', 'exact_recheck']
    for i, (domain, probe) in enumerate(itertools.product(range(8), probes)):
        unit = DOMAINS[domain][1]
        family = list(FAMILIES)[(domain + probes.index(probe)) % len(FAMILIES)]
        values = [x * (domain+1) for x in FAMILIES[family]]
        ref = f'H{8300+i}'
        pop = population(ref, values, unit, '2026-09-04T13:00/14:00Z', True)
        populations[ref] = pop
        for f, form in enumerate(['mean-of', 'median-of']):
            value = centre(values, form)
            e, a = assertion(form, ref, number(value), unit)
            context = 'The immutable record names only the listed finite sample, with equal weights, no missing values and no transformation. ' + record_text(pop)
            yes = False
            if probe == 'above_most':
                question = 'Is the reported number strictly greater than more than half of these individual observations?'
                yes = sum(Fraction(x) < value for x in values) > len(values)/2
            elif probe == 'observed_centre':
                question = 'Does any listed observation actually equal the reported number?'
                yes = value in values
            elif probe == 'sample_scope':
                question = 'Does this report alone establish the same number for the wider population from which this sample was drawn?'
            elif probe == 'exclusion_change':
                context += ' A later collection removes the largest listed observation and has a different immutable reference.'
                question = 'Can the later collection silently keep the original reference in this exact report?'
            elif probe == 'weighted':
                context = context.replace('equal weights', 'unequal weights') + ' The backend used an unequal-weight estimator, not the unweighted statistic.'
                question = 'Is the report licensed as an assertion of the stated unweighted finite-collection statistic from that backend?'
            elif probe == 'approximate':
                context += ' The backend instead produced an approximation from a moving window and cannot reproduce this exact finite file.'
                question = 'Does that backend by itself license the exact report as written?'
            elif probe == 'categorical':
                context = 'The referenced file actually contains only the unordered category labels red, red, blue, blue, green. A numeric order has not been defined.'
                question = 'Can either of these numeric-centre reports be justified by taking the most common category in that file?'
            elif probe == 'uncertainty':
                question = 'Does reporting this centre alone provide a confidence interval or certify the measurement precision?'
            elif probe == 'causation':
                question = 'Does this centre report alone establish that an earlier intervention caused the observed values?'
            else:
                question = 'Could the exact reported centre be independently checked using these complete finite observations and the specified procedure?'
                yes = True
            options = ['yes', 'no']
            rows.append({'id': f'mean-hard-{i:03}-{f}', 'english': context+'\nReport: '+e,
                'ainglish': context+'\nReport: '+a, 'question': question,
                'options': options, 'answer': options[0 if yes else 1], 'settlement_stratum': form,
                'strata': {'form': form, 'domain': DOMAINS[domain][0], 'probe': probe, 'family': family,
                    'frame_cluster': i, 'target_ref': ref, 'reported_value': number(value),
                    'diagnostic_only': True, 'intentionally_unlicensed': probe in ['weighted', 'approximate', 'categorical']}})
    return rows

def balance(rows, seed):
    for form in sorted({r['settlement_stratum'] for r in rows}):
        subset = [r for r in rows if r['settlement_stratum'] == form]
        choices = len(subset[0]['options'])
        order = [i % choices for i in range(len(subset))]
        random.Random(seed + len(form)).shuffle(order)
        for row, pos in zip(subset, order):
            options = row['options']; shift = (options.index(row['answer']) - pos) % choices
            row['options'] = options[shift:] + options[:shift]

def verdict_primary():
    tasks = [('smoke suite', 'deployment'), ('signature verifier', 'release bundle'),
             ('integrity monitor', 'stored ledger'), ('schema check', 'dataset'),
             ('policy gate', 'access change'), ('replication runner', 'source claim'),
             ('inventory audit', 'stock record'), ('checksum check', 'archive')]
    scenarios = [
        ('all required inputs were read; the target-specific assertion was false', 'the runner timed out before it could read the target'),
        ('the target comparison finished and a required property did not hold', 'the input fixture was missing before comparison began'),
        ('all planned steps finished; the target evidence violated the criterion', 'a rate limit stopped the run before any target finding'),
        ('the result was committed after completion: the target did not meet its requirement', 'the process crashed before a target result was committed'),
    ]
    questions = ['target_evidence', 'first_result', 'failure_object', 'prior_knowledge']
    rows = []
    for i, (domain, reason, probe) in enumerate(itertools.product(range(8), range(4), questions)):
        check, target = tasks[domain]; ref = f'V{9100+i}'
        for f, form in enumerate(['verdict-fail', 'no-verdict']):
            common = (f'The {check} was scheduled for {target} {ref}. Before this check, the target state was unknown; '
                      'there is no other current finding. Retained execution log: ' + scenarios[reason][f] + '.\n')
            e = f'{check}: ' + ('ran to completion and found the target defective.' if f == 0 else 'did not reach a target judgment.')
            a = f'{check}: {form}.'
            if probe == 'target_evidence':
                question = 'Is the thing being checked now known to be broken?'
                options = ['yes', 'no, it is known to be sound', 'cannot tell from the available findings']
                answer = options[0 if f == 0 else 2]
            elif probe == 'first_result':
                question = 'Is another completed check still needed to obtain the first finding about this target?'
                options = ['yes, no target finding was obtained', 'no, a target finding is already available', 'the target has been proved sound']
                answer = options[1 if f == 0 else 0]
            elif probe == 'failure_object':
                question = 'Where does the failure information point?'
                options = ['a required property of the target', 'the checking process before a result', 'both a sound target and a completed successful process']
                answer = options[f]
            else:
                question = 'What changed in what the receiver knows about the target?'
                options = ['new evidence of a target defect', 'no new target judgment; it remains unknown', 'new evidence proving the target sound']
                answer = options[f]
            rows.append({'id': f'verdict-primary-{i:03}-{f}', 'english': common+e,
                'ainglish': common+a, 'question': question, 'options': options, 'answer': answer,
                'settlement_stratum': form, 'strata': {'form': form, 'domain': check,
                    'frame_cluster': i, 'log_branch': reason, 'probe': probe,
                    'anchor': scenarios[reason][f], 'prior_target_knowledge': 'unknown'}})
    bare = json.loads(json.dumps(rows))
    for row in bare:
        context, report = row['english'].rsplit('\n', 1)
        check = report.split(': ', 1)[0]
        row['english'] = context + '\n' + check + ': failed.'
    return rows, bare

def main():
    mean, practical, populations = mean_primary()
    hard = mean_hard(populations)
    verdict, bare = verdict_primary()
    studies = {'mean.careful': mean, 'mean.practical': practical, 'mean.hard': hard,
               'verdict.careful': verdict, 'verdict.bare': bare}
    audit = {}
    for i, (name, rows) in enumerate(studies.items()):
        balance(rows, 2026090560 if name.startswith('mean') else 2026090561)
        assert len({r['id'] for r in rows}) == len(rows)
        assert len({(r['english'], r['ainglish'], r['question']) for r in rows}) == len(rows)
        assert all(r['answer'] in r['options'] and len(set(r['options'])) == len(r['options']) for r in rows)
        data = rows + controls(name)
        save(FROZEN / (name + '.items.json'), data)
        audit[name] = {'real_items': len(rows), 'calibration_items': 8,
            'per_form': dict(Counter(r['settlement_stratum'] for r in rows)),
            'positions_by_form': {f: dict(Counter(r['options'].index(r['answer']) for r in rows if r['settlement_stratum'] == f))
                                  for f in sorted({r['settlement_stratum'] for r in rows})},
            'items_sha256': hashlib.sha256(canonical(data)).hexdigest(), 'reader_calls': 0}
    save(FROZEN / 'populations.json', populations)
    save(FROZEN / 'design-index.json', audit)
    print(json.dumps(audit, indent=2))

if __name__ == '__main__':
    main()
