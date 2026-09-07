"""Prospective instruments. No network, tokenizer or model calls in this module."""

FRAMES = [
    ('the backup', 'finish', 'finished'), ('the parcel', 'arrive', 'arrived'),
    ('the lights', 'be off', 'been off'), ('the room', 'be empty', 'been empty'),
    ('the accounts', 'balance', 'balanced'), ('the train', 'leave', 'left'),
    ('the gate', 'be closed', 'been closed'), ('the report', 'be available', 'been available'),
    ('the pump', 'stop', 'stopped'), ('the test suite', 'complete', 'completed'),
    ('the invoice', 'reach the customer', 'reached the customer'),
    ('the package', 'clear customs', 'cleared customs'), ('the pool', 'be warm', 'been warm'),
    ('the server', 'be idle', 'been idle'), ('the seedlings', 'be watered', 'been watered'),
    ('the archive', 'be sealed', 'been sealed'), ('the printer', 'finish the labels', 'finished the labels'),
    ('the library', 'be open', 'been open'), ('the paths', 'be clear', 'been clear'),
    ('the team', 'submit its figures', 'submitted its figures'),
    ('the courier', 'return the keys', 'returned the keys'),
    ('the clock', 'synchronise', 'synchronised'), ('the stock count', 'end', 'ended'),
    ('the new account', 'be active', 'been active'), ('the queue', 'be empty', 'been empty'),
]


def ordered(options, answer, position):
    rest = [x for x in options if x != answer]
    rest.insert(position % len(options), answer)
    return rest


def controls(prefix):
    """Target-independent routing controls; missing information versus a resolved fact.

    The cold arm is intentionally unresolved, not a meaning-matched language arm.
    Its score measures recovery of the planted answer, not cold-arm correctness.
    There is no instruction to copy a supplied option or select a named answer.
    """
    names = ['Ari', 'Bex', 'Cleo', 'Dara', 'Eren']
    things = ['amber ledger', 'east key', 'blue folder', 'export list', 'south permit',
              'seal book', 'north checklist', 'green pass', 'west docket', 'audit envelope']
    rows = []
    for i, thing in enumerate(things):
        first, second = names[i % 5], names[(i + 2) % 5]
        rows.append({'id': f'{prefix}-control-{i}', 'calibration': True,
            'calibration_scope': 'target-independent', 'calibration_construct': 'resolved custody',
            'english': f'The handoff assigns the {thing} to {first} or {second}; which one is not recorded.',
            'ainglish': f'The handoff assigns the {thing} to {first}, not {second}.',
            'question': f'Who receives the {thing}?',
            'options': ordered(names + ['cannot determine'], first, i), 'answer': first})
    return rows


def should_items():
    answers = ['A departure from an invoked standard is established by this statement.',
               'No such departure is established by this statement; other standards may still apply.']
    question = ('The described event did not happen by the stated deadline. From this statement alone, '
                'is that failure enough to establish a departure from what an applicable standard calls for?')
    rows = []
    for n, (subject, infinitive, participle) in enumerate(FRAMES):
        for aspect in ('plain', 'perfect'):
            complement = infinitive if aspect == 'plain' else 'have ' + participle
            common = ('Fictional handoff. Other requirements may exist, but their applicability has not '
                      'been disclosed. Interpret only what this statement establishes. Statement: ')
            for role in ('rule', 'forecast'):
                i = len(rows); answer = answers[role == 'forecast']
                english = (f'The applicable procedure calls for {subject} to {complement} by Friday.'
                    if role == 'rule' else
                    f'Based on normal behaviour, the speaker expects {subject} to {complement} by Friday; '
                    'this statement does not specify an obligation.')
                rows.append({'id': f'should-repair-{n}-{aspect}-{role}',
                    'english': common + english,
                    'ainglish': common + f'{subject.capitalize()} should-as-{role} {complement} by Friday.',
                    'question': question, 'options': ordered(answers, answer, n + int(aspect == 'perfect') + int(role == 'forecast')), 'answer': answer,
                    'settlement_stratum': role, 'frame': n, 'aspect': aspect,
                    'oracle': {'invokes_applicable_requirement': role == 'rule',
                               'asserts_absence_of_other_requirements': False}})
    return rows + controls('should-repair')


