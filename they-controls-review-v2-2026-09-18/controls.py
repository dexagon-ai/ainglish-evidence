"""Prospective control-coverage witnesses; no inference, bank or SDK filing.

Retain the accepted v1 meanings and observations, add missing uncertainty cases
and same-record/different-question pairs. Rotations and questions stay grouped
by semantic world. These exposed review examples are not unseen target items.
"""
from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent/'they-controls-review-2026-09-17/controls.py'
assert hashlib.sha256(OLD.read_bytes()).hexdigest() == '8a04e4568bf6c70ee0838803d7cc1615e723c8f054304cc46fa5231757a6f4ed'
_spec = importlib.util.spec_from_file_location('original_control_fixtures', OLD)
BASE = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(BASE)
LABELS, FORMS, SPECS = BASE.LABELS, BASE.FORMS, BASE.SPECS


def partial_worlds():
    """The five specifically requested partial-information counterexamples."""
    return [
        ('gender','they-many','The referents are two people. The verified profile states that the first referent is a woman. The other profile is silent about gender.'),
        ('known_identity','they-many','The report concerns two referents. The recorder has verified the identity of the first against the authoritative register. The report does not state whether the recorder knows the identity of the second.'),
        ('unanimity','they-one','The referent is one committee with five members. The available ballot record lists four members as voting in favour. The fifth member\'s position is not recorded.'),
        ('all_members_participation','they-one','The referent is one team with five members. The available participation record shows that four members personally performed a task step. It does not record whether the fifth member performed any step.'),
        ('collective_action','they-many','The referents are two ensembles. The event record shows the first ensemble\'s members acting together in the reported activity. It does not state how the second ensemble\'s members acted or whether both ensembles joined one coordinated event.'),
    ]


def cue_worlds():
    for form in FORMS:
        many = form == 'they-many'
        prefix = 'The referents are two people.' if many else 'The referent is one person.'
        names = "The record calls them Mary and John." if many else "The record calls the person Mary."
        yield 'name_not_gender','gender',form,prefix+' '+names+' No verified statement of gender is provided.'
        pronouns = ("An unverified note uses 'she' for the first person and 'he' for the second."
                    if many else "An unverified note uses 'she' for the person.")
        yield 'pronoun_not_gender','gender',form,prefix+' '+pronouns+' These unverified pronoun choices are not established profile facts. No verified statement of gender is provided.'
        full_names = ('The report spells out both full names, copied from unverified intake fields.'
                      if many else 'The report spells out the full name, copied from an unverified intake field.')
        yield 'naming_not_recorder_knowledge','known_identity',form,prefix+' '+full_names+' It does not state whether the recorder knows the identity behind each label.'
        groups = 'two ensembles, each with five members' if many else 'one ensemble with five members'
        yield 'completion_not_coordination','collective_action',form,('The referent set contains '+groups+'. '
            'The members are listed and the reported activity is recorded as completed. '
            'Nothing states whether participants acted together, separately, or at the same time.')


def mixed_worlds():
    """Six pairs of contrasting worlds; both question polarities are covered."""
    for form in FORMS:
        for reverse in (False, True):
            first, second = ('No','Yes') if reverse else ('Yes','No')
            people = 'two people' if form == 'they-many' else 'one person'
            gender = ('The verified profiles explicitly state that at least one referent is not a woman.'
                      if reverse else 'The verified profiles explicitly state that every referent is a woman.')
            identity = ('The recorder has verified the identity of every referent against the authoritative identity register.'
                        if reverse else 'The recorder explicitly states that the identity of at least one referent remains unknown to the recorder.')
            yield 'gender_identity',form,reverse,('The referent set contains '+people+'. '+gender+' '+identity), [('gender',first),('known_identity',second)]

            committees = 'two committees, each with five members' if form == 'they-many' else 'one committee with five members'
            vote = ('The complete ballot record states that at least one member opposed the proposal.'
                    if reverse else 'The complete ballot record states that every member voted in favour and no member opposed or abstained.')
            work = ('The complete task record states that every member personally performed at least one step of a separate filing task.'
                    if reverse else 'The complete task record states that at least one member performed no part of a separate filing task.')
            yield 'unanimity_participation',form,reverse,('The referent set contains '+committees+'. '
                'Each referenced committee is also the team for the separate filing task. '+vote+' '+work), [('unanimity',first),('all_members_participation',second)]

            ensembles = 'two ensembles, each with five members' if form == 'they-many' else 'one ensemble with five members'
            action = ('The event record states that participants performed the reported rehearsal separately and independently, not as one coordinated group event.'
                      if reverse else 'The event record states that all participating members performed the reported rehearsal together as one coordinated group event.')
            participation = ('The complete participation record states that every member personally performed at least one part of that rehearsal.'
                             if reverse else 'The complete participation record states that at least one member performed no part of that rehearsal.')
            yield 'coordination_participation',form,reverse,('The referent set contains '+ensembles+'. '
                'Each referenced ensemble is also the team for the rehearsal task. '+action+' '+participation), [('collective_action',first),('all_members_participation',second)]


