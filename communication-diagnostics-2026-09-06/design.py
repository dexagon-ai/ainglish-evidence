"""New prospective diagnostic: correct references, constrained writers, three contexts.

The former free-prose study is retained unchanged. This study intentionally tests
a narrower fixed-sentence communication interface, not unrestricted writing.
"""
from itertools import product
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIELDS = ['include_recipient', 'finish_deadline', 'collective', 'both_allowed', 'old_A_active']
PREFIXES = ['Team', 'Deadline', 'Work', 'Options', 'Update']
PHRASES = {
    'ainglish': [
        ['we-excluding-you', 'we-including-you'],
        ['start-by(18:00 UTC)', 'complete-by(18:00 UTC)'],
        ['each-alone', 'as-one'],
        ['red or blue, not-both', 'red or blue, or-both'],
        ['C: supersedes(A): perform the named check', 'C: supplements(A): perform the named check']],
    'english': [
        ['the acting team excludes you', 'the acting team includes you'],
        ['the check must start by 18:00 UTC', 'the check must successfully finish by 18:00 UTC'],
        ['each team member performs their own named check', 'the team performs one collective named check'],
        ['choose exactly one of red and blue', 'choose red or blue or both'],
        ['C replaces A with the instruction to perform the named check', 'C adds the instruction to perform the named check while A remains active']],
}
CONTEXTS = [
    {'id':'handoff', 'text': 'You are Mira, receiving a release-review handoff from Noor and Ivo. The named check is reviewing the release notes.'},
    {'id':'equipment', 'text': 'You are Mira, arranging an equipment handover with Noor and Ivo. The named check is inspecting the loaned camera.'},
    {'id':'community', 'text': 'You are Mira, preparing a community exhibition with Noor and Ivo. The named check is checking the exhibit inventory.'},
]
COMMON = ('The speakers are Noor and Ivo; the addressee is you (Mira). Both speakers belong to '
    'the acting team; the message determines whether you also belong. A named check is specified below. '
    'The deadline is 18:00 UTC today; all parties know the date and timezone. Red and blue are '
    'both feasible check methods. Earlier instructions A and B are authorized and active; C is '
    'also authorized. Read update effects at the authoritative acceptance of C, before any '
    'work begins. B remains unchanged. No physical action is performed by this diagnostic.')
MEANINGS = [
    'Does the acting team include you, Mira?',
    'Does the deadline constrain successful completion rather than starting?',
    'Is one collective check requested rather than one check per member?',
    'May both red and blue be chosen?',
    'Does earlier instruction A remain active after C is accepted?',
]
GUIDE = ('Each pair below gives the false and true readings of one field. Both languages are '
         'defined explicitly; this is reference-assisted interpretation, not cold reading.\n')

def guide(arm):
    return GUIDE+'\n'.join(f'{field}: false = {options[0]}; true = {options[1]}.'
        for field, options in zip(FIELDS, PHRASES[arm]))

def render(brief, arm):
    return '\n'.join(f'{prefix}: {options[int(brief[field])] }.'
        for field,prefix,options in zip(FIELDS,PREFIXES,PHRASES[arm]) if field in brief)

def decode_message(raw, arm, fields):
    # Deliberately strict requested interface; unrecognised prose is UNPARSED,
    # not a claim that it is semantically incorrect under all English parsers.
    lines = [line.strip().rstrip('.').strip() for line in raw.strip().splitlines() if line.strip()]
    expected = {f'{prefix}: {options[int(value)]}'.casefold(): (field,value)
        for field,prefix,options in zip(FIELDS,PREFIXES,PHRASES[arm]) if field in fields
        for value in [False,True]}
    decoded = {}
    for line in lines:
        match = expected.get(line.casefold())
        if match is None or match[0] in decoded: return None
        decoded[match[0]] = match[1]
    return decoded if set(decoded)==set(fields) else None

def decode_json(raw, fields):
    try:
        def pairs(rows):
            if len(rows)!=len({k for k,v in rows}): raise ValueError('duplicate key')
            return dict(rows)
        out=json.loads(raw.strip(),object_pairs_hook=pairs)
        if not isinstance(out,dict) or set(out)!=set(fields): return None
        if any(type(value) is not bool for value in out.values()): return None
        return out
    except (TypeError,ValueError): return None

def reader_messages(case, arm, text):
    fields=list(case['brief'])
    meanings='\n'.join(f'{field}: {MEANINGS[FIELDS.index(field)]}' for field in fields)
    return [{'role':'system','content':'Interpret the message, without executing it. Reply only with a JSON object containing exactly the listed fields, each a boolean. Do not provide explanation or markdown.'},
        {'role':'user','content':COMMON+'\n'+case['context']+'\n'+guide(arm)+'\nMessage:\n'+text+'\nQuestions:\n'+meanings}]