DOMAINS = [
    ('tests', 'failed'), ('replicas', 'responded'), ('permissions', 'expired'),
    ('recipients', 'replied'), ('alerts', 'cleared'), ('items', 'arrived'),
    ('students', 'submitted a project'), ('walkers', 'crossed the bridge'),
    ('lamps', 'were lit'), ('seats', 'were occupied'),
]


def quantifier_items():
    options = ['First: yes; second: yes.', 'First: yes; second: no.',
               'First: no; second: yes.', 'First: no; second: no.']
    rows = []
    for domain, (noun, predicate) in enumerate(DOMAINS):
        for variant in range(10):
            size = variant + 2
            common = (f'Case Q{domain}-{variant}. The set under discussion is exactly these {size} {noun}. '
                      'Interpret what the quoted sentence asserts, not a hidden actual count. Sentence: ')
            positive = variant % 2 == 0
            question = ('First, would the sentence be contradicted if zero members satisfied the predicate? '
                        'Second, must at least one member fail to satisfy the predicate?' if positive else
                        'First, is zero satisfying members compatible with the sentence? '
                        'Second, is every member satisfying the predicate compatible with the sentence?')
            for marker in ('some-or-all', 'some-but-not-all'):
                upper_excluded = marker == 'some-but-not-all'
                bits = (True, upper_excluded) if positive else (False, not upper_excluded)
                answer = f'First: {"yes" if bits[0] else "no"}; second: {"yes" if bits[1] else "no"}.'
                english = (f'At least one of the {noun} {predicate}; this sentence does not exclude every one of them doing so.'
                           if not upper_excluded else f'At least one but fewer than all of the {noun} {predicate}.')
                rows.append({'id': f'quantifier-repair-{domain}-{variant}-{marker}',
                    'english': common + english, 'ainglish': common + f'{marker.capitalize()} {noun} {predicate}.',
                    'question': question, 'options': ordered(options, answer, len(rows) % 4), 'answer': answer,
                    'settlement_stratum': marker, 'frame': f'{domain}-{variant}',
                    'oracle': {'population_size': size, 'lower_bound': 1,
                               'upper_bound': size - int(upper_excluded), 'positive_probes': positive}})
    return rows + controls('quantifier-repair')


def selfcheck():
    from collections import Counter
    should = should_items(); quantifiers = quantifier_items()
    assert Counter(r['settlement_stratum'] for r in should if not r.get('calibration')) == {'rule': 50, 'forecast': 50}
    for frame in range(25):
        for aspect in ('plain', 'perfect'):
            pair = [r for r in should if r.get('frame') == frame and r.get('aspect') == aspect]
            assert len(pair) == 2 and {r['oracle']['invokes_applicable_requirement'] for r in pair} == {True, False}
            assert all(not r['oracle']['asserts_absence_of_other_requirements'] for r in pair)
    assert Counter(r['settlement_stratum'] for r in quantifiers if not r.get('calibration')) == {'some-or-all': 100, 'some-but-not-all': 100}
    # Enumerate all count worlds, not model judgements or an answer-copy instruction.
    for row in quantifiers:
        if row.get('calibration'): continue
        o = row['oracle']; legal = set(range(o['lower_bound'], o['upper_bound'] + 1)); size = o['population_size']
        assert 0 not in legal and bool(legal)
        if o['positive_probes']:
            bits = (0 not in legal, all(n < size for n in legal))
        else:
            bits = (0 in legal, size in legal)
        assert row['answer'] == f'First: {"yes" if bits[0] else "no"}; second: {"yes" if bits[1] else "no"}.'
    for rows in (should, quantifiers):
        targets = [r for r in rows if not r.get('calibration')]
        assert len({(r['english'], r['ainglish'], r['question']) for r in targets}) == len(targets)
        assert max(Counter(r['options'].index(r['answer']) for r in targets).values()) == len(targets) // len(targets[0]['options'])
    return {'should_targets': 100, 'quantifier_targets': 200, 'controls_per_instrument': 10,
            'oracle': 'exhaustive finite quantifier counts and explicit should entailment metadata',
            'target_calls': 0, 'qualification_calls': 0}

if __name__ == '__main__':
    print(selfcheck())
