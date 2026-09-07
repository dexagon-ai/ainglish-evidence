"""Prospective cold-reading instruments. No inference, sampling or network here.

Both target arms disclose the answer-bearing facts. Controls deliberately do not:
their planted information gap measures sensitivity, not comparative comprehension.
Frame variants are correlated authored examples, not independent natural usage.
"""
from collections import Counter
from itertools import product


def ordered(options, answer, index):
    remaining = [x for x in options if x != answer]
    remaining.insert(index % len(options), answer)
    return remaining


def controls(prefix):
    names = ['Anu', 'Bryn', 'Cato', 'Deni', 'Elin']
    objects = ['inspection card', 'harbour key', 'linen docket', 'station ledger',
               'tool receipt', 'visitor badge', 'orange folder', 'loan slip',
               'meeting notes', 'dispatch envelope']
    return [{'id': f'{prefix}-control-{i}', 'calibration': True,
             'calibration_scope': 'target-independent', 'calibration_construct': 'resolved custody',
             'english': f'The handoff assigns the {thing} to {names[i % 5]} or {names[(i + 2) % 5]}; the recipient is not recorded.',
             'ainglish': f'The handoff assigns the {thing} to {names[i % 5]}, not {names[(i + 2) % 5]}.',
             'question': f'Who receives the {thing}?',
             'options': ordered(names + ['cannot determine'], names[i % 5], i),
             'answer': names[i % 5]} for i, thing in enumerate(objects)]


DOMAINS = {
    'compute': ['batch node', 'inference slot', 'build worker'],
    'rooms': ['seminar room', 'practice room', 'meeting booth'],
    'transport': ['cargo bicycle', 'shuttle seat', 'van slot'],
    'storage': ['archive shelf', 'locker', 'storage volume'],
    'services': ['repair appointment', 'translation slot', 'support session'],
    'tickets': ['gallery ticket', 'concert seat', 'lecture place'],
    'subscriptions': ['journal account', 'backup subscription', 'analysis plan'],
    'equipment': ['tripod', 'microscope', 'survey meter'],
}


def availability_items():
    """288 targets: complete English; polarity/unknown extensions reported separately."""
    states = ['yes', 'no', 'unknown']
    options = [f'Listed charge: {a}; immediate assignment: {b}.' for a, b in product(states, repeat=2)]
    rows = []
    for domain, objects in DOMAINS.items():
        for n, obj in enumerate(objects):
            for marker, positive, other in product(['no-charge', 'available-now'], [True, False], states):
                price = ('no' if positive else 'yes') if marker == 'no-charge' else other
                available = other if marker == 'no-charge' else ('yes' if positive else 'no')
                common = (f'Fictional booking for the {obj}. Billing scope B is the listed charge for this single use; '
                          'allocation scope P is the named pool at 10:00 for this qualifying requester. '
                          'Both scopes and the references are resolved. A refundable deposit, later charges, '
                          'permissions, operational health, other pools and tomorrow are separate and unspecified. ')
                if marker == 'no-charge':
                    other_fact = {'yes': 'A unit can be assigned immediately from P.',
                                  'no': 'Every unit in P is occupied and cannot be assigned immediately.',
                                  'unknown': 'Whether a unit can be assigned immediately from P is not disclosed.'}[other]
                    english = f'The offer for the {obj} ' + ('has zero listed monetary charge in B.' if positive else 'has a nonzero listed monetary charge in B.')
                    ainglish = f'The offer for the {obj} is ' + ('' if positive else 'not ') + 'no-charge(B).'
                else:
                    other_fact = {'yes': 'This use creates a nonzero listed monetary charge in B.',
                                  'no': 'This use creates zero listed monetary charge in B.',
                                  'unknown': 'Whether this use creates a listed monetary charge in B is not disclosed.'}[other]
                    english = f'The {obj} ' + ('can' if positive else 'cannot') + ' currently be assigned to this qualifying requester from P.'
                    ainglish = f'The {obj} is ' + ('' if positive else 'not ') + 'available-now(P).'
                answer = f'Listed charge: {price}; immediate assignment: {available}.'
                rows.append({'id': f'availability-{len(rows):03}',
                    'english': common + other_fact + ' Statement: ' + english,
                    'ainglish': common + other_fact + ' Statement: ' + ainglish,
                    'question': 'Will assigning this item create a listed monetary charge in B, and can this requester get it assigned immediately from P? Use unknown only where not established.',
                    'options': ordered(options, answer, len(rows)), 'answer': answer,
                    'settlement_stratum': marker + ('-positive' if positive else '-negated'),
                    'domain': domain, 'frame': f'{domain}-{n}',
                    'oracle': {'price': price, 'allocation': available, 'unasserted_axis': other,
                               'positive_surface': positive, 'permission_or_health_implied': False}})
    return rows + controls('availability')


DECISIONS = {
    'operational': ['rotate the backup media', 'pause the batch queue', 'replace the pump', 'inspect the west line'],
    'social': ['hold a shared lunch', 'move the club meeting', 'book the museum visit', 'invite a guest speaker'],
    'governance': ['adopt the reporting schedule', 'open a consultation', 'appoint the audit team', 'revise the agenda'],
    'scheduling': ['move the workshop to Monday', 'start the survey at noon', 'reserve the evening slot', 'extend the booking window'],
}


