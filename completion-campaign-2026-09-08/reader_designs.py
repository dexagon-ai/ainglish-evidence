"""Prospective authored consequence tests; no inference or token counting here.

Both arms have identical visible contextual anchors. Bare English is never
assigned a hidden writer-intent gold. Correlated templates are not natural usage.
The main two-bit may-not test and its unsupported-inference probes stay separate.
"""
from collections import Counter
from itertools import product


def ordered(options, answer, index):
    rest = [v for v in options if v != answer]
    rest.insert(index % len(options), answer)
    return rest


def controls(prefix):
    """Target-independent information-sensitivity controls, not answer copying."""
    people = ['Inez', 'Jori', 'Kemi', 'Luan', 'Mavi']
    objects = ['survey card', 'blue notebook', 'harbour ticket', 'repair docket',
               'visitor ledger', 'class register', 'garden key', 'red umbrella',
               'parcel label', 'concert programme']
    return [{'id': f'{prefix}-cal-{i}', 'calibration': True,
             'calibration_scope': 'target-independent', 'calibration_construct': 'resolved custody',
             'english': f'The {thing} was given to {people[i % 5]} or {people[(i+1) % 5]}; the recipient is not recorded.',
             'ainglish': f'The {thing} was given to {people[i % 5]}, not {people[(i+1) % 5]}.',
             'question': f'Who received the {thing}?',
             'options': ordered(people + ['cannot determine'], people[i % 5], i),
             'answer': people[i % 5]} for i, thing in enumerate(objects)]


FRAMES = [
    ('transport', 'animate', 'The courier', 'enter the depot'),
    ('transport', 'inanimate', 'The shuttle', 'reach the island'),
    ('compute', 'animate', 'The analyst', 'publish the package'),
    ('compute', 'inanimate', 'The service', 'enter production'),
    ('learning', 'animate', 'The student', 'finish the exercise'),
    ('learning', 'inanimate', 'The teaching robot', 'enter the examination room'),
    ('workshop', 'animate', 'The technician', 'start the lathe'),
    ('workshop', 'inanimate', 'The delivery drone', 'reach the roof'),
    ('events', 'animate', 'The speaker', 'arrive at the hall'),
    ('events', 'inanimate', 'The display unit', 'activate the projector'),
]


