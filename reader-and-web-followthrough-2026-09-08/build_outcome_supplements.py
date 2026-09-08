"""Prospective complements to the 240-item panels; never alter their frozen bytes."""
from fractions import Fraction
from itertools import product
import json
from pathlib import Path
from build_readers import freeze

ROOT = Path(__file__).resolve().parent
for comparator, seed in [('careful', 2026090884), ('compact', 2026090885)]:
    source = json.loads((ROOT / ('outcome-' + comparator) / 'items.json').read_text())
    items = []
    options = [f'Under D, probability of x exceeds one half: {a}; statement certifies that D models reality correctly: {b}.'
               for a, b in product(['yes', 'no'], repeat=2)]
    for old in source:
        if old.get('calibration') or old['variant'] not in [0, 2]:
            continue
        oracle = old['oracle']
        mass = Fraction(oracle['masses'].get(oracle['value'], '0'))
        answer = f'Under D, probability of x exceeds one half: {"yes" if mass > Fraction(1, 2) else "no"}; statement certifies that D models reality correctly: no.'
        offset = len(items) % 4
        items.append({'id': 'majority-' + old['id'], 'english': old['english'], 'ainglish': old['ainglish'],
                      'question': 'Using the exact stated distribution, is the probability of x STRICTLY greater than one half? Separately, does the statistic statement itself certify that D correctly represents reality?',
                      'options': options[offset:] + options[:offset], 'answer': answer,
                      'settlement_stratum': old['settlement_stratum'], 'domain': old['domain'], 'boundary': old['boundary'],
                      'variant': old['variant'], 'oracle': {'mass_of_x': str(mass), 'majority': mass > Fraction(1, 2), 'certifies_model': False},
                      'shared_world_with': old['id']})
    assert len(items) == 120
    freeze('outcome-majority-' + comparator, 'outcome', items,
           'Separately frozen majority-probability and model-certification diagnostic. 120 authored worlds per comparator, 60 per predicate; two fixed cached readers. Worlds are a prespecified subset of the main packet, so this is neither an independent replication nor 120 new independent scenarios. Same common definitions and arms; two-bit question directly tests the below/at/above one-half distinction omitted by the main four-bit question.',
           'diagnostic', {'kind': 'outcome-' + comparator + '-shared-definition-v1', 'description': 'Exactly the same comparator and shared definition exposure as the main ' + comparator + ' packet; different, separately reported question.'},
           seed, ['Exact supplementary question and golds require independent semantic review before execution; main-packet approval alone is insufficient',
                  'Do not pool the simpler two-bit diagnostic into the primary four-bit scalar or use it to rescue failed primary noninferiority',
                  'Report exact-vector, majority and false-model-certification counts by predicate, boundary, domain and reader, with denominators'])

old = json.loads((ROOT.parent / 'night-progression-2026-09-07/full-claim/outcome-specification-diagnostics.json').read_text())
scope = ('Shared scope rule for this registered version: D must uniquely identify a fixed, nonempty, finite discrete probability distribution over numeric values in one declared quantity and unit; positive exact masses sum to one. Relevant model version and conditioning must be fixed. Partial, rounded-without-an-exact-interpretation, continuous, infinite-support, unordered-category and ambiguous specifications are outside this version. A specification can be sufficient even when the asserted statistic value is false. ')
for item in old:
    item['id'] = 'followthrough-' + item['id']
    for arm in ['english', 'ainglish']:
        item[arm] = scope + item[arm]
assert len(old) == 32
freeze('outcome-specification', 'outcome', old,
       '32-item diagnostic of this registered version’s specification boundary. Eight classes per predicate, including a sufficient-model control; identical finite-discrete scope supplied to both arms. Not a test of general mathematical validity, not the primary comprehension scalar, and not an independent replication. Two fixed cached readers.',
       'diagnostic', {'kind': 'careful-english-shared-scope-v1', 'description': 'Equal visible scope rules and complete model descriptions; evaluability question rather than truth of the claimed statistic.'},
       2026090886, ['Independent review must cover exact scope wording and all diagnostic golds before execution',
                   'Report sufficient-control accuracy separately from rejection of insufficient descriptions; preserve every class; do not pool into the primary scalar'])
