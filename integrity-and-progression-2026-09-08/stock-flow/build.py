"""Prepare a held careful-English reader component; no network, tokenizer or reader calls."""
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
DOMAINS = [
    ('staffing', 'workers', 'the active duty roster'),
    ('rooms', 'visitors', 'the room'),
    ('evacuation', 'responders', 'the evacuation sector'),
    ('queues', 'jobs', 'the pending queue'),
    ('inventory', 'packages', 'the inventory bin'),
    ('replicas', 'replicas', 'the active replica set'),
    ('subscriptions', 'subscriptions', 'the active subscription set'),
    ('fleets', 'sensors', 'the connected device fleet'),
]
PATTERNS = {
    'arrival': [(15, True)],
    'exit': [(20, False)],
    'repeat-exit': [(10, False), (20, True), (30, False)],
    'reentry': [(10, False), (40, True)],
    'cutoff-exit': [(60, False)],
    'start-exit': [(0, False)],
    'unspecified-endpoint': [(60, False)],
    'no-flow': [],
}
PROBES = {
    'arrival': ('is outside at the start, enters before cutoff, stays inside through cutoff, and never exits during the interval', 'one', 'zero'),
    'exit': ('starts inside, exits strictly between the interval endpoints, and does not return before cutoff', 'zero', 'one'),
    'repeat-exit': ('starts inside, exits, returns, then exits again strictly between the interval endpoints, and is outside at cutoff', 'zero', 'one'),
    'reentry': ('starts inside, exits strictly between the interval endpoints, returns before cutoff, and stays inside through cutoff', 'one', 'one'),
    'cutoff-exit': ('is inside until an exit effective exactly at cutoff; the interval includes its start and excludes its end at cutoff', 'zero', 'zero'),
    'start-exit': ('exits exactly at the included start of the interval and stays outside through cutoff', 'zero', 'one'),
    'unspecified-endpoint': ('is inside until an exit exactly at cutoff; the separate interval ends at cutoff but its endpoint-inclusion rule is not specified', 'zero', 'not determined'),
    'no-flow': ('stays inside throughout the interval and through cutoff without any exit', 'one', 'zero'),
}


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def save(name, value):
    # The explicit switch replaces only this builder's generated, unrun files.
    with (ROOT / name).open('w' if '--replace-generated' in sys.argv else 'x') as out:
        json.dump(value, out, ensure_ascii=False, indent=2, allow_nan=False)
        out.write('\n')


def world(domain_index, pattern, variant):
    # Stable identity keys, valid transitions and two independent state/flow oracles.
    initial = {'subject': pattern != 'arrival'}
    for i in range((domain_index + variant) % 3): initial['stayer-' + str(i)] = True
    departures = (domain_index + 2 * variant) % 3
    for i in range(departures): initial['leaver-' + str(i)] = True
    events = [{'minute': t, 'member': 'subject', 'inside': state} for t, state in PATTERNS[pattern]]
    events += [{'minute': 22 + i, 'member': 'leaver-' + str(i), 'inside': False} for i in range(departures)]
    if variant:
        initial['arrival-extra'] = False
        events.append({'minute': 45, 'member': 'arrival-extra', 'inside': True})
    events.sort(key=lambda event: (event['minute'], event['member']))
    state = dict(initial)
    left = set()
    for event in events:
        assert state[event['member']] != event['inside'], 'not a real transition'
        if state[event['member']] and not event['inside'] and 0 <= event['minute'] < 60:
            left.add(event['member'])
        if event['minute'] <= 60: state[event['member']] = event['inside']
    final_by_history = {}
    exits_by_history = set()
    for member, start in initial.items():
        history = [event for event in events if event['member'] == member]
        final_by_history[member] = next((event['inside'] for event in reversed(history) if event['minute'] <= 60), start)
        # Validity was checked above; a false event is therefore an inside-to-outside transition.
        if any(not event['inside'] and 0 <= event['minute'] < 60 for event in history): exits_by_history.add(member)
    assert state == final_by_history and left == exits_by_history
    return {'initial_inside': initial, 'events': events, 'cutoff_minute': 60,
            'interval': {'start': 0, 'end': 60, 'include_start': True, 'include_end': False},
            'stock': sum(state.values()), 'distinct_flow': len(left), 'independent_oracles_agree': True}