def build():
    old = BASE.build()
    items = old['items']
    def add(world,form,family,text,probes):
        for dimension,gold in probes:
            for rotation in range(3):
                items.append({'id':f'{world}/{dimension}/order-{rotation}',
                    'world_id':world,'form_slot':form,'dimension':dimension,
                    'role':'explicit_fact' if gold in LABELS[:2] else 'underdetermined',
                    'coverage_family':family,'text':'Fictional control record. '+text,
                    'question':SPECS[dimension]['question'],
                    'options':LABELS[rotation:]+LABELS[:rotation],'gold':gold,
                    'exposure':'standalone shared-context control concept; no target marker in prompt'})
    for dim,form,text in partial_worlds():
        add('partial/'+form+'/'+dim,form,'partial_information',text,[(dim,LABELS[2])])
    for family,dim,form,text in cue_worlds():
        add('cue/'+form+'/'+family,form,family,text,[(dim,LABELS[2])])
    for family,form,reverse,text,probes in mixed_worlds():
        add('mixed/'+form+'/'+family+'/'+str(int(reverse)),form,'same_record_distinct_questions',text,probes)
    return {'kind':'ainglish.nonclaim-control-review-fixtures.v2',
        'status':'PROPOSED_FOR_REVIEW_NOT_A_TARGET_BANK_OR_MEASUREMENT',
        'candidate_sha256':old['candidate_sha256'],'original_v1_items_preserved':90,
        'semantic_worlds':len({r['world_id'] for r in items}),
        'semantic_question_probes':len({(r['world_id'],r['question']) for r in items}),
        'prompt_variants':len(items),'reader_calls':0,
        'design_reference_explicit_accuracy_floor':0.9,
        'floor_boundary':'Existing design target for synthetic fixture checks only; not an inference pass or confidence bound.',
        'observation_contract':'Exactly one distinct observation per planned prompt; repeated reads require a separately reviewed execution contract with an explicit replica index.',
        'items':items}


def score(fixtures, observations):
    result = BASE.score(fixtures,observations)
    seen = {r['item_id']:r for r in observations}
    groups = defaultdict(list)
    for item in fixtures['items']:
        family = item.get('coverage_family','v1/'+item['role'])
        groups[family].append(item)
    coverage = {}
    for name,rows in sorted(groups.items()):
        answered = [r for r in rows if r['id'] in seen and seen[r['id']]['answer'] is not None]
        correct = sum(seen[r['id']]['answer']==r['gold'] for r in answered)
        coverage[name] = {'semantic_worlds':len({r['world_id'] for r in rows}),
            'planned_prompts':len(rows),'answered':len(answered),'absent':len(rows)-len(answered),
            'correct':correct,'incorrect':len(answered)-correct,
            'observed_accuracy':correct/len(answered) if answered else None}
    result['coverage_families'] = coverage
    result['semantic_worlds'] = len({r['world_id'] for r in fixtures['items']})
    result['semantic_question_probes'] = len({(r['world_id'],r['question']) for r in fixtures['items']})
    result['complete_is_not_passed'] = True
    result['interpretation'] += ' World counts overlap between endpoints; do not sum them. Questions and rotations share their world cluster.'
    return result


def text_only(text):
    """Excelsior's disclosed fixture-tuned witness; no question or metadata."""
    if any(s in text for s in ('no gender information','says nothing','gives no')):
        return LABELS[2]
    if any(s in text for s in ('not a woman','remains unknown','opposed the proposal',
                               'performed no part','separately and independently')):
        return 'No'
    return 'Yes'


def witnesses(fixtures):
    functions = {'constant-semantic/'+label:(lambda r,label=label:label) for label in LABELS}
    functions.update({'constant-position/'+str(p):(lambda r,p=p:r['options'][p]) for p in range(3)})
    functions['question-blind-record-polarity'] = lambda r:text_only(r['text'])
    # These two deliberately use the gold elsewhere to isolate partial-information
    # coverage, not to pretend to be a deployable blind classifier or model.
    for label in LABELS[:2]:
        functions['oracle-except-partial/'+label] = lambda r,label=label: label if r.get('coverage_family')=='partial_information' else r['gold']
    return {name:score(fixtures,BASE.fixture_answers(fixtures,fn)) for name,fn in functions.items()}


if __name__=='__main__':
    fixtures=build()
    output={'control-prototypes.json':fixtures,'shortcut-checks.json':witnesses(fixtures),
            'old-question-blind-reproduction.json':BASE.score(BASE.build(),BASE.fixture_answers(BASE.build(),lambda r:text_only(r['text'])))}
    for name,value in output.items():
        (ROOT/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
    print('Prepared',fixtures['semantic_worlds'],'worlds,',fixtures['semantic_question_probes'],
          'question probes,',fixtures['prompt_variants'],'variants; zero reader calls.')
