#!/usr/bin/env python3
"""Build synthetic, non-normative teaching data and a separate fresh task holdout."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = Path('/home/dexagon/codex/worktrees/web-learning-roadmap-20260906/public/releases/ainglish-core-v3')
REVISION = 'a09a35458c702b33eeacc393d103063234e8bc28'
SYSTEM = 'Read the supplied record. Answer the question using only its facts and rules. Return exactly one option letter: A, B, or C. Do not assume missing facts.'
SLUGS = {
    'participants': 'we-including-you-we-excluding-you-clusivity-mark-whether-we--4',
    'deadline': 'start-by-complete-by-say-which-task-event-a-deadline-constra',
    'unknown': 'fact-not-known-choice-not-made-distinguish-missing-evidence-',
    'multiplicity': 'each-alone-as-one-distributive-vs-collective-does-the-plural',
    'alternatives': 'or-both-not-both-english-or-never-says-whether-both-is-allow',
    'update': 'supersedes-ref-supplements-ref-say-whether-a-follow-up-repla-2',
}
# Hand-authored case grammars; mechanical expansion is not independent human validation.
GUIDES = {
    'participants': (
        'we-including-you includes the addressed reader in the first-person plural group; we-excluding-you excludes that reader. Bare we leaves inclusion unspecified. Neither form grants authority.',
        'A first-person plural group can include or exclude the addressed reader. Explicit inclusion or exclusion determines membership; an unspecified we does not. Wording alone grants no authority.'),
    'deadline': (
        'start-by(t) requires actual task execution to begin at or before t, not merely queuing or acknowledgement. complete-by(t) requires successful completion at or before t, not stopping or failure. A start deadline alone is not a completion deadline.',
        'A begin-no-later-than deadline constrains actual task execution, not queuing or acknowledgement. A successful-finish-no-later-than deadline requires success, not stopping or failure. A start deadline alone is not a completion deadline.'),
    'unknown': (
        'fact-not-known marks an already-determined answer for which the speaker lacks evidence. choice-not-made marks the absence of an operative authorized selection. Neither marker asks the reader to act or grants authority. An unknown future contingency outside anyone\'s control is neither.',
        'An already-determined answer missing from the speaker\'s evidence needs evidence. A not-yet-made authorized selection needs a decision. Describing either gap neither requests action nor grants authority. An undetermined future contingency outside anyone\'s control is neither.'),
    'multiplicity': (
        'each-alone distributes a plural action once per member; as-one makes one collective instance. Simultaneous independent acts are still separate, not one collective act. Bare plural wording does not determine the number of instances.',
        'Acting once independently per member gives as many instances as members; acting once collectively gives one instance. Simultaneous independent acts remain separate. Bare plural wording does not determine the number of instances.'),
    'alternatives': (
        'On a two-option disjunction, or-both permits either or both but not neither. not-both requires exactly one. Neither marker overrides another constraint. Missing permission cannot be inferred from an unqualified disjunction.',
        'A two-option inclusive choice permits either or both, but not neither. An exclusive choice requires exactly one. These choices do not override other constraints. Missing permission cannot be inferred from an unqualified disjunction.'),
    'update': (
        'An authorized supersedes(ref): X retires the named active clause\'s uncompleted obligations at the stated commit event and activates X. supplements(ref): X keeps the named clause active and adds X. Other clauses survive. Completed effects are not undone. Invalid/missing references make the entire marked unit invalid; do not execute X as a fallback. In-flight work is not automatically cancelled.',
        'An authorized whole-clause replacement retires the named active clause\'s uncompleted obligations at the stated commit event and activates the replacement. An addition retains the named clause. Other clauses survive. Completed effects are not undone. Invalid/missing references invalidate the entire update, not just its reference. In-flight work is not automatically cancelled.'),
}
TRAIN_CONTEXTS = ['catalogue', 'invoice', 'inventory']
TEST_CONTEXTS = ['observatory', 'conservatory']


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jsonl(path, rows):
    path.write_text(''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in rows))


def scenario(family, context, variant, holdout):
    """Return parallel records, common question/options, gold option index and case type."""
    name = context + '-packet'
    v = variant
    boundary = v in (3, 6, 7)
    if family == 'participants':
        mode = v % 3
        a = ['we-including-you', 'we-excluding-you', 'we'][mode]
        e = ['we, including you,', 'we, excluding you,', 'we'][mode]
        envelope = ('A coordinator addresses you directly about a joint task. The membership of the team is otherwise unspecified.' if holdout else 'This message is addressed to you. No other group membership is supplied.')
        tail = f' will inspect {name}.'
        if v == 6:
            a = e = f'The sender and two named colleagues will inspect {name}; you are not one of those colleagues.'
            tail = ''
            gold = 1
        elif v == 7:
            a = e = f'You and the sender will inspect {name}.'
            tail = ''
            gold = 0
        else:
            gold = mode
        q = ('Does the announced inspecting group contain you, the recipient?' if holdout else 'Are you included in the group that will inspect the packet?')
        return envelope+'\nMessage: '+a+tail, envelope+'\nMessage: '+e+tail, q, ['Yes', 'No', 'Not determined'], gold, boundary
    if family == 'deadline':
        due = '16:00Z' if holdout else '11:00Z'
        before = '15:59Z' if holdout else '10:59Z'
        after = '16:01Z' if holdout else '11:01Z'
        marker = 'start-by' if v < 4 else 'complete-by'
        phrase = 'Begin actual execution of' if v < 4 else 'Successfully finish'
        logs = [f'Actual upload starts at {due}; successful finish at {after}.',
                f'Actual upload starts at {after}; successful finish later.',
                f'Upload queued at {before}, but actual execution starts at {after}.',
                'No execution timestamp is available.',
                f'Actual execution starts at {before}; successful upload completes at {due}.',
                f'Actual execution starts at {before}; successful upload completes at {after}.',
                f'The only upload attempt terminates with failure at {before}; no successful completion occurs by the deadline.',
                'The record contains no completion status or timestamp.']
        envelope = ('Audit extracts for one upload on 2031-11-09; all times refer to that UTC day. Decide about the stated deadline, not a new deadline.' if holdout else 'All times refer to the same UTC day, 2030-05-04. Evaluate only the stated deadline.')
        a = f'Please upload {name} {marker}({due}).'
        e = f'{phrase} the upload of {name} no later than {due}.'
        log = '\nObserved log: '+logs[v]
        q = ('Does the observed run satisfy the deadline that was actually specified?' if holdout else 'Was the specified deadline met?')
        return envelope+'\nInstruction: '+a+log, envelope+'\nInstruction: '+e+log, q, ['Yes', 'No', 'Not determined'], [0,1,1,2,0,1,1,2][v], boundary
    if family == 'unknown':
        issues = [f'which storage region the board already selected for {name}',
                  f'which region the board will select for {name}',
                  f'whether yesterday\'s checksum of {name} matched',
                  f'which of two approved checks to select for {name}',
                  f'which filename the board already chose for {name}',
                  f'which filename the board will choose for {name}']
        if v < 6:
            mode = v % 2
            marker = ['fact-not-known', 'choice-not-made'][mode]
            a = f'{marker} — {issues[v]}.'
            e = (f'The answer to {issues[v]} is already determined, but I lack evidence of it.' if mode == 0 else f'No operative authorized selection has yet been made about {issues[v]}; making that selection closes the gap.')
            q = ('What kind of missing information or selection does this report identify?' if holdout else 'What would close the gap identified by this report?')
            options, gold = ['Evidence of an already-determined answer', 'An authorized selection', 'Neither of those gaps is established'], mode
        elif v == 6:
            a = e = f'The board\'s choice for {name} is known to everyone here and has not been implemented.'
            q, options, gold = 'Which gap is described?', ['Missing evidence of an existing answer', 'No operative selection yet', 'Neither; the gap is implementation'], 2
        else:
            a = f'choice-not-made — which region the board will select for {name}. You are an observer without decision authority.'
            e = f'The board has not made its operative region selection for {name}. You are an observer without decision authority.'
            q, options, gold = 'Does the report give you authority to select the region?', ['Yes', 'No', 'The report says you already selected it'], 1
        envelope = ('A status note follows; it is a description, not a request for you to investigate or decide.' if holdout else 'Read this status report. No task is assigned by reporting the gap.')
        return envelope+'\n'+a, envelope+'\n'+e, q, options, gold, boundary
    if family == 'multiplicity':
        n = 5 if holdout else 3
        mode = v % 3
        if v == 6:
            a = e = f'The {n} inspectors each submit an independent signed check of {name} at the same instant.'
            gold = 0
        elif v == 7:
            a = e = f'The {n} inspectors submit one jointly signed check of {name}.'
            gold = 1
        else:
            a = f'The {n} inspectors check {name}'+[', each-alone.', ', as-one.', '.'][mode]
            e = [f'Each of the {n} inspectors performs an independent check of {name}.', f'The {n} inspectors jointly perform one check of {name}.', f'The {n} inspectors check {name}.'][mode]
            gold = mode
        q = ('How many separate checking acts does this report establish?' if holdout else 'How many checks does the statement specify?')
        return a, e, q, [str(n), '1', 'Not determined'], gold, boundary
    if family == 'alternatives':
        inclusive = v % 2 == 0
        a = f'For {name}, choose a text report or a chart, '+('or-both.' if inclusive else 'not-both.')
        e = f'For {name}, choose '+('a text report, a chart, or both; at least one is required.' if inclusive else 'exactly one of a text report and a chart, but not both.')
        pick = ['both', 'both', 'neither', 'neither', 'text only', 'chart only', 'both', 'both'][v]
        if v == 6:
            a += ' A separate binding rule prohibits charts.'
            e += ' A separate binding rule prohibits charts.'
        if v == 7:
            a = e = f'For {name}, choose a text report or a chart. Whether both are permitted is unspecified.'
        q = (f'A proposed outcome supplies {pick}. Does it satisfy all the stated choice rules?' if holdout else f'Is choosing {pick} allowed by all these rules?')
        gold = [0,1,1,1,0,0,1,2][v]
        return a, e, q, ['Yes', 'No', 'Not determined'], gold, boundary
    if family == 'update':
        ref = 'ledger-Q' if holdout else 'message-P'
        second = 'ledger-R' if holdout else 'message-S'
        envelope = (f'An instruction ledger records {ref}: upload {name}; {second}: publish a checksum. Both were issued by the current sender, remain active and are uncompleted. No work is in flight. The sender is authorized; the update below commits now.' if holdout else f'The sender issued active, uncompleted {ref}: upload {name}. Separate {second}: publish a checksum remains active. No work is in flight. This authorized update commits now.')
        addition = v % 2 == 1
        a = f'{"supplements" if addition else "supersedes"}({ref}): Please archive the notes.'
        e = (f'Keep {ref} active and add: please archive the notes; neither clause gains precedence.' if addition else f'Retire all uncompleted obligations of {ref} and replace that whole clause with: please archive the notes.')
        q = ('After this commit, is the original upload still an obligation?' if holdout else 'Must the original upload still be performed?')
        options, gold = ['Yes', 'No', 'The whole update is invalid; ask for repair'], 0 if addition else 1
        if v in (2, 3):
            q, gold = 'Does the separately referenced checksum obligation remain active?', 0
        if v in (4, 5):
            a = a.replace(ref, 'missing-reference')
            e = e.replace(ref, 'missing-reference')
            envelope += ' missing-reference does not identify any clause. An update with a missing reference is entirely invalid; its new instruction is not a fallback.'
            q, gold = 'How should the recipient treat this entire update?', 2
        if v == 6:
            envelope = envelope.replace('No work is in flight.', 'The upload has already been dispatched and is still in flight; it may not be cancellable.')
            q, options, gold = 'Does this language update guarantee the physical upload has stopped?', ['Yes', 'No', 'The update proves the upload never started'], 1
        if v == 7:
            envelope += ' Publishing the checksum and archiving the notes are compatible.'
            q, gold = 'Does adding the note-archiving obligation cancel the checksum obligation?', 1
        return envelope+'\nUpdate: '+a, envelope+'\nUpdate: '+e, q, options, gold, boundary
    raise ValueError(family)


def row(family, context, variant, split):
    a, e, q, options, gold, boundary = scenario(family, context, variant, split == 'test')
    shift = (variant + list(SLUGS).index(family) + (0 if split == 'train' else 1)) % 3
    options = options[shift:]+options[:shift]
    gold = (gold-shift) % 3
    return {'id': f'{split}/{family}/{context}/{variant}', 'frame': f'{split}/{family}/{context}',
            'family': family, 'variant': variant, 'split': split, 'ainglish': a, 'english': e,
            'question': q, 'options': dict(zip('ABC', options)), 'answer': 'ABC'[gold],
            'boundary_case': boundary, 'synthetic': True, 'normative': False, 'source_slug': SLUGS[family]}


def messages(case, arm):
    language, reference = arm.split('-')
    body = case['ainglish' if language == 'ainglish' else 'english']
    if reference == 'reference':
        body = 'Reading reference: '+GUIDES[case['family']][0 if language == 'ainglish' else 1]+'\n\n'+body
    body += '\n\n'+case['question']+'\n'+'\n'.join(k+'. '+v for k,v in case['options'].items())
    return [{'role':'system','content':SYSTEM}, {'role':'user','content':body}]


def build():
    if (ROOT/'results').exists():
        raise SystemExit('REFUSING to rebuild after model exposure')
    released = json.loads((SOURCE/'register.json').read_text())
    selection = {key: next(x for x in released['entries'] if x['slug']==slug) for key,slug in SLUGS.items()}
    dump(ROOT/'source-constructs.json', {'source_url':'https://ainglish.org/releases/ainglish-core-v3/register.json',
         'source_sha256':sha(SOURCE/'register.json'), 'register_digest':released['register_digest'], 'entries':selection})
    train = [row(f,c,v,'train') for f in SLUGS for c in TRAIN_CONTEXTS for v in range(8)]
    test = [row(f,c,v,'test') for f in SLUGS for c in TEST_CONTEXTS for v in range(8)]
    jsonl(ROOT/'curriculum.jsonl', train)
    jsonl(ROOT/'evaluation.jsonl', test)
    for language in ('ainglish','english'):
        examples = [{'id':r['id'], 'messages':messages(r,language+'-cold')+[{'role':'assistant','content':r['answer']}]} for r in train]
        jsonl(ROOT/f'train-{language}.jsonl', examples)
    dump(ROOT/'guides.json', {k: {'ainglish':v[0], 'english':v[1]} for k,v in GUIDES.items()})
    dialogues = []
    examples = [
        ('participants', 'we-excluding-you will review the catalogue.', 'We, excluding you, will review the catalogue.',
         'Am I part of the review group?', 'No. This statement informs you; it does not include you in that group.'),
        ('deadline', 'Please upload the inventory start-by(2030-05-04T11:00Z).', 'Please begin the inventory upload no later than 2030-05-04T11:00Z; no completion deadline is stated.',
         'It entered a queue at 10:59Z, but actual upload began at 11:01Z that day. Was the deadline met?', 'No. Queueing is not actual upload execution, and execution began after the stated deadline.'),
        ('unknown', 'choice-not-made — which catalogue layout the board will select.', 'The board has not yet made an operative selection of the catalogue layout.',
         'Can I infer that you are asking me to choose it?', 'No. This reports a missing decision; it neither requests a choice from you nor gives you authority.'),
        ('multiplicity', 'The three inspectors checked the invoice, each-alone.', 'Each of the three inspectors independently checked the invoice.',
         'All three checks began at the same instant. Does that make it one joint check?', 'No. Simultaneous timing does not combine three independent checks into one collective act.'),
        ('alternatives', 'For the inventory summary choose a table or a chart, or-both.', 'For the inventory summary choose a table, a chart, or both; at least one is required.',
         'Could I deliver neither?', 'No. Allowing both does not remove the requirement to choose at least one.'),
        ('update', 'Active uncompleted message-P requests the invoice upload. I am its issuer. This update commits now: supersedes(message-P): Please archive the notes.',
         'Active uncompleted message-P requests the invoice upload. I am its issuer. At this commit, retire that whole clause and replace it with: please archive the notes.',
         'The upload was already dispatched. Does the update guarantee it has stopped?', 'No. The obligation is replaced, but the language update does not cancel an in-flight physical action. Report its state and any later effect separately.'),
    ]
    for family,a,e,question,answer in examples:
        for language,statement in [('ainglish',a),('english',e)]:
            dialogues.append({'id':f'teaching-dialogue/{family}/{language}', 'family':family,
                'synthetic':True, 'normative':False, 'source_slug':SLUGS[family], 'split':'train',
                'messages':[{'role':'user','content':statement}, {'role':'assistant','content':'What would you like clarified?'},
                            {'role':'user','content':question}, {'role':'assistant','content':answer}]})
    jsonl(ROOT/'conversations.jsonl',dialogues)
    (ROOT/'LICENSE-CC0-1.0.txt').write_bytes((SOURCE/'LICENSE-CC0-1.0.txt').read_bytes())
    # Only train-only assets belong in the teaching export; evaluation stays visibly separate.
    readme = ['# Six ratified distinctions: contextual teaching cards', '',
              'Synthetic, agent-authored, non-normative CC0 teaching material. Not an official language release.',
              'The source meanings are pinned in source-constructs.json. No human validation is claimed.', '']
    for family in SLUGS:
        readme += ['## '+family, '', GUIDES[family][0], '', '### Example and careful-English rendering', '',
                   train[next(i for i,r in enumerate(train) if r['family']==family)]['ainglish'], '',
                   train[next(i for i,r in enumerate(train) if r['family']==family)]['english'], '',
                   '### Boundary', '', GUIDES[family][1], '']
    (ROOT/'TEACHING.md').write_text('\n'.join(readme))
    plan = {'kind':'ainglish.ratified-learning-pilot.v1', 'governance_evidence':False,
            'base_model':'Qwen/Qwen2.5-7B-Instruct', 'base_revision':REVISION,
            'seed':2026090601, 'training_rows_per_adapter':len(train), 'test_cases':len(test),
            'test_frames':12, 'families':list(SLUGS),
            'conditions':['base','ainglish','english'],
            'arms':['ainglish-cold','ainglish-reference','english-cold','english-reference'],
            'training':{'epochs':2,'batch_size':1,'gradient_accumulation_steps':8,'learning_rate':0.0002,
                        'max_length':768,'lora_r':16,'lora_alpha':32,'lora_dropout':0.05,
                        'target_modules':['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj'],
                        'max_artifact_bytes':536870912},
            'evaluation':{'batch_size':8,'max_new_tokens':8,'do_sample':False,'automatic_retries':0},
            'primary':'Paired cold-Ainglish accuracy difference: Ainglish-trained minus English-trained, plus the corresponding careful-English difference (difference in differences).',
            'guards':'No claim of selective benefit if careful-English or boundary-case accuracy loses more than 5 percentage points relative to English-trained control. Report every family. Single seed; no population-wide causal claim.',
            'design_limits':'Synthetic shared semantic cases; held-out scenario framing, names and full prompts, not held-out concepts. Twelve context clusters. Short-reference cost included. No natural-use or independent governance claim.',
            'outputs':{p.name:sha(p) for p in ROOT.iterdir() if p.name in ['source-constructs.json','curriculum.jsonl','evaluation.jsonl','train-ainglish.jsonl','train-english.jsonl','guides.json','TEACHING.md','conversations.jsonl','LICENSE-CC0-1.0.txt']}}
    dump(ROOT/'PLAN.json', plan)
    print(json.dumps({'train_pairs':len(train),'test_cases':len(test),'calls':len(test)*12}))


if __name__ == '__main__':
    build()