def modal_rows(contrast):
    assert contrast in ('careful', 'bare')
    rows = []
    answers = [f'Breach if P: {a}; retain not-P in forecast: {b}.'
               for a, b in product(['licensed', 'not licensed'], repeat=2)]
    for frame, (domain, animacy, subject, predicate) in enumerate(FRAMES):
        for form, occurred, tense, anchor in product(['prohibition', 'possibility'], [False, True], ['future', 'ongoing'], [0, 1]):
            event = predicate + (' tomorrow' if tense == 'future' else ' during the current session')
            if form == 'prohibition':
                context = ['This is an applicable conduct-code entry, not a model forecast.',
                           'The archive classifies the following entry as a binding restriction; no forecast accompanies it.'][anchor]
                expansion = f'An applicable authority or rule forbids {subject.lower()} from satisfying P.'
                normative, epistemic = True, False
            else:
                context = ['This is a forecast entry under the speaker\'s current evidence, not a conduct-code entry.',
                           'The archive classifies the following entry as an epistemic assessment; no directive accompanies it.'][anchor]
                expansion = f'Under the speaker\'s current evidence or model, non-occurrence of P remains possible.'
                normative, epistemic = False, True
            # The later outcome cannot retrospectively change what the earlier sentence asserted.
            outcome = 'P subsequently happened.' if occurred else 'P subsequently did not happen.'
            common = (f'Fictional {domain} record. P means: {subject} will {event}. '
                      'The statement is interpreted at its recording time, before any outcome is known. '
                      + context + ' A later history note says ' + outcome + ' No other rule, capability or forecast is disclosed. Statement: ')
            tagged = f'{subject} may-not-as-{form} {event}.'
            bare = f'{subject} may not {event}.'
            answer = f'Breach if P: {"licensed" if normative else "not licensed"}; retain not-P in forecast: {"licensed" if epistemic else "not licensed"}.'
            common_fields = {'domain': domain, 'animacy': animacy, 'frame': frame,
                             'temporal_scope': tense, 'outcome_occurs': occurred, 'anchor_variant': anchor,
                             'form': form, 'semantic_cell': f'm-{frame}-{form}-{int(occurred)}-{tense}-{anchor}'}
            rows.append({**common_fields, 'id': f'modal-{len(rows):03}',
                'english': common + (expansion if contrast == 'careful' else bare),
                'ainglish': common + tagged,
                'question': 'Using only what the earlier statement establishes, are these two decisions licensed: recording a conduct violation if P happens; retaining not-P among live predicted outcomes? A decision not licensed here may be justified by other undisclosed information.',
                'options': ordered(answers, answer, frame + int(occurred) + (tense == 'ongoing') + anchor),
                'answer': answer, 'settlement_stratum': form + '-joint', 'probe': 'two-bit',
                'oracle': {'normative_violation_licensed': normative, 'epistemic_alternative_licensed': epistemic,
                           'future_outcome_does_not_change_prior_assertion': True},
                'token_pair': {'english': common + expansion, 'ainglish': common + tagged}})
    # Independent questions about four explicit non-entailments; not pooled with joint recovery.
    questions = {
        'physical-impossibility': 'Does this statement alone establish that P cannot physically happen?',
        'actual-nonoccurrence': 'Before observing any outcome, can this statement alone be used to report that not-P actually happened?',
        'permission-to-refrain': 'Does this statement alone grant its subject authorisation to refrain from P?',
        'absence-of-duty': 'Does this statement alone rule out every separate obligation to make P happen?',
    }
    for frame, (domain, animacy, subject, predicate) in enumerate(FRAMES):
        for form, (probe, question) in product(['prohibition', 'possibility'], questions.items()):
            context = ('This is an applicable conduct-code entry, not a forecast.' if form == 'prohibition'
                       else 'This is an epistemic forecast entry, not a conduct-code entry.')
            common = f'Fictional {domain} record. P means: {subject} will {predicate} tomorrow. {context} No outcome, physical-capability evidence, other obligation or authorisation is supplied. Statement: '
            expansion = (f'An applicable authority or rule forbids {subject.lower()} from satisfying P.' if form == 'prohibition'
                         else 'Under the speaker\'s current evidence or model, non-occurrence of P remains possible.')
            tagged = f'{subject} may-not-as-{form} {predicate} tomorrow.'
            rows.append({'id': f'modal-probe-{len(rows):03}', 'english': common + (expansion if contrast == 'careful' else f'{subject} may not {predicate} tomorrow.'),
                         'ainglish': common + tagged, 'question': question,
                         'options': ordered(['yes', 'no'], 'no', frame + (form == 'possibility')),
                         'answer': 'no', 'settlement_stratum': form + '-' + probe,
                         'form': form, 'probe': probe, 'frame': frame, 'domain': domain,
                         'oracle': {'unsupported_inference': True},
                         'diagnostic_limit': 'All four entailment probes are negative controls; acquiescence and no-bias limit generalisation.'})
    return rows + controls('modal-' + contrast)


QUOTA_DOMAINS = ['votes', 'uploads', 'bookings', 'dispatches', 'tickets', 'queries', 'prints', 'edits']


