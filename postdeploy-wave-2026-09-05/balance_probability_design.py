"""Prospective v2: remove all-first answers and all-no extra-information probes."""
from collections import Counter, defaultdict
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXTRA = {
    'payout': ('A separate contract states a net payout of four units per unit staked if the event occurs.',
               'Does this message separately specify a bookmaker payout?'),
    'calibration': ('A separate held-out calibration audit reports that this model met its declared calibration tolerance on the audited population.',
                    'Does this message include a separate calibration assessment?'),
    'frequency': ('A separate observation log records that the event occurred in four of ten observed trials.',
                  'Does this message separately state an observed event frequency?'),
    'causation': ('A separate investigator statement attributes the event to cause C; this is a causal claim, not proof that the investigator is right.',
                  'Does this message include a separate causal claim?'),
    'rounding': ('A separate precision note says the supplied probability estimate was rounded to the nearest whole percentage point.',
                 'Does this message separately state a rounding rule?'),
}


def main():
    source = ROOT / 'token-studies/probability.comprehension-design.json'
    old = json.loads(source.read_text())
    rows = deepcopy(old['items'])
    groups = defaultdict(list)
    for row in rows:
        row['id'] = row['id'].replace('prob-prospective-', 'prob-balanced-v2-')
        groups[row['form'], row['probe']].append(row)
    for (form, probe), group in groups.items():
        for index, row in enumerate(group):
            values = row['options']
            gold = row['answer']
            if probe in EXTRA:
                statement, row['question'] = EXTRA[probe]
                has_extra = index % 2 == 0
                if has_extra:
                    for arm in ['english', 'ainglish']:
                        row[arm] += ' ' + statement
                values = ['yes', 'no']
                gold = 'yes' if has_extra else 'no'
                row['audit']['separately_supplied_information'] = has_extra
                # This is about the message, not proof that an external claim is correct.
                assert (statement in row['english']) == has_extra
                assert (statement in row['ainglish']) == has_extra
            labels = list('ABCD')[:len(values)]
            # Position and the supplied-information bit vary independently.
            position = (index // 2) % 2 if probe in EXTRA else index % len(values)
            alternatives = [v for v in values if v != gold]
            alternatives.insert(position, gold)
            row['audit']['answer_meanings'] = dict(zip(labels, alternatives))
            row['audit']['semantic_gold'] = gold
            row['options'] = labels
            row['answer'] = labels[position]
            row['question'] += ' Answer with one option letter. ' + ' '.join(
                f'{label} = {meaning}.' for label, meaning in zip(labels, alternatives))
            row['settlement_stratum'] = form + ':' + probe
            assert row['audit']['answer_meanings'][row['answer']] == gold
            if probe in ['probability', 'complement']:
                p = Fraction(row['audit']['probability'])
                assert Fraction(gold) == (p if probe == 'probability' else 1 - p)
        assert max(Counter(r['answer'] for r in group).values()) - min(Counter(r['answer'] for r in group).values()) <= 1
        if probe in EXTRA:
            assert Counter(r['audit']['semantic_gold'] for r in group) == {'yes': 4, 'no': 4}
    output = {
        'items': rows,
        'invalid_boundary_cases': old['invalid_boundary_cases'],
        'previous_design_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'validated_items': len(rows),
        'reader_calls': 0,
        'status': 'Prospective design, not a preregistered or measured panel.',
        'changes': 'Opaque options balanced within each form/probe; extra-information questions now balance supplied/absent facts equally in both language arms. Earlier design retained without inference.',
        'gates': ['independent confirmation of the token prerequisite', 'fresh panel/control plan and reader qualification', 'public freeze and mint before any calls'],
        'limits': 'Authored mathematical and reported-information cases, not actual calibration, causal or bookmaker investigations. Never pool auxiliary information probes into numeric conversion accuracy.',
    }
    with (ROOT / 'token-studies/probability.comprehension-design-v2.json').open('x') as f:
        json.dump(output, f, indent=2)
        f.write('\n')
    print(len(rows), 'prospective items; every auxiliary form/probe has 4 yes and 4 no; zero inference')


if __name__ == '__main__':
    main()