def sender_messages(case, arm):
    table='\n'.join(f'{prefix}: choose exactly "{options[0]}" for false or "{options[1]}" for true.'
        for prefix,options in zip(PREFIXES,PHRASES[arm]))
    return [{'role':'system','content':'Write the operational message using exactly five labelled sentences from the permitted phrase table, one sentence per line, with the label followed by a colon and the selected phrase. Do not output the input booleans, JSON, analysis, quotation marks, or commentary.'},
        {'role':'user','content':COMMON+'\n'+case['context']+'\n'+guide(arm)+'\nPhrase table:\n'+table+'\nThe intended choices are:\n'+json.dumps(case['brief'],sort_keys=True)}]

def save(name,value):
    p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def build():
    cases=[]
    for context in CONTEXTS:
        for count in [1,2,5]:
            for bits in product([False,True],repeat=count):
                brief=dict(zip(FIELDS[:count],bits))
                cases.append({'id':context['id']+'/'+str(count)+'/'+''.join(str(int(b)) for b in bits),
                    'context':context['text'],'dimensions':count,'brief':brief,
                    'messages':{arm:render(brief,arm) for arm in PHRASES}})
    controls=[]
    for i in range(8):
        brief={'sealed':bool(i%2),'metal':bool((i//2)%2)}
        words={'sealed':['open','sealed'],'metal':['wood','metal']}
        content=f"Package code {801+i} has state {words['sealed'][int(brief['sealed'])]} and material {words['metal'][int(brief['metal'])]}."
        controls.append({'id':f'control-{i}','brief':brief,'messages':[
            {'role':'system','content':'Reply only with a JSON object containing boolean fields sealed and metal. No explanation or markdown.'},
            {'role':'user','content':content+' Is the package sealed rather than open, and metal rather than wood?'}],
            'writer_messages':[{'role':'system','content':'Translate the two booleans into exactly two labelled lines. For sealed use State: open or State: sealed. For metal use Material: wood or Material: metal. No other text.'},
                {'role':'user','content':json.dumps(brief)}],
            'writer_gold':f"State: {words['sealed'][int(brief['sealed'])]}\nMaterial: {words['metal'][int(brief['metal'])]}"})
    plan={'kind':'ainglish.communication-diagnostic.v1','governance_evidence':False,
        'snapshot':'/home/dexagon/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28',
        'arms':list(PHRASES),'conditions':['base'],'greedy':True,'max_prompt_tokens':4096,
        'receiver_cap':256,'sender_cap':512,'controls_per_role':8,'minimum_control_correct':7,
        'qualification':'Both target-independent package reader and fixed-line writer screens must score at least7/8, with zero truncated calls. Otherwise no language targets. This is interface sensitivity, not target accuracy.',
        'cases':len(cases),'full_cases':sum(c['dimensions']==5 for c in cases),'contexts':len(CONTEXTS),
        'target_calls':len(cases)*2+sum(c['dimensions']==5 for c in cases)*4,
        'primary':['Known-correct-message receiver exact accuracy by language, context and dimensions.',
                   'Constrained sender parse rate and exact intended-message accuracy, with truncation separate.',
                   'Receiver accuracy against intended brief and, where parsable, against actual sender meaning.'],
        'next_training_gate':'At least80% exact known-correct-message accuracy in EACH language arm of the full-five-field condition; at least80% sender outputs parsed in EACH language; zero control truncations. Gate is checked before any communication-adapter training.',
        'no_retry':'No outcome-selected call repetitions. Safe restart may reuse verified completed cells but refuses uncertain in-flight calls.',
        'limits':['Three authored contexts, not114 independent reasoning templates.',
                  'Explicit reference guides and constrained phrase table, not free prose or unaided reading.',
                  'Same base model on both ends; not independent agents or a governance replication.',
                  'Fixed current tokenizer; no future efficiency guarantee.'],
        'supersedes':None,'previous_study':'sender-receiver-2026-09-06 is retained unchanged; narrower interface and larger budgets are declared prospectively.'}
    save('cases.json',cases);save('controls.json',controls);save('PLAN.json',plan)
    pins={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in
        ['design.py','run.py','analyse.py','test_design.py','cases.json','controls.json','PLAN.json','../overnight-runtime-2026-09-06/runtime.py','source-constructs.json']}
    save('FROZEN.json',pins)

if __name__=='__main__':build()