def fixed_violation(events, period, limit):
    totals = Counter()
    for t, n in events:
        totals[t // period] += n
    return any(n > limit for n in totals.values())


def rolling_violation(events, period, limit):
    # All maximal contents of a half-open interval can be witnessed by its first event.
    return any(sum(n for t, n in events if start <= t < start + period) > limit
               for start, _ in events)


def rolling_oracle_independent(events, period, limit):
    # Integer-minute instances: enumerate every candidate start instead of event endpoints.
    return any(sum(n for t, n in events if start <= t < start + period) > limit
               for start in range(min(t for t, _ in events) - period, max(t for t, _ in events) + 1))


def quota_rows(contrast):
    assert contrast in ('careful', 'bare')
    rows = []
    for domain_index, thing in enumerate(QUOTA_DOMAINS):
        limit = [8, 12, 16, 20, 24, 28, 32, 36][domain_index]
        for unit, period, variant, form in product(['hour', 'day@UTC'], [None], range(4), ['clock', 'any']):
            period = 60 if unit == 'hour' else 1440
            duration = '60m' if unit == 'hour' else '24h'
            # A timestamp is minutes after the declared UTC origin, with a complete event log.
            events = [
                [(period - 2, limit), (period + 2, limit)],
                [(period + 2, limit), (period + 4, limit)],
                [(period - 2, limit), (2 * period + 2, limit)],
                [(period - 2, limit // 2), (period + 2, limit // 2)],
            ][variant]
            common = (f'Fictional complete {thing} log, all times UTC. Origin t=0 is 2026-11-03 00:00 UTC; '
                      't is elapsed whole minutes. No other events occur in the surrounding two periods. '
                      + (f'The enforcer starts a fresh counter at t=0, {period}, {2*period}, and so on.' if form == 'clock' else
                         f'The enforcer keeps each event in its counter for {period} elapsed minutes; clock boundaries do not clear it.')
                      + f' Event log: {events[0][1]} {thing} at t={events[0][0]}, then {events[1][1]} at t={events[1][0]}. Limit: ')
            tagged = f'{limit} {thing} per-clock({unit}).' if form == 'clock' else f'{limit} {thing} per-any({duration}).'
            # Exact short full-English examples specified by the registered mapping, instantiated.
            expansion = (f'at most {limit} {thing} in each clock hour.' if form == 'clock' and unit == 'hour'
                         else f'at most {limit} {thing} in each UTC calendar day.' if form == 'clock'
                         else f'at most {limit} {thing} in any 60-minute span.' if unit == 'hour'
                         else f'at most {limit} {thing} in any 24-hour span.')
            english = common + (expansion if contrast == 'careful' else f'{limit} {thing} per {"hour" if unit == "hour" else "day"}.')
            bad = fixed_violation(events, period, limit) if form == 'clock' else rolling_violation(events, period, limit)
            answer = 'yes' if bad else 'no'
            rows.append({'id': f'quota-{len(rows):03}', 'english': english, 'ainglish': common + tagged,
                         'question': 'Did the second burst break the limit?',
                         'options': ordered(['yes', 'no', 'cannot tell'], answer, domain_index + variant),
                         'answer': answer, 'settlement_stratum': 'per-' + form,
                         'domain': thing, 'unit': unit, 'boundary_case': variant,
                         'semantic_cell': f'q-{domain_index}-{unit}-{variant}-{form}',
                         'oracle': {'events': events, 'period': period, 'limit': limit, 'breaks_limit': bad},
                         'token_pair': {'english': common + expansion, 'ainglish': common + tagged}})
    return rows + controls('quota-' + contrast)


def selfcheck():
    result = {}
    for name, rows in [('may-not-careful', modal_rows('careful')), ('may-not-bare', modal_rows('bare')),
                       ('quota-careful', quota_rows('careful')), ('quota-bare', quota_rows('bare'))]:
        targets = [r for r in rows if not r.get('calibration')]
        assert len({r['id'] for r in rows}) == len(rows)
        assert all(r['answer'] in r['options'] and len(r['options']) == len(set(r['options'])) for r in rows)
        assert all(r['english'] != r['ainglish'] for r in rows)
        if name.startswith('may-not'):
            assert Counter(r['form'] for r in targets if r['probe'] == 'two-bit') == {'prohibition': 80, 'possibility': 80}
        else:
            assert len(targets) == 128
            for r in targets:
                o = r['oracle']
                assert rolling_violation(o['events'], o['period'], o['limit']) == rolling_oracle_independent(o['events'], o['period'], o['limit'])
                # Independent fixed-window check specialised to two already ordered bursts.
                (a, x), (b, y) = o['events']
                independent = max(x, y, x+y if a//o['period'] == b//o['period'] else 0) > o['limit']
                assert independent == fixed_violation(o['events'], o['period'], o['limit'])
        result[name] = {'targets': len(targets), 'controls': len(rows)-len(targets),
                        'strata': dict(Counter(r['settlement_stratum'] for r in targets)), 'structural_checks': True}
    # The same anchored worlds, targets and keys are frozen for both comparators.
    for generator in [modal_rows, quota_rows]:
        a, b = generator('careful'), generator('bare')
        assert all(x['ainglish'] == y['ainglish'] and x['question'] == y['question'] and x['answer'] == y['answer'] for x, y in zip(a, b))
    return result


GENERATORS = {'may-not-careful': lambda: modal_rows('careful'), 'may-not-bare': lambda: modal_rows('bare'),
              'quota-careful': lambda: quota_rows('careful'), 'quota-bare': lambda: quota_rows('bare')}

if __name__ == '__main__':
    import json
    print(json.dumps(selfcheck(), indent=2))