def build():
    items, worlds = [], []
    for di, (domain, noun, scope_name) in enumerate(DOMAINS):
        for pattern in PATTERNS:
            for variant in range(2):
                ident = f'sf-{domain}-{pattern}-{variant}'
                w = world(di, pattern, variant)
                w.update(id=ident, domain=domain, pattern=pattern, variant=variant)
                worlds.append(w)
                scope = 'S-' + str(800 + len(worlds))
                shared = (f'Fictional report for {noun}. Scope {scope} names {scope_name}; inside means membership '
                          f'in that scope, not physical movement unless the domain requires it. Members have stable '
                          'distinct identity keys. The date is 2026-09-10, all times are UTC. Cutoff is 08:00, '
                          'after all membership changes effective at 08:00. Interval I is [07:00,08:00): start included, end excluded.\n')
                for form in ['remain-in', 'departed-from']:
                    n = w['stock'] if form == 'remain-in' else w['distinct_flow']
                    marked = (f'Exactly {n} {noun} remain-in({scope}) as_of(08:00Z).' if form == 'remain-in'
                              else f'Exactly {n} distinct {noun} departed-from({scope}) during(I).')
                    english = (f'Immediately after all changes effective at 08:00, exactly {n} distinct {noun} are inside {scope}.'
                               if form == 'remain-in' else
                               f'Exactly {n} distinct {noun} each changed from inside {scope} to outside {scope} at least once during I.')
                    stock_answer = f'Capacity tickets: {n}; exit-review files: not determined.'
                    flow_answer = f'Capacity tickets: not determined; exit-review files: {n}.'
                    primary_options = [stock_answer, flow_answer,
                                       f'Capacity tickets: {n}; exit-review files: {n}.',
                                       'Neither total is determined.']
                    primary_question = ('The desk issues one capacity ticket for each member inside just after cutoff, '
                                        'and opens one exit-review file for each distinct member that changed from inside to '
                                        'outside during I. Which allocation record follows from this report alone?')
                    event_description, stock_contribution, flow_contribution = PROBES[pattern]
                    secondary_question = ('For a SEPARATE hypothetical case using the same kind of count, one qualifying '
                                          f'member {event_description}. All stated boundary facts in this question apply to '
                                          'that separate case; do not fill in an explicitly unspecified rule. How many '
                                          'contributions does this member make to the kind of count reported by the statement?')
                    for probe, question, options, gold in [
                        ('mode-and-count', primary_question, primary_options, stock_answer if form == 'remain-in' else flow_answer),
                        ('membership-boundary', secondary_question, ['zero', 'one', 'two', 'not determined'],
                         stock_contribution if form == 'remain-in' else flow_contribution),
                    ]:
                        offset = len(items) % 4
                        items.append({'id': ident + '-' + form + '-' + probe,
                                      'english': shared + 'Report: ' + english,
                                      'ainglish': shared + 'Report: ' + marked,
                                      'question': question, 'options': options[offset:] + options[:offset], 'answer': gold,
                                      'settlement_stratum': form + '-' + domain, 'form': form,
                                      'domain': domain, 'pattern': pattern, 'probe': probe,
                                      'world_id': ident,
                                      'oracle_boundary': 'The visible statement and question license the key. The hidden construction ledger is not a reader premise; the unreported other quantity is never scored as secretly known.'})
    assert len(worlds) == 128 and len(items) == 512
    assert len({item['id'] for item in items}) == len(items)
    counts = Counter(item['settlement_stratum'] for item in items)
    assert len(counts) == 16 and set(counts.values()) == {32}
    # Do not let form or probe determine the correct answer's position. Balance
    # all four positions within every form/domain/probe group, before any run.
    option_rng = random.Random(2026090841)
    position_counts = {}
    for stratum in counts:
        for probe in ['mode-and-count', 'membership-boundary']:
            group = [item for item in items if item['settlement_stratum'] == stratum and item['probe'] == probe]
            positions = list(range(4)) * (len(group) // 4)
            option_rng.shuffle(positions)
            for item, position in zip(group, positions, strict=True):
                distractors = [option for option in item['options'] if option != item['answer']]
                assert len(distractors) == 3
                option_rng.shuffle(distractors)
                distractors.insert(position, item['answer'])
                item['options'] = distractors
            distribution = Counter(item['options'].index(item['answer']) for item in group)
            assert set(distribution.values()) == {4} and len(distribution) == 4
            position_counts[stratum + '/' + probe] = dict(sorted(distribution.items()))
    for i in range(12):
        person = ['Ari', 'Bela', 'Cleo', 'Daru'][i % 4]
        items.append({'id': f'sf-control-{i}', 'calibration': True, 'calibration_scope': 'target-independent',
                      'calibration_construct': 'resolved pickup identity',
                      'english': f'The collector of parcel C-{900+i} is not recorded.',
                      'ainglish': f'The collector of parcel C-{900+i} is {person}.',
                      'question': f'Who collected parcel C-{900+i}?',
                      'options': ['Ari', 'Bela', 'Cleo', 'Daru', 'not determined'], 'answer': person})
    instruments = json.loads((REPO / 'overnight-2026-09-05/clock.careful.intent.json').read_text())['manifest']
    readers = [{k: v for k, v in reader.items() if k != 'instrument_preparation' and v != 'provider-default'}
               for reader in instruments['readers']]
    scope = ('Careful-English component only: 128 authored stock/flow worlds across eight domains, both forms, '
             '512 target items split equally between operational mode/count and separate hypothetical membership '
             'boundaries; sixteen form/domain strata. Cold markers versus explicit meaning-complete English, no '
             'glossary. No bare-left hidden-intention scoring, robustness, adoption, human-reader or future-trained claim. '
             'Shared templates and two pinned model families do not establish a natural-population estimate.')
    spec = {'kind': 'dexagon.stock-flow-careful-component.v1',
            'public_id': 'a-xffrm7wz2wt3xhzf', 'slug': 'exactly-n-members-remain-in-scope-as-of-t-exactly-n',
            'metric': 'comprehension_accuracy_delta', 'construct': 'remain-in / departed-from', 'seed': 2026090841,
            'panel': readers, 'models': instruments['models'], 'reader_qualifications': instruments['reader_qualifications'],
            'planted_arm': 'ainglish', 'calibration_min_gap': 0.5, 'calibration_min_recovered': 1, 'panel_neff': 2,
            'study_purpose': 'claim_test', 'study_scope': scope,
            'comparator': {'kind': 'careful-english-v1', 'description': 'Same resolved membership/time bindings. Marked complete count versus explicit meaning-complete English. Operational mode/count and separate hypothetical transitions are answerable from visible statements/questions, never the hidden world ledger.'},
            'items': items, 'items_sha256': digest(items),
            'settlement_strata': [{'id': key, 'weight': 1} for key in counts],
            'attempt': {'proposal_revision': 'exactly-n-members-remain-in-scope-as-of-t-exactly-n', 'estimand': scope,
                        'admissibility_gates': [
                            'HOLD until the confirming token source packet integrity review has a public resolution and the exact current cost prerequisite remains complete',
                            'Fresh authenticated suggestions still permit this original comprehension component; mapping and acceptance margins unchanged',
                            'Full input bytes and qualifiers frozen publicly before any reader call; verify exact cached artifact/settings and unexpired own qualifications',
                            'Review the separate-case boundary probes for leakage or contradictions before committing a run; no hidden-world answer inference',
                            'No model downloads or substitutions; physical host disk floor 15 GiB; unrelated GPU workloads are not evicted',
                            'Mint before spend; both readers pass the frozen target-independent control gate before all targets; no retries or selective omission',
                            'Retain absolute accuracy, every form/domain stratum, every probe category and unknown-boundary outcome; no pooled-only flagship claim',
                        ],
                        'planned_sample': {'worlds': 128, 'target_items': 512, 'controls': 12, 'readers': 2,
                                           'target_calls': 1024, 'calibration_calls': 48}}}
    save('worlds.json', worlds); save('items.json', items); save('unbound-runspec.json', spec)
    save('design-audit.json', {'state': 'prepared_not_run', 'worlds': 128, 'targets': 512, 'controls': 12,
                              'items_sha256': digest(items), 'strata': dict(counts), 'oracles_agree': True,
                              'answer_position_counts_by_form_domain_probe': position_counts,
                              'model_calls': 0, 'minted_attempt': None,
                              'mode_count_differing_worlds': sum(w['stock'] != w['distinct_flow'] for w in worlds),
                              'primary_other_quantity': 'not determined from the reported claim, even when the construction ledger knows it',
                              'limitations': ['128 authored worlds, eight shared event patterns; not 128 independent natural-language templates.',
                                              'The fine probes are prespecified diagnostics, not extra automatic settlement gates.',
                                              'Bare-language improvement and robustness remain unmeasured.',
                                              'Cold current-model scores are not estimates after Ainglish training.']})
    print('Prepared 128 worlds, 512 targets, 12 controls; zero network, encoding or reader calls.')


if __name__ == '__main__':
    build()
