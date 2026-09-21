"""Exposed review-fixture repair, not reader qualification or a target experiment."""
from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PRIOR = ROOT.parent / 'they-controls-review-v2-2026-09-18/controls.py'
assert hashlib.sha256(PRIOR.read_bytes()).hexdigest() == '7d934c5fccc8b35458361324ab323050f32c4868f52a60522533da44130d1402'
spec = importlib.util.spec_from_file_location('review_controls_v2', PRIOR)
V2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(V2)
BASE, FORMS, LABELS, SPECS = V2.BASE, V2.FORMS, V2.LABELS, V2.SPECS
RULE = {'explicit_fact': {'numerator': 9, 'denominator': 10},
        'partial_information': {'numerator': 9, 'denominator': 10}}


def additions():
    return [
        ('gender', 'they-one',
         "The referent is one person. A verified profile fragment records the person's job title and residence. The profile's gender field is not included in the available fragment."),
        ('known_identity', 'they-one',
         "The report concerns one referent. The recorder has checked the identity document's issuing authority. The record does not state whether the recorder knows which person the document belongs to."),
        ('collective_action', 'they-one',
         "The referent is one ensemble with five members. The reported activity is the full rehearsal. The event record shows two members performing one segment together. It gives no coordination information about the other segments or members."),
        ('unanimity', 'they-many',
         "The referents are two committees, each with five members. The available ballot record states that all members of the first committee voted in favour. It lists four members of the second committee as voting in favour. The fifth member's position is not recorded."),
        ('all_members_participation', 'they-many',
         "The referents are two teams, each with five members. The available task record shows all members of the first team and four members of the second personally performing a task step. It does not record whether the fifth member of the second team performed any step."),
    ]


def build():
    result = V2.build()
    for dimension, form, text in additions():
        world = 'partial/' + form + '/' + dimension
        for rotation in range(3):
            result['items'].append({
                'id': f'{world}/{dimension}/order-{rotation}', 'world_id': world,
                'form_slot': form, 'dimension': dimension, 'role': 'underdetermined',
                'coverage_family': 'partial_information',
                'text': 'Fictional control record. ' + text,
                'question': SPECS[dimension]['question'],
                'options': LABELS[rotation:] + LABELS[:rotation], 'gold': LABELS[2],
                'exposure': 'standalone shared-context control concept; no target marker in prompt',
            })
    result.update(kind='ainglish.nonclaim-control-review-fixtures.v3',
                  original_v2_items_preserved=201,
                  semantic_worlds=len({x['world_id'] for x in result['items']}),
                  semantic_question_probes=len({(x['world_id'], x['question']) for x in result['items']}),
                  prompt_variants=len(result['items']), fixture_rule=deepcopy(RULE))
    result['floor_boundary'] = 'Executable synthetic review-fixture floors only; not confidence bounds, a qualification receipt or permission to execute the shelved study.'
    return result


def check(rows, seen, floor):
    answered = [x for x in rows if x['id'] in seen and seen[x['id']]['answer'] is not None]
    correct = sum(seen[x['id']]['answer'] == x['gold'] for x in answered)
    complete = bool(rows) and len(answered) == len(rows)
    # Exact integer comparison. Missing responses or missing coverage cannot pass.
    passed = complete and correct * floor['denominator'] >= len(rows) * floor['numerator']
    return {'planned_prompts': len(rows), 'semantic_worlds': len({x['world_id'] for x in rows}),
            'answered': len(answered), 'correct': correct, 'absent': len(rows)-len(answered),
            'coverage_present': bool(rows), 'floor': deepcopy(floor),
            'status': 'incomplete' if not complete else 'pass' if passed else 'fail'}


def score(fixtures, observations):
    if fixtures.get('fixture_rule') != RULE:
        raise ValueError('Missing or changed frozen review-fixture rule')
    result = V2.score(fixtures, observations)  # Validates observation schema/uniqueness.
    seen = {x['item_id']: x for x in observations}
    for endpoint in result['endpoints']:
        items = [x for x in fixtures['items'] if x['form_slot'] == endpoint['form_slot']
                 and x['dimension'] == endpoint['dimension']]
        checks = {
            'explicit_fact': check([x for x in items if x['role'] == 'explicit_fact'], seen, RULE['explicit_fact']),
            'partial_information': check([x for x in items if x.get('coverage_family') == 'partial_information'], seen, RULE['partial_information']),
        }
        statuses = {x['status'] for x in checks.values()}
        endpoint['fixture_checks'] = checks
        endpoint['fixture_status'] = 'fail' if 'fail' in statuses else 'incomplete' if 'incomplete' in statuses else 'pass'
    statuses = {x['fixture_status'] for x in result['endpoints']}
    result['kind'] = 'ainglish.control-fixture-score.v3'
    result.pop('complete_is_not_passed', None)  # Replaced by the actual separate decision.
    result['fixture_acceptance'] = {
        'status': 'fail' if 'fail' in statuses else 'incomplete' if 'incomplete' in statuses or not result['complete'] else 'pass',
        'failed_endpoints': [x['form_slot'] + '/' + x['dimension'] for x in result['endpoints'] if x['fixture_status'] == 'fail'],
        'incomplete_endpoints': [x['form_slot'] + '/' + x['dimension'] for x in result['endpoints'] if x['fixture_status'] == 'incomplete' or not x['complete']],
        'instrument_qualified': False,
        'boundary': 'Synthetic review-fixture decision only. These small exposed worlds and rotations do not certify accuracy, uncertainty, fresh inputs, provenance or execution. The author shelved the full study.',
    }
    return result


def witnesses(fixtures):
    choices = {'constant-semantic/' + label: (lambda x, label=label: label) for label in LABELS}
    choices.update({'constant-position/' + str(i): (lambda x, i=i: x['options'][i]) for i in range(3)})
    choices['question-blind-record-polarity'] = lambda x: V2.text_only(x['text'])
    for label in LABELS[:2]:
        choices['oracle-except-partial/' + label] = lambda x, label=label: label if x.get('coverage_family') == 'partial_information' else x['gold']
    return {name: score(fixtures, BASE.fixture_answers(fixtures, fn)) for name, fn in choices.items()}
