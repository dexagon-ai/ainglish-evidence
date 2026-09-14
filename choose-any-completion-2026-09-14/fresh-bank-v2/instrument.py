"""Fresh, unlaunched study instrument. No inference, network, credentials or old imports.

The menu and all shared facts are built without a requested form. Assignment is a separate
operation over a previously committed neutral artifact. The retained rejected bank and excluded
witnesses are NOT target inputs. See SEMANTICS.md for the reviewed meaning of the calculations.
"""
from collections import Counter
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parent
WORLD_SEED = 2026091461
ASSIGNMENT_SEED = 2026091462
PANEL_SEED = 2026091451
FORMS = ('choose-any', 'draw-uniform')
POLICIES = ('constant-first', 'criterion-based', 'unequal-weight', 'equal-probability', 'out-of-set')
GUARANTEES = ('one-eligible', 'equal-odds', 'crypto-unpredictable', 'cross-draw-independent')
DOMAINS = (
    ('service-routing', 'service endpoint', 'latency', (
        'a document-preview request', 'a currency-cache lookup', 'an image-thumbnail request',
        'a parcel-status query', 'a metadata lookup', 'an account-notification request')),
    ('reviewer-assignment', 'reviewer', 'queue length', (
        'a methods manuscript', 'a replication report', 'a registered protocol',
        'a dataset description', 'a conference abstract', 'a software-note review')),
    ('evaluation-item-selection', 'evaluation item', 'preparation cost', (
        'a navigation evaluation slot', 'a factuality evaluation slot', 'a planning evaluation slot',
        'a retrieval evaluation slot', 'a translation evaluation slot', 'a reasoning evaluation slot')),
    ('failover', 'standby node', 'activation cost', (
        'a stopped log collector', 'an unavailable cache', 'a failed indexing job',
        'an interrupted export', 'an offline job dispatcher', 'a failed telemetry worker')),
    ('content-choice', 'content item', 'retrieval cost', (
        'a catalogue illustration slot', 'an onboarding example slot', 'a tutorial excerpt slot',
        'a public showcase slot', 'a demo soundtrack slot', 'an exhibition caption slot')),
    ('resource-allocation', 'worker', 'current load', (
        'a checksum job', 'a report-rendering job', 'a video-transcoding job',
        'a search-index job', 'an archive-verification job', 'a batch-compression job')),
)
FRAMES = (
    'A selection memo for {task} is being checked before dispatch.',
    'At a handover, the team needs to interpret a request concerning {task}.',
    'A selection interface has received a new instruction about {task}.',
    'An engineer is comparing proposed procedures for {task}.',
    'An audit record asks what the instruction for {task} actually requires.',
    'A supervisor has supplied the following selection contract for {task}.',
    'Before implementing the next request, a team reviews the selection for {task}.',
    'The instruction in a pending work ticket concerns {task}.',
    'A dispatch review separates permitted procedures from promised properties for {task}.',
    'A test-plan author is reading the request for {task}, not observing its outcome.',
    'The next operation requires interpretation of the selection instruction for {task}.',
    'A colleague asks which procedures meet the recorded request about {task}.',
)
NAMES = ('Alder', 'Bracken', 'Cinder', 'Delta', 'Ember', 'Fennel', 'Garnet', 'Hickory',
         'Indigo', 'Jasper', 'Kelvin', 'Laurel', 'Mallow', 'Nimbus', 'Opal', 'Plover')

def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()

def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()

