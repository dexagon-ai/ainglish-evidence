"""Prospective component diagnostic; not a rerun of the held bare-English panel.

No inference here. Rule-selection and small-number counter tasks are distinct
strata, never pooled into a claim-completion judgement. Both arms have identical
context. The rule-selection arm has no event arithmetic; the arithmetic arm
explicitly states the enforcer's rule, so it need not infer it from the marker.
"""
from collections import Counter
from itertools import product


def ordered(options, answer, index):
    rest = [x for x in options if x != answer]
    rest.insert(index % len(options), answer)
    return rest


def fixed(events, limit):
    counts = Counter()
    for minute, count in events:
        counts[minute // 60] += count
    return any(n > limit for n in counts.values())


def rolling(events, limit):
    return any(sum(n for t, n in events if start <= t < start + 60) > limit
               for start, _ in events)


def enumerated(events, limit, form):
    if form == 'clock':
        starts = range(0, 240, 60)
    else:
        starts = range(min(t for t, _ in events) - 60, max(t for t, _ in events) + 1)
    return any(sum(n for t, n in events if start <= t < start + 60) > limit for start in starts)


DOMAINS = ['stamps', 'rentals', 'scans', 'exports', 'drawings', 'signals', 'claims', 'samples']


def items():
    rows = []
    for domain_index, domain in enumerate(DOMAINS):
        limit = 2 + domain_index % 4
        for form, variant in product(['clock', 'any'], range(4)):
            english = f'At most {limit} {domain} in ' + ('each clock hour.' if form == 'clock' else 'any 60-minute span.')
            marked = f'{limit} {domain} ' + ('per-clock(hour).' if form == 'clock' else 'per-any(60m).')
            prefix = f'Fictional {domain} rule, clock hours begin at minute 00 in UTC. Rule: '
            correct = ('A fresh allowance begins at each UTC clock-hour boundary.' if form == 'clock'
                       else 'Every elapsed 60-minute window must respect the allowance, even across a clock-hour boundary.')
            options = ['A fresh allowance begins at each UTC clock-hour boundary.',
                       'Every elapsed 60-minute window must respect the allowance, even across a clock-hour boundary.',
                       'Unused allowance accumulates forever and can be spent later.']
            # Distinct task wording, without a hidden intended reading or event calculation.
            questions = ['Which enforcement rule does the sentence specify?',
                         'Which counter policy follows from the stated rule?',
                         'An implementer reads only this rule. Which constraint is specified?',
                         'Which of these descriptions preserves the rule?']
            rows.append({'id': f'qd-rule-{domain_index}-{form}-{variant}',
                'english': prefix + english, 'ainglish': prefix + marked,
                'question': questions[variant], 'options': ordered(options, correct, domain_index + variant),
                'answer': correct, 'settlement_stratum': form + '-rule',
                'form': form, 'task': 'rule-selection', 'domain': domain, 'variant': variant,
                'oracle': {'policy': form, 'calculation_required': False}})

            # The condition set includes a crossing boundary, a same-hour excess,
            # a gap longer than one hour, and an exactly-at-limit case.
            events = [[(57, limit), (63, limit)], [(63, limit), (66, 1)],
                      [(57, limit), (123, limit)], [(57, 1), (63, limit - 1)]][variant]
            schedule = ', then '.join(f'{n} {domain} at {t//60:02d}:{t%60:02d} UTC' for t, n in events)
            enforcer = ('The counter resets to zero at 00:00, 01:00, 02:00 UTC and each subsequent clock hour.'
                        if form == 'clock' else 'Each event stays in the counter for 60 elapsed minutes; a clock-hour boundary does not reset it.')
            prefix = (f'Complete fictional {domain} log on one UTC day: {schedule}. No other events occur. '
                      + enforcer + ' A count greater than the allowance is a violation; equality is permitted. Rule: ')
            bad = fixed(events, limit) if form == 'clock' else rolling(events, limit)
            assert bad == enumerated(events, limit, form)
            answer = 'yes' if bad else 'no'
            rows.append({'id': f'qd-counter-{domain_index}-{form}-{variant}',
                'english': prefix + english, 'ainglish': prefix + marked,
                'question': 'Did the second event exceed the allowance?',
                'options': ordered(['yes', 'no', 'not enough information'], answer, domain_index + variant),
                'answer': answer, 'settlement_stratum': form + '-counter',
                'form': form, 'task': 'explicit-counter', 'domain': domain, 'variant': variant,
                'oracle': {'events': events, 'limit': limit, 'violated': bad}})
    # Ten new, target-independent sensitivity controls. These are not target
    # competence tests and do not show the gold answer in either arm.
    people = ['Ari', 'Bela', 'Cleo', 'Daru', 'Etta']
    for i in range(10):
        a, b = people[i % 5], people[(i + 1) % 5]
        rows.append({'id': f'qd-control-{i}', 'calibration': True,
            'calibration_scope': 'target-independent', 'calibration_construct': 'resolved custody',
            'english': f'Parcel QD-{i+21} was collected by {a} or {b}; the register does not say which.',
            'ainglish': f'Parcel QD-{i+21} was collected by {a}, not {b}.',
            'question': f'Who collected parcel QD-{i+21}?',
            'options': ordered(people + ['not determined'], a, i), 'answer': a})
    return rows


def selfcheck():
    rows = items(); target = [r for r in rows if not r.get('calibration')]
    assert len(target) == 128
    assert Counter(r['settlement_stratum'] for r in target) == dict.fromkeys(
        ['clock-rule', 'any-rule', 'clock-counter', 'any-counter'], 32)
    for row in rows:
        assert row['answer'] in row['options']
        assert len(set(row['options'])) == len(row['options'])
    return {'target_items': 128, 'controls': 10, 'strata': dict(Counter(r['settlement_stratum'] for r in target)),
            'counter_oracles_agree': True, 'scope': 'Authored component diagnostics, not natural-use samples or independent confirmation.'}


if __name__ == '__main__':
    import json
    print(json.dumps(selfcheck(), indent=2))