def decision_items():
    options = [f'At noon: {state}; existing choice then: {record}; this sentence commands or permits: {force}.'
               for state, record, force in product(['offered', 'selected'], ['yes', 'no'], ['yes', 'no'])]
    rows = []
    for domain, actions in DECISIONS.items():
        for action in actions:
            for variant in range(4):
                source = ['the chair', 'the organiser', 'the coordinator', 'the designated delegate'][variant]
                background = [
                    f'{source.capitalize()} is senior, but seniority does not by itself select an option.',
                    f'A junior clerk reports {source}\'s record verbatim; the clerk\'s own rank is irrelevant.',
                    'At 15:00 another record superseded this one. The question concerns noon, not 15:00.',
                    'Many people expressed agreement beforehand. Popularity alone does not select an option.',
                ][variant]
                common = (f'Fictional {domain} record at noon. {source.capitalize()} has standing to make a choice '
                          'on this matter but is also free to offer an option without choosing it. '
                          + background + ' The record is a report, not a directive to its reader. Record: ')
                for marker in ['proposal-by', 'decision-by']:
                    chosen = marker == 'decision-by'
                    english = (f'{source.capitalize()} has operatively selected this course: {action}.' if chosen else
                               f'{source.capitalize()} offers this course for consideration, without selecting it: {action}.')
                    answer = f'At noon: {"selected" if chosen else "offered"}; existing choice then: {"yes" if chosen else "no"}; this sentence commands or permits: no.'
                    rows.append({'id': f'decision-{len(rows):03}', 'english': common + english,
                        'ainglish': common + f'{marker}({source}): {action}.',
                        'question': 'Classify the course at noon, whether it could then be reported as an existing choice, and whether this sentence itself directs the reader or grants authorisation.',
                        'options': ordered(options, answer, len(rows)), 'answer': answer,
                        'settlement_stratum': marker, 'domain': domain, 'frame': action,
                        'adversary': variant, 'oracle': {'selected_at_noon': chosen,
                            'force_granted': False, 'source_has_standing': True}})
    return rows + controls('decision')


CHECKS = {
    'CI': ['package signature', 'migration output', 'binary checksum', 'test fixture'],
    'monitor': ['reservoir sensor', 'relay line', 'coolant circuit', 'pressure gauge'],
    'verifier': ['archive seal', 'submitted certificate', 'parcel weight', 'ledger total'],
    'measurement': ['sample purity', 'timing trace', 'optical reading', 'voltage sample'],
}


def verdict_items(contrast):
    assert contrast in ['careful', 'bare-anchored']
    options = ['yes', 'no', 'cannot tell']
    rows = []
    for domain, objects in CHECKS.items():
        for obj in objects:
            for variant in range(4):
                for marker in ['verdict-fail', 'no-verdict']:
                    failed = marker == 'verdict-fail'
                    anchor = ([
                        'The completed log records an out-of-spec target and no intervening repair.',
                        'The final signed finding identifies a defect in the target; its state has not changed.',
                        'All required checks ran and found the target noncompliant; no correction followed.',
                        'The persisted result marks the target defective; this remains the current state.',
                    ] if failed else [
                        'The process exited before reading the target. Its condition has not been established.',
                        'The connection failed before assessment began. No other assessment is available.',
                        'The run was cancelled without evaluating the target. Its condition remains unestablished.',
                        'A retry is required because no assessment was produced. No other result is known.',
                    ])[variant]
                    common = f'Fictional {domain} report about the {obj}. Anchor: {anchor} Status: '
                    english = ('failed' if contrast == 'bare-anchored' else
                               ('ran and found the target defective' if failed else 'did not reach a judgement about the target'))
                    answer = 'yes' if failed else 'cannot tell'
                    rows.append({'id': f'verdict-{len(rows):03}', 'english': common + english + '.',
                        'ainglish': common + marker + '.',
                        'question': 'Is the thing being checked now known to be broken?',
                        'options': ordered(options, answer, len(rows)), 'answer': answer,
                        'settlement_stratum': marker, 'domain': domain, 'frame': obj,
                        'anchor_variant': variant, 'oracle': {'known_defective': failed, 'absence_of_judgement_is_success': False}})
    return rows + controls('verdict-' + contrast)


GENERATORS = {'availability': availability_items, 'decision': decision_items,
              'verdict-careful': lambda: verdict_items('careful'),
              'verdict-bare-anchored': lambda: verdict_items('bare-anchored')}


def selfcheck():
    report = {}
    for name, fn in GENERATORS.items():
        targets = [r for r in fn() if not r.get('calibration')]
        assert len({(r['english'], r['ainglish'], r['question']) for r in targets}) == len(targets)
        positions = Counter(r['options'].index(r['answer']) for r in targets)
        assert max(positions.values()) - min(positions.values()) <= 1
        for r in targets:
            assert r['answer'] in r['options'] and len(set(r['options'])) == len(r['options'])
            o = r['oracle']
            if name == 'availability':
                assert r['answer'] == f'Listed charge: {o["price"]}; immediate assignment: {o["allocation"]}.'
                assert o['unasserted_axis'] in ['yes', 'no', 'unknown']
            elif name == 'decision':
                assert ('At noon: selected; existing choice then: yes;' in r['answer']) == o['selected_at_noon']
                assert not o['force_granted'] and o['source_has_standing']
            else:
                assert r['answer'] == ('yes' if o['known_defective'] else 'cannot tell')
        report[name] = {'targets': len(targets), 'controls': 10,
                        'strata': dict(Counter(r['settlement_stratum'] for r in targets)),
                        'answer_positions': dict(positions), 'reader_calls': 0}
    a, b = verdict_items('careful'), verdict_items('bare-anchored')
    assert all(x['ainglish'] == y['ainglish'] and x['answer'] == y['answer'] for x, y in zip(a[:-10], b[:-10]))
    return report