def write(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n')

def expansion(form, world):
    ref, n = world['set_ref'], world['n']
    if form == 'choose-any':
        return (f'Choose exactly one member of {ref}; every member is acceptable and the selection '
                'policy is otherwise unconstrained. A deterministic first-member rule, a criterion-based '
                'rule, a weighted rule, or a uniform draw may be used. This makes no claim of randomness, '
                'equal probability, unpredictability, independence, rotation, or fairness.')
    if form == 'draw-uniform':
        return (f'Make exactly one stochastic draw from {ref}. Conditional on this frozen eligibility '
                f'set and before the outcome is known, each distinct member identity has probability '
                f'exactly 1/{n} of being returned. This does not by itself promise cryptographic '
                'unpredictability, public verifiability, independence between repeated draws, sampling '
                'with or without replacement, or a balanced finite run; it specifies one draw only.')
    raise ValueError(form)

def permitted(form, world, distribution):
    """Finite distribution semantics, not a score inferred from the menu or policy's name."""
    p = {key: Fraction(value) for key, value in distribution.items()}
    if sum(p.values()) != 1 or any(v < 0 for v in p.values()):
        raise ValueError('Invalid probability distribution')
    positive_support = {key for key, probability in p.items() if probability > 0}
    if not positive_support.issubset(set(world['members'])):
        return False
    if form == 'choose-any':
        return True
    if form == 'draw-uniform':
        return all(p.get(member, 0) == Fraction(1, world['n']) for member in world['members'])
    raise ValueError(form)

def neutral_world(domain_index, local_index):
    domain, member_type, criterion, tasks = DOMAINS[domain_index]
    wid = f'ca2-world-{domain_index + 1:02d}-{local_index + 1:02d}'
    rng = random.Random(f'{WORLD_SEED}:{wid}')
    n = 2 + (local_index + 3 * domain_index) % 7
    suffix = hashlib.sha256(wid.encode()).hexdigest()[:5]
    members = [f'{name}-{suffix}' for name in rng.sample(NAMES, n)]
    outsider = 'Unlisted-'+suffix
    scores = rng.sample(range(2, 97), n)
    # Ensure criterion and constant-first are different procedures, before any form assignment.
    if scores.index(min(scores)) == 0:
        scores[0], scores[-1] = scores[-1], scores[0]
    high_weight = 2 + local_index % 3
    weighted_index = rng.randrange(n)
    denominator = n - 1 + high_weight
    ref = 'eligibility-'+suffix+'@frozen-2'
    task = tasks[local_index % len(tasks)]
    frame = local_index % len(FRAMES)
    common = (FRAMES[frame].format(task=task)+'\n'
              f'The eligible {member_type} identities, in their recorded order, are {", ".join(members)}. '
              f'Their {criterion} scores in the same order are {", ".join(map(str, scores))}. '
              f'{ref} uniquely names this finite, nonempty snapshot of distinct identities. '
              f'That snapshot is fixed before the selection; {outsider} is outside it. '
              'No other selection requirement has been added, and no result has yet been observed.')
    world = {'id': wid, 'domain': domain, 'frame_family': f'new-frame-{frame:02d}',
             'task_family': task, 'n': n, 'members': members, 'outsider': outsider,
             'scores': scores, 'criterion': criterion, 'set_ref': ref, 'context': common,
             'weighted_index': weighted_index, 'high_weight': high_weight}
    minimum = members[scores.index(min(scores))]
    policies = [
        {'kind': 'constant-first', 'text': f'Returns {members[0]} on every execution, with probability one.',
         'distribution': {members[0]: '1'}},
        {'kind': 'criterion-based', 'text': f'Returns {minimum}, which has the unique lowest {criterion} score, with probability one.',
         'distribution': {minimum: '1'}},
        {'kind': 'unequal-weight', 'text': f'Assigns probability {high_weight}/{denominator} to {members[weighted_index]} '
         f'and 1/{denominator} to each other listed identity, then returns one draw from that distribution.',
         'distribution': {x: str(Fraction(high_weight if j == weighted_index else 1, denominator))
                          for j, x in enumerate(members)}},
        {'kind': 'equal-probability', 'text': f'Assigns probability 1/{n} to each distinct listed identity before drawing and returning exactly one.',
         'distribution': {x: str(Fraction(1, n)) for x in members}},
        {'kind': 'out-of-set', 'text': f'Returns {outsider} on every execution, with probability one.',
         'distribution': {outsider: '1'}},
    ]
    guarantees = [
        {'key': 'one-eligible', 'text': 'Exactly one identity is returned, and it belongs to the frozen eligible set.'},
        {'key': 'equal-odds', 'text': 'Before this selection, every distinct eligible identity has the same probability of being returned.'},
        {'key': 'crypto-unpredictable', 'text': 'A well-informed adversary cannot predict the result better than chance.'},
        {'key': 'cross-draw-independent', 'text': 'Learning this result leaves the probability distribution of a later selection unchanged.'},
    ]
    rng.shuffle(policies)
    rng.shuffle(guarantees)
    for i, p in enumerate(policies, 1): p['label'] = 'P'+str(i)
    for i, g in enumerate(guarantees, 1): g['label'] = 'G'+str(i)
    policy_contrast = POLICIES[(local_index + domain_index) % 5]
    guarantee_contrasts = {form: GUARANTEES[(local_index + domain_index + j) % 4]
                           for j, form in enumerate(FORMS)}
    gold = {}
    profiles = []
    for form in FORMS:
        allowed = {p['label'] for p in policies if permitted(form, world, p['distribution'])}
        true_keys = {'one-eligible'} | ({'equal-odds'} if form == 'draw-uniform' else set())
        established = {g['label'] for g in guarantees if g['key'] in true_keys}
        gold[form] = {'policies': sorted(allowed), 'guarantees': sorted(established)}
        toggle_p = next(p['label'] for p in policies if p['kind'] == policy_contrast)
        toggle_g = next(g['label'] for g in guarantees if g['key'] == guarantee_contrasts[form])
        for pset in (allowed, allowed ^ {toggle_p}):
            for gset in (established, established ^ {toggle_g}):
                profiles.append({'policies': sorted(pset), 'guarantees': sorted(gset)})
    rng.shuffle(profiles)
    def label(record):
        return ('Implementations: '+(', '.join(record['policies']) or 'none')+
                '; claims: '+(', '.join(record['guarantees']) or 'none')+'.')
    options = [label(r) for r in profiles]
    assert len(set(options)) == 8
    question = ('Evaluate two complete lists: implementations that satisfy the request, and claims '
                'that follow from the request itself. Select the answer record containing BOTH complete lists. '
                'A permitted procedure may have extra properties that the request does not guarantee.\n\n'
                'Candidate implementations (each returns exactly once):\n'+
                '\n'.join(p['label']+': '+p['text'] for p in policies)+
                '\n\nClaims an auditor might make:\n'+
                '\n'.join(g['label']+': '+g['text'] for g in guarantees))
    world.update(question=question, options=options, option_records=dict(zip(options, profiles)),
                 policies=policies, guarantees=guarantees, gold_by_form=gold,
                 policy_contrast=policy_contrast, guarantee_contrasts=guarantee_contrasts)
    return world

def neutral_bank():
    return [neutral_world(d, i) for i in range(24) for d in range(6)]

def project(world, form, *, audit=False):
    gold = world['gold_by_form'][form]
    answer, = [label for label, record in world['option_records'].items() if record == gold]
    return {'id': world['id']+(('/'+form) if audit else ''),
            'english': world['context']+'\nRequest: '+expansion(form, world),
            'ainglish': world['context']+f'\nRequest: {form}({world["set_ref"]}).',
            'question': world['question'], 'options': deepcopy(world['options']), 'answer': answer,
            'settlement_stratum': form, 'domain': world['domain'], 'frame_family': world['frame_family'],
            'member_count': world['n'], 'world_id': world['id'],
            'semantic_world': {k: deepcopy(world[k]) for k in ('n','members','outsider','scores','criterion','set_ref')},
            'probe_contract': {'kind': 'common-eight-record-complete-lists-v2',
                'option_records': deepcopy(world['option_records']), 'policies': deepcopy(world['policies']),
                'guarantees': deepcopy(world['guarantees']), 'gold': deepcopy(gold)},
            'status': 'AUDIT_ONLY_COUNTERFACTUAL' if audit else 'REVIEW_REQUIRED_NOT_LAUNCH_APPROVAL'}

def assign(worlds):
    """One published prospective seed, no reroll or outcome-based balancing."""
    mapping = {}
    for domain, *_ in DOMAINS:
        ids = sorted(w['id'] for w in worlds if w['domain'] == domain)
        random.Random(f'{ASSIGNMENT_SEED}:{domain}').shuffle(ids)
        mapping.update({wid: FORMS[i // 12] for i, wid in enumerate(ids)})
    return mapping

def opportunities(item):
    out = []
    for field, key in (('policies','kind'), ('guarantees','key')):
        for entry in item['probe_contract'][field]:
            offered = {entry['label'] in record[field] for record in item['probe_contract']['option_records'].values()}
            if offered == {True, False}: out.append(entry[key])
    return out

if __name__ == '__main__':
    # Phase 1 only. Assignment is deliberately not called before the neutral artifact is committed.
    worlds = neutral_bank()
    value = {'status': 'NEUTRAL_REVIEW_FREEZE_NO_REQUEST_ASSIGNMENT', 'worlds_sha256': digest(worlds),
             'world_seed': WORLD_SEED, 'assignment_seed_planned': ASSIGNMENT_SEED,
             'worlds': worlds}
    write('neutral-worlds.json', value)
    print(json.dumps({'worlds':len(worlds),'worlds_sha256':digest(worlds),'requested_forms_assigned':0}))
