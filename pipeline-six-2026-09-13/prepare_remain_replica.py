"""Freeze a fresh source-preserving stock/flow replication; never calls a reader.

Source labels identify reader instruments, not the principal performing this run.
The filing principal will be Dexagon, not Saturnia. No source score is optimized.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
import urllib.request

from ainglish.panel import (arm_for, prepare_reader_instruments, reader_receipt,
                            _planned_panel_manifest)
from ainglish.reader_qualification import validate_screen
from ainglish.experiment_audit import audit_items
from local_colony_auth import ainglish_client

REPO = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent / 'remain-source-matched'
PID = 'a-xffrm7wz2wt3xhzf'
SOURCE = 'f6ea7793b22c101c1d3ada038db24ec58518e7a145c428e01081e827b2feead1'
ATTEMPT = '661695d7-6268-486e-bc20-3cf4552fd290'
DOMAINS = [('staffing', 'worker', 'workers'), ('rooms', 'visitor', 'visitors'),
           ('evacuation', 'responder', 'responders'), ('queues', 'job', 'jobs'),
           ('inventory', 'package', 'packages'), ('replicas', 'replica', 'replicas'),
           ('subscriptions', 'subscription', 'subscriptions'), ('fleets', 'sensor', 'sensors')]
# One focal member; the other members are varied independently of its boundary history.
PATTERNS = [
    ('arrival', False, [(9, True)], 1, 0),
    ('exit', True, [(16, False)], 0, 1),
    ('repeat-exit', True, [(8, False), (21, True), (32, False)], 0, 1),
    ('reentry', True, [(12, False), (37, True)], 1, 1),
    ('cutoff-exit', True, [(45, False)], 0, 0),
    ('start-exit', True, [(0, False)], 0, 1),
    ('unspecified-endpoint', True, [(45, False)], 0, None),
    ('no-flow', True, [], 1, 0),
]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def save(name, value):
    with (HERE / name).open('x', encoding='utf-8') as out:
        json.dump(value, out, indent=2, ensure_ascii=False, allow_nan=False)
        out.write('\n')


def fetch_json(url):
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)


def clock(offset):
    # The fresh scenario is a 45-minute interval rather than the source's hour.
    minute = 9 * 60 + 20 + offset
    return f'{minute // 60:02d}:{minute % 60:02d}'


def generate():
    HERE.mkdir(exist_ok=True)
    c = ainglish_client()
    offered = c.suggestions(proposal=PID)['suggestions']
    assert any(r.get('replicates_hash') == SOURCE and r.get('confirmation_capable') for r in offered)
    proposal = c.proposal(PID, authenticated=True)
    assert proposal['stage'] == 'measured' and not proposal['author_work_notices']['active']
    source = c.attempt_manifest(ATTEMPT)
    old = fetch_json(source['items_url'])
    assert isinstance(old, list) and digest(old) == source['items_sha256']
    save('remain-source-manifest.json', source)
    save('remain-source-items.json', old)
    save('remain-proposal-contract.json', {k: proposal[k] for k in
         ['public_id', 'slug', 'form', 'english_mapping', 'predicted_measurement', 'evidence_contract']})
    readers = [{k: v for k, v in r.items() if v != 'provider-default' and k != 'instrument_preparation'}
               for r in source['readers']]
    holder = {'panel': readers}
    prepare_reader_instruments(holder)
    inventory = [reader_receipt(r) for r in readers]
    access = c.reader_access(SOURCE, inventory)
    assert access['status'] == 'matching_inventory', access
    save('remain-reader-access.json', access)
    seed = source['seed']
    rng = random.Random(202609131705)
    items, worlds = [], []
    per_arm = Counter()
    for di, (domain, singular, plural) in enumerate(DOMAINS):
        for pi, (pattern, initial, events, stock_gold, flow_gold) in enumerate(PATTERNS):
            for variant in range(2):
                # Match the actual source's within-stratum population, including
                # its limitation: each form appears in four of the eight patterns.
                # A fully crossed design would be a different prospective study.
                form = 'remain-in' if pi % 2 == 0 else 'departed-from'
                probe = 'mode-and-count' if variant == 0 else 'membership-boundary'
                stratum = form + '-' + domain
                # New meaningful facts: stock and unique departures vary independently;
                # returning/repeated departures are not counted as independent members.
                stayers = (3 * di + pi + variant + 1) % 4
                leavers = (di + 3 * pi + variant + 2) % 4
                arrivals = (di + pi + variant + 1) % 2
                state = initial
                exited = False
                for t, inside in events:
                    assert state != inside
                    exited |= state and not inside and 0 <= t < 45
                    state = inside
                stock = stayers + arrivals + int(state)
                flow = leavers + int(exited)
                # Independent closed-form oracle for the focal contribution.
                assert int(state) == stock_gold
                if pattern != 'unspecified-endpoint':
                    assert int(exited) == flow_gold
                count = stock if form == 'remain-in' else flow
                noun = singular if count == 1 else plural
                scope = f'R-{domain}-{pi}-{variant}'
                context = (f'A fictional {domain} record uses scope {scope}. Membership means being '
                           f'in the defined set of qualifying {plural}; identity keys distinguish members. '
                           'The reference date is 2026-09-15 and all clock times are UTC. '
                           'The cutoff is 10:05, after all changes effective at that time. '
                           'Interval J is [09:20,10:05), with the start included and the end excluded. ')
                if form == 'remain-in':
                    marked = f'Exactly {count} {noun} remain-in({scope}) as_of(10:05Z).'
                    english = (f'Immediately after all changes effective at 10:05, exactly {count} distinct '
                               f'{noun} {"is" if count == 1 else "are"} inside {scope}.')
                else:
                    marked = f'Exactly {count} distinct {noun} departed-from({scope}) during(J).'
                    english = (f'Exactly {count} distinct {noun} changed from inside {scope} to outside '
                               f'{scope} at least once during J.')
                if probe == 'mode-and-count':
                    # Both resources are explicit. Never score the hidden ledger's other count.
                    question = ('The records desk creates one blue access slot per member inside at '
                                'cutoff, and one amber history card per distinct member that exited '
                                'during J. Which pair of totals is licensed by the report alone?')
                    a = f'Blue slots: {count}; amber cards: unknown.'
                    b = f'Blue slots: unknown; amber cards: {count}.'
                    options = [a, b, f'Blue slots: {count}; amber cards: {count}.', 'Both totals are unknown.']
                    gold = a if form == 'remain-in' else b
                else:
                    trajectory = 'The individual is initially ' + ('inside' if initial else 'outside') + '.'
                    trajectory += ''.join(f' At {clock(t)} the individual {"enters" if inside else "exits"}.'
                                          for t, inside in events)
                    trajectory += ' There are no other transitions before or at cutoff.'
                    endpoint = ('For this separate case ONLY, the interval ends at cutoff but whether '
                                'that endpoint is included is explicitly unspecified.' if pattern == 'unspecified-endpoint'
                                else 'This separate case uses the explicitly stated [09:20,10:05) interval.')
                    question = ('Consider a separate hypothetical individual under the same kind of count, '
                                'not an additional fact about the reported total. ' + trajectory + ' ' + endpoint +
                                ' How much does this individual contribute to the quantity the report counts?')
                    options = ['0 members', '1 member', '2 members', 'Cannot determine from the stated endpoint rule']
                    value = stock_gold if form == 'remain-in' else flow_gold
                    gold = options[3] if value is None else options[value]
                # Balance the actual hash-defined arm allocation before any reader call.
                target_arm = 'ainglish' if (pi // 2 + variant) % 2 == 0 else 'english'
                serial = 0
                while True:
                    ident = f'dex-sf13-{domain}-{pi}-{variant}-{serial}'
                    arms = [arm_for(seed, reader['name'], ident) for reader in readers]
                    if arms[0] == target_arm and arms[1] != arms[0]:
                        break
                    serial += 1
                    assert serial < 1000
                per_arm[stratum, target_arm] += 1
                distractors = [o for o in options if o != gold]
                rng.shuffle(distractors)
                distractors.insert((pi // 2 + variant) % 4, gold)
                items.append({'id': ident, 'english': context + english, 'ainglish': context + marked,
                              'question': question, 'options': distractors, 'answer': gold,
                              'settlement_stratum': stratum,
                              'strata': {'domain': domain, 'form': form, 'pattern': pattern, 'probe': probe,
                                         'world_id': ident}})
                worlds.append({'id': ident, 'domain': domain, 'pattern': pattern, 'form': form,
                               'probe': probe, 'focal_initial_inside': initial, 'events': events,
                               'other_stayers': stayers, 'other_distinct_leavers': leavers,
                               'other_arrivals': arrivals, 'stock': stock, 'distinct_flow': flow,
                               'focal_stock': stock_gold, 'focal_flow_when_endpoint_stated': int(exited),
                               'gold': gold})
    assert len(items) == 128 and len({i['id'] for i in items}) == 128
    assert Counter(i['settlement_stratum'] for i in items) == {s['id']: 8 for s in source['settlement_strata']}
    assert set(per_arm.values()) == {4} and len(per_arm) == 32
    assert Counter(i['strata']['probe'] for i in items) == {'mode-and-count': 64, 'membership-boundary': 64}
    axes = ('domain', 'form', 'probe', 'pattern')
    assert Counter(tuple(i['strata'][a] for a in axes) for i in items) == Counter(
        tuple(i[a] for a in axes) for i in old if not i.get('calibration'))
    old_pairs = {(i['english'], i['ainglish']) for i in old if not i.get('calibration')}
    assert not old_pairs.intersection((i['english'], i['ainglish']) for i in items)
    # All texts/questions were rebuilt around new counts, times and resource rules;
    # the world identities used for arm balancing are not the basis of freshness.
    controls = [deepcopy(i) for i in old if i.get('calibration')]
    assert len(controls) == 12
    items += controls
    save('remain-fresh-items.json', items)
    save('remain-fresh-worlds.json', worlds)
    audit = audit_items(items)
    assert audit['ok'], audit
    save('remain-structural-audit.json', audit)
    save('remain-design.json', {'source_hash': SOURCE, 'items_sha256': digest(items),
                              'real_items': 128, 'independent_worlds': 128, 'calibration_items': 12,
                              'source_complete_pair_overlap': 0, 'reader_calls': 0,
                              'reader_instruments': inventory, 'reader_principal': 'Dexagon',
                              'source_labels_preserved': 'Instrument names are not filing identities.',
                              'limitations': ['Eight shared event patterns are not 128 natural-language templates.',
                                              'Source form-pattern allocation is preserved, not fully crossed. Departed-from boundary probes do not test repeat-exit or unspecified endpoint.',
                                              'Only the careful-English component; no bare-word gain or trained-reader claim.',
                                              'Same host and exact models as source; different measurement principal and inputs.']})
    for index, reader in enumerate(readers):
        screen = {'kind': 'ainglish.reader-qualification-screen.v1',
                  'roster_id': source['models'][index], 'reader': reader,
                  'lineage': deepcopy(source['reader_qualifications'][index]['lineage']),
                  'validity_days': 7, 'min_gap_bps': 5000, 'min_recovered_bps': 10000,
                  'controls': [{'id': i['id'], 'detectable': i['ainglish'], 'other': i['english'],
                                'question': i['question'], 'options': i['options'], 'answer': i['answer']}
                               for i in controls]}
        validate_screen(screen)
        save(f'remain-reader-{index}-screen.json', screen)
    print('Fresh 128-world/128-item design and exact reader match frozen; no reader calls.')


def bind(commit):
    c = ainglish_client()
    source = json.loads((HERE / 'remain-source-manifest.json').read_text())
    contract = json.loads((HERE / 'remain-proposal-contract.json').read_text())
    live = c.proposal(PID, authenticated=True)
    assert {k: live[k] for k in contract} == contract
    assert (HERE / 'REMAIN-REVIEW.md').exists()
    items = json.loads((HERE / 'remain-fresh-items.json').read_text())
    readers, qualifications = [], []
    for index in range(2):
        screen = json.loads((HERE / f'remain-reader-{index}-screen.json').read_text())
        qualification = json.loads((HERE / f'remain-reader-{index}-qualification.json').read_text())
        assert qualification['status'] == 'passed'
        readers.append(screen['reader']); qualifications.append(qualification['receipt'])
    spec = {'slug': live['slug'], 'construct': source['construct'], 'form': live['form'],
            'metric': 'comprehension_accuracy_delta', 'replicates_hash': SOURCE,
            'seed': source['seed'], 'panel_neff': 2, 'panel': readers,
            'reader_qualifications': qualifications, 'items': items, 'items_sha256': digest(items),
            'items_url': 'https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/' + commit +
                         '/' + str(HERE.relative_to(REPO)) + '/remain-fresh-items.json',
            'comparator': deepcopy(source['comparator']),
            'settlement_strata': deepcopy(source['settlement_strata']),
            'calibration_min_gap': 0.5, 'calibration_min_recovered': 1, 'planted_arm': 'ainglish',
            'admissibility': {'kind': 'ainglish.panel.admissibility.v1', 'per_reader_calibration': True,
                              'max_off_option_cells': 0, 'max_absent_cells': 0,
                              'max_truncated_cells': 0, 'max_transport_fault_cells': 0},
            'study_purpose': 'claim_test', 'study_scope': source['study_scope'],
            'attempt': {'estimand': c.attempt(ATTEMPT)['pin']['estimand'],
                        'admissibility_gates': [
                            'Exact source f6ea7793 remains valid, unconfirmed, unretracted and offered to Dexagon for replication',
                            'Fresh proposal content equals the frozen contract, with no author hold or supersession',
                            '128 fresh worlds and one scored item per world; both forms/probes balanced 64/64; same 16 ordered equally weighted strata',
                            'Same exact two reader digests/settings, fresh valid qualification and full per-reader planted calibration before targets',
                            'New operational counts, times and question texts; no original complete pair reused; source hidden worlds not scored as premises',
                            'No retry, model replacement, threshold change or selective reporting; adverse/null/uncertain outcomes retained',
                            'Existing local models only; native SSD >20GiB free; no other active local inference connection at start',
                        ],
                        'planned_sample': {'scientific_items': 128, 'independent_worlds': 128,
                                           'calibration_items': 12, 'readers': 2,
                                           'scientific_cells': 256, 'calibration_cells': 48,
                                           'settlement_strata': source['settlement_strata'],
                                           'replicates_hash': SOURCE}}}
    prepare_reader_instruments(spec)
    planned = _planned_panel_manifest(spec)
    assert planned['readers'] == source['readers']
    assert planned['settlement_strata'] == source['settlement_strata']
    preflight = c.preflight_attempt(spec['slug'], planned, **spec['attempt'])
    save('remain-runspec.json', spec)
    save('remain-planned-manifest.json', planned)
    save('remain-preflight.json', preflight)
    print(json.dumps(preflight, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['generate', 'bind'])
    parser.add_argument('--commit')
    args = parser.parse_args()
    if args.phase == 'generate': generate()
    else:
        assert args.commit and len(args.commit) == 40
        bind(args.commit)
