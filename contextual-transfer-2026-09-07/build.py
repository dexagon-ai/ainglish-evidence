"""Prospective contextual curriculum and structurally harder, paired reading tasks."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import re

ROOT=Path(__file__).resolve().parent
SYSTEM='Read the supplied record. Choose the one correct option. Output exactly one capital letter A, B, C or D, and nothing else.'
DOMAINS=['tidal observatory','seed exchange','lantern exhibition','kite workshop','fossil archive','canal survey','costume library','planetarium']
PAIR_OPTIONS=['First warranted; second warranted','First warranted; second not warranted',
              'First not warranted; second warranted','Neither warranted']

def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
def save(name,value):dump(ROOT/name,value)
def messages(text,question,options):
    return [{'role':'system','content':SYSTEM},{'role':'user','content':text+'\n\n'+question+'\n'+'\n'.join(k+'. '+v for k,v in options.items())}]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def labelled(options,gold,index,shuffle_seed=None):
    assert len(options)==4 and len(set(options))==4 and gold in options
    wrong=[s for s in options if s!=gold];random.Random(index if shuffle_seed is None else shuffle_seed).shuffle(wrong)
    at=index%4;wrong.insert(at,gold)
    return dict(zip('ABCD',wrong)),'ABCD'[at]
def we(include,arm):return ('we-including-you' if include else 'we-excluding-you') if arm=='ainglish' else ('we, including you,' if include else 'we, excluding you,')
def unknown(choice,issue,arm):
    if arm=='ainglish':return ('choice-not-made' if choice else 'fact-not-known')+' — '+issue
    return ('No operative authorized choice has been made about '+issue if choice else
        'An answer about '+issue+' is already determined by facts or a declared criterion, but I do not have enough evidence to assert it')
def deadline(finish,task,arm):
    return task+(' complete-by(16:00Z)' if finish else ' start-by(16:00Z)') if arm=='ainglish' else (
        'The action “'+task+'” must '+('satisfy its successful-completion condition' if finish else 'genuinely begin execution')+' no later than 16:00Z')
def either(both,task,arm):
    return task+(', or-both' if both else ', not-both') if arm=='ainglish' else task+('; at least one is required and both are allowed' if both else '; exactly one is required and both are forbidden')
def plural(joint,task,arm):
    return task+(', as-one' if joint else ', each-alone') if arm=='ainglish' else task+(', jointly in one whole verification' if joint else ', independently with one whole verification per inspector')
def relation(add,refs,task,arm):
    task=task.replace('req: ','please ')
    return ('supplements' if add else 'supersedes')+'('+refs+'): '+task+'.' if arm=='ainglish' else ('Keep all named clauses active and add without precedence: ' if add else 'Retire all named whole clauses\' still-uncompleted obligations and replace them with: ')+task+' (named clauses: '+refs+').'

def clean(text):
    # Mechanical presentation normalization, before freezing or any exposure.
    # Preserve timestamps, dates and identifiers; separate accidentally joined prose.
    return re.sub(r'\b(The|At|at|to|than|by|until|totals|exactly|contains|Add|remove|receive)(?=\d)',r'\1 ',text)

FRAME_NAMES={
 'participants':['quoted-addressee-versus-new-addressee','two-addressed-groups','current-membership-versus-historical-message','membership-is-not-execution-permission'],
 'unknown':['gap-kind-versus-reader-authority','two-independent-issues','asserted-marker-versus-external-decision-log','decision-state-changes-after-a-report'],
 'deadline':['deadline-equality-and-phase','terminal-failure-versus-success','two-phase-deadlines-on-separate-actions','queueing-versus-execution'],
 'alternatives':['all-four-delivery-outcomes','local-choice-versus-quality-constraint','two-separate-disjunctions','both-branch-versus-separate-capacity-limit'],
 'multiplicity':['two-groups-whole-act-count','simultaneity-versus-unit-count','substeps-versus-complete-instances','shared-versus-per-person-payment'],
 'update':['two-exact-reference-local-updates','committed-chain-and-uncommitted-successor','retired-obligation-and-completed-external-history','all-or-nothing-reference-and-authority-validation'],
}

def structural(family,frame,i,arm):
    x=bool(i&1);y=bool(i&2);z=bool(i&4);d=DOMAINS[i]
    pre=f'This is an independent {d} record. '
    if family=='participants':
        if frame==0:
            text='Mira originally wrote directly to Noor: "'+we(x,arm)+' will check the first ledger." Jae later receives a verbatim forwarded copy; the addressee of that quotation stays Noor. Mira then writes a separate new message directly to Jae: "'+we(y,arm)+' will check the second ledger."'
            q=['Noor belongs to the first message’s checking group.','Jae belongs to the second message’s checking group.'];gold=(x,y)
        elif frame==1:
            text='Mira tells Noor "'+we(x,arm)+' will check the east room." Ivo independently tells Noor "'+we(y,arm)+' will check the west room." Neither message refers to the other group.'
            q=['Noor is included in the east-room group.','Noor is included in the west-room group.'];gold=(x,y)
        elif frame==2:
            text='At09:00 Mira tells Noor "'+we(x,arm)+' will inspect the ledger." At10:00 she explicitly withdraws that future plan and replaces it, addressing Noor again: "'+we(y,arm)+' will inspect the ledger." The earlier utterance remains a historical fact.'
            q=['The currently operative group includes Noor.','The09:00 message included Noor.'];gold=(y,x)
        else:
            text='Mira addresses Noor: "'+we(x,arm)+' will inspect the ledger." Separately, the access authority '+('has granted' if y else 'has not granted')+' Noor permission to begin now. Group membership does not itself grant access.'
            q=['The named inspection group includes Noor.','The access authority has granted Noor permission to begin now.'];gold=(x,y)
    elif family=='unknown':
        if frame==0:
            text=unknown(x,'which room the board selects',arm)+'. The reader '+('is' if y else 'is not')+' separately authorized to select the room. The report itself requests no action.'
            q=['Closing this particular gap requires a new authorized choice, not merely learning a determined answer.','The reader has separate authority to select the room.'];gold=(x,y)
        elif frame==1:
            text=unknown(x,'the board’s room selection',arm)+'. '+unknown(y,'the committee’s date selection',arm)+'. The issues are independent.'
            q=['The room issue lacks an operative choice.','The date issue lacks an operative choice.'];gold=(x,y)
        elif frame==2:
            text='An authoritative log says the board '+('has made' if x else 'has not made')+' its operative room selection. The reporting speaker has not learned any selection content. The speaker nevertheless asserts: "'+unknown(y,'which room the board selects',arm)+'." Assess that assertion against the external log; quoting it does not make it true.'
            q=['The board has an operative room selection.','The quoted state assertion agrees with the external log.'];gold=(x,x!=y)
        else:
            text='At09:00 the speaker truthfully reports "'+unknown(x,'which room the board selects',arm)+'." The board can change its decision. At10:00 an authoritative update says it '+('now has an operative selection' if y else 'now has no operative selection')+'. At11:00 the speaker knows that status, but not the content of any selection.'
            q=['The11:00 gap needs a new authorized choice.','The09:00 gap needed a new authorized choice.'];gold=(not y,x)
    elif family=='deadline':
        pre+='All clocks refer to2026-11-19 UTC. The stated task goal is successful delivery. '
        if frame==0:
            text='Requirement: '+deadline(x,'deliver the record',arm)+'. Genuine execution started at15:59Z; successful delivery occurred at'+('16:00Z' if y else '16:01Z')+'.'
            q=['The specified deadline was satisfied.','The requirement specifically constrains successful completion.'];gold=(not x or y,x)
        elif frame==1:
            text='Requirement: '+deadline(x,'deliver the record',arm)+'. Actual execution began at15:50Z. At16:00Z the process '+('successfully delivered the record' if y else 'stopped in terminal failure without delivery')+'.'
            q=['The specified deadline was satisfied.','Successful delivery occurred by16:00Z.'];gold=(not x or y,y)
        elif frame==2:
            text='East requirement: '+deadline(x,'deliver the east record',arm)+'. West requirement: '+deadline(y,'deliver the west record',arm)+'. Both genuinely began at15:59Z and successfully finished at16:01Z.'
            q=['The east deadline was satisfied.','The west deadline was satisfied.'];gold=(not x,not y)
        else:
            text='Requirement: '+deadline(x,'deliver the record',arm)+'. At15:00Z the worker acknowledged and queued it. The first task-specific execution step '+('occurred at16:00Z' if y else 'did not occur until16:01Z')+'. Successful delivery occurred at16:10Z. Queueing is not the requested delivery action.'
            q=['The specified deadline was satisfied.','The acknowledgement alone satisfied the specified deadline.'];gold=(not x and y,False)
    elif family=='alternatives':
        if frame==0:
            outcome=['neither a chart nor a note','only a chart','only a note','both a chart and a note'][i//2]
            text='Requirement: '+either(x,'provide a chart or a note',arm)+'. The actual delivery contains '+outcome+'. There are no other delivery constraints.'
            q=['The delivered selection satisfies the requirement.','The choice rule itself licenses delivering both.'];gold=(i//2 in [1,2] or (i//2==3 and x),x)
        elif frame==1:
            text='Requirement: '+either(x,'provide a chart or a note',arm)+'. All delivered documents must separately be signed. Both documents are delivered '+('with valid signatures' if y else 'without signatures')+'.'
            q=['The choice part alone accepts this selection.','The complete instruction, including signatures, is satisfied.'];gold=(x,x and y)
        elif frame==2:
            text='East job: '+either(x,'provide a chart or a note',arm)+'. West job: '+either(y,'provide a chart or a note',arm)+'. Both alternatives are supplied to each job; the jobs have separate choice requirements.'
            q=['The east selection satisfies its requirement.','The west selection satisfies its requirement.'];gold=(x,y)
        else:
            text='Requirement: '+either(x,'provide a chart or a note',arm)+'. A separate binding capacity rule permits at most '+('one document' if y else 'two documents')+'. Neither requirement overrides the other.'
            q=['The disjunction alone permits both documents.','Both documents can satisfy the combined rules.'];gold=(x,x and not y)
    elif family=='multiplicity':
        n=3+i%3
        if frame==0:
            text=plural(x,f'The{n} east inspectors verify the ledger',arm)+'. '+plural(y,f'The{n} west inspectors verify a different ledger',arm)+'. These are two distinct jobs.'
            q=['The east group performs one whole verification.','The two groups together perform exactly two whole verifications.'];gold=(x,x and y)
        elif frame==1:
            text=plural(x,f'The{n} inspectors verify the ledger',arm)+'. Their assigned work starts '+('simultaneously' if y else 'at different times')+'. A group act may contain differently timed contributions.'
            q=['There is one whole verification instance.','The assigned work starts simultaneously.'];gold=(x,y)
        elif frame==2:
            text=plural(x,f'The{n} inspectors verify the ledger',arm)+'. Each whole verification contains exactly three separately logged substeps. The log '+('also records a separate later verification by an auditor' if y else 'records no other verification')+'.'
            q=['The inspectors’ required work comprises exactly three substeps in total.','The complete log contains more whole verification instances than the inspectors’ work alone.'];gold=(x,y)
        else:
            grant=(f'The {n} recipients receive 100 credits, '+('as-one' if x else 'each-alone')+'.') if arm=='ainglish' else (
                f'The {n} recipients receive a single grant of 100 credits shared among them.' if x else f'Each of the {n} recipients receives a separate grant of 100 credits.')
            text=grant+' '+('The shared amount, if any, must be divided equally.' if y else 'No division of a shared amount is specified.')
            q=[f'The stated grant totals{n*100} credits.',f'The record determines that each recipient receives exactly{100/n:.6f} credits (rounded to six decimals).'];gold=(not x,x and y)
    elif family=='update':
        pre+='Clause IDs are immutable. Unless stated otherwise, references resolve uniquely, the sender has authority, and updates commit in the stated order before further work. The ledger accepts an update only if ALL named references resolve to active clauses within the sender’s authority. Otherwise the ENTIRE update is invalid: no new standalone clause activates and no earlier clause retires. Valid updates apply only at their declared receipt/commit event. Retiring an obligation does not undo completed external history. '
        if frame==0:
            text='A requires copying the east ledger; B separately requires copying the west ledger. Both are active and uncompleted. C commits: '+relation(x,'A','req: photograph the east ledger',arm)+' D then commits: '+relation(y,'B','req: photograph the west ledger',arm)
            q=['A remains active.','B remains active.'];gold=(x,y)
        elif frame==1:
            text='B has validly superseded A, so A is inactive and B active. The new message C says '+relation(x,'B','req: sign the ledger',arm)+' The ledger '+('has committed C' if y else 'has not yet reached C’s receipt/commit event')+'.'
            q=['B remains active now.','C’s new action is active now.'];gold=(x or not y,y)
        elif frame==2:
            text='A requires printing and delivering the ledger. Printing already produced a physical page; delivery is uncompleted. C says '+relation(x,'A','req: photograph the ledger',arm)+' C '+('has committed' if y else 'has not committed')+'. C requests no cancellation, deletion, repetition or compensation.'
            q=['A’s still-uncompleted delivery obligation remains active now.','The already printed physical page remains part of the historical record.'];gold=(x or not y,True)
        else:
            text='A is active and resolved. B '+('is also active and uniquely resolved' if x else 'is missing and cannot be resolved')+'. The sender '+('has' if y else 'does not have')+' authority to update A and B. The ledger receives C: '+relation(False,'A,B','req: sign the ledger',arm)+' There is no independent standalone instruction to sign.'
            valid=x and y;q=['C validly activates the signing obligation.','A stays active after this received update.'];gold=(valid,not valid)
    else:raise ValueError(family)
    return clean(pre+text),[clean(s) for s in q],gold

def general(i,split):
    # Same families of ordinary English in rehearsal/retention, disjoint numbers,
    # labels and question instances. Not a claim of structural independence.
    base=1000 if split=='rehearsal' else 5000;n=base+i*11
    if i%4==0:
        values=[str(n+7),str(n+8),str(n+9),str(n+10)];gold=str(n+8)
        text=f'A tray contains{n} counters. Add11 and remove3.';q='How many counters remain?'
    elif i%4==1:
        values=[f'bin-{n+j}' for j in range(4)];gold=values[2]
        text='One recorded bin is '+gold+'. No other bin is selected.';q='Which bin is recorded?'
    elif i%4==2:
        values=[f'card-{n+j}' for j in range(4)];gold=values[0]
        text=f'The ordering is {values[3]} before {values[2]}, {values[2]} before {values[1]}, and {values[1]} before {values[0]}.';q='Which card is last in this ordering?'
    else:
        values=[str(n),str(n+1),str(n+2),str(n+3)];gold=values[3]
        text='The allowed set contains '+', '.join(values)+'.';q='What is the greatest allowed number?'
    options,answer=labelled(values,gold,(i//4)%4,shuffle_seed=base+i)
    return {'id':f'{split}/{i:03d}','case_id':f'{split}/{i:03d}','family':'ordinary-english',
        'frame':f'ordinary-{i%4}','study':split,'arm':'english','semantic_gold':gold,
        'options':options,'answer':answer,'messages':messages(clean(text),q,options)}

def main():
    source=ROOT.parent/'contextual-teaching-2026-09-07/curriculum.jsonl'
    curriculum=[json.loads(line) for line in source.read_text().splitlines()]
    rehearsal=[general(i,'rehearsal') for i in range(192)]
    train={a:[] for a in ['ainglish','english']}
    for i,row in enumerate(curriculum):
        correct=row['answer']
        pool=['Yes','No','Not stated','Contradictory'] if correct in ['Yes','No'] else ([str(n) for n in [1,3,4,5,6]] if correct.isdigit() else
            ['An authorized choice','Evidence of the determined answer','Actual execution starting','Successful completion'])
        choices=[correct]+[x for x in pool if x!=correct][:3]
        # Rotate answer positions across frames as well as domains: a domain
        # name alone must not determine the answer label throughout training.
        opts,answer=labelled(choices,correct,i+i//12,shuffle_seed=10000+i)
        for arm in train:
            train[arm].append({'id':row['id'],'messages':messages(row[arm]+'\nScope note: '+row['scope_note'],row['question'],opts)+[{'role':'assistant','content':answer}]})
    for arm in train:
        train[arm]+=[{'id':r['id'],'messages':r['messages']+[{'role':'assistant','content':r['answer']}]} for r in rehearsal]
        with (ROOT/f'train-{arm}.jsonl').open('x') as f:
            for row in train[arm]:f.write(json.dumps(row,ensure_ascii=False)+'\n')
    cases=[];tasks=[]
    for family in sorted(FRAME_NAMES):
        for frame,name in enumerate(FRAME_NAMES[family]):
            for i,domain in enumerate(DOMAINS):
                a,q,gold=structural(family,frame,i,'ainglish');e,q2,gold2=structural(family,frame,i,'english');assert (q,gold)==(q2,gold2)
                semantic=PAIR_OPTIONS[(0 if gold[0] else 2)+(0 if gold[1] else 1)]
                opts,answer=labelled(PAIR_OPTIONS,semantic,i+frame,shuffle_seed=20000+len(cases))
                question='For each conclusion below, does the record warrant it? Not warranted does not mean that its opposite is known true.\nFirst: '+q[0]+'\nSecond: '+q[1]
                cid=f'holdout-{len(cases)+8100}'
                row={'id':cid,'case_id':cid,'family':family,'frame':family+'/'+name,'context':domain,
                    'ainglish':a,'english':e,'question':question,'conclusions':q,'gold_bits':list(gold),
                    'options':opts,'answer':answer,'semantic_gold':semantic,'study':'structural-transfer'}
                cases.append(row)
                for arm in train:tasks.append({**row,'id':cid+'/'+arm,'arm':arm,'messages':messages(row[arm],question,opts)})
    tasks += [general(i,'retention') for i in range(96)]
    for name,rows in [('cases.jsonl',cases),('tasks.jsonl',tasks),('rehearsal.jsonl',rehearsal)]:
        with (ROOT/name).open('x') as f:
            for row in rows:f.write(json.dumps(row,ensure_ascii=False)+'\n')
    training=json.loads((ROOT.parent/'learning-transfer-2026-09-06/PLAN.json').read_text())['training']
    training.update(epochs=1,batch_size=2,gradient_accumulation_steps=8,max_length=1024)
    plan={'kind':'ainglish.contextual-structural-transfer.v1','seed':17,'seeds':[17,29],
        'base_revision':'a09a35458c702b33eeacc393d103063234e8bc28','training':training,
        'conditions':['base','ainglish-17','english-17','ainglish-29','english-29'],
        'training_rows_per_arm':768,'contextual_teaching_rows':576,'identical_english_rehearsal_rows':192,
        'holdout_cases':192,'authored_structural_frames':24,'target_calls_per_condition':480,'max_target_calls':2400,
        'guards':{'max_prompt_tokens':2048,'minimum_correct_controls':11,'control_items':12,'maximum_truncations_controls':0,
            'minimum_ram_before_load_gib':14,'physical_gpu':0,'physical_disk_reserve_gib':15,'target_retries':0,'downloads':0},
        'primary':'For each fixed seed: Ainglish-trained minus matched English-trained accuracy on the Ainglish structural holdout without a glossary. Task-local facts and ledger boundary rules are supplied equally in both languages. Report all24 frames and six families; do not select the better seed.',
        'retention':'Ainglish-trained minus base on paired careful English structural tasks, and separately96 ordinary English items. Same -5pp point screen overall and per language family; point estimates are screens, not statistical non-inferiority proofs.',
        'analysis':'2000 paired bootstrap draws resampling24 authored structural frames, seed2026090770. Every output and failed qualification retained. Qualification is per model condition; unqualified conditions have no invented target score. Ordinary-English rehearsal/retention are related authored families, not an independent benchmark.',
        'changes':'Larger contextual curriculum, common ordinary-English rehearsal, four-choice answer alignment, one epoch with batch2. Multiple changes plus a changed holdout prevent a causal attribution versus earlier runs.',
        'limits':['One cached Qwen2.5-7B family, two training seeds, synthetic single-author tasks. Not independent human validation or governance evidence.',
            '192 semantic configurations instantiate24 authored frames. More domains or rows are not192 independent task structures.',
            'Frames exercise reference tracking, temporal state, action traces, joint constraints and boundaries absent from the simple single-question teaching rows. Task-local background sometimes supplies relevant boundary rules in both arms; this is not wholly unassisted understanding. Related reasoning may occur in prior published tests; novelty is relative to this frozen training split, not globally unseen concepts.',
            'The model and fixed tokenizer already know English. This is modest adapter learning, not a future large-scale pretraining or tokenizer-replacement forecast.',
            'All four adapters must be trained and publicly digest-sealed before any heldout evaluation. No adaptive epochs, favourable seed selection, post-hoc re-scoring or uncertain-call retry.',
            'No full model checkpoints or downloads. Existing cached models remain untouched. Total new adapter allowance is2GiB with at least15GiB physical host reserve.']}
    save('PLAN.json',plan)
    names=['build.py','audit.py','run.py','analyse.py','test_design.py','README.md','PLAN.json','cases.jsonl','tasks.jsonl','rehearsal.jsonl','train-ainglish.jsonl','train-english.jsonl',
        '../contextual-teaching-2026-09-07/curriculum.jsonl','../contextual-teaching-2026-09-07/source-constructs.json',
        '../ratified-learning-pilot-2026-09-06/run.py','../overnight-runtime-2026-09-06/runtime.py']
    save('FROZEN.json',{name:sha(ROOT/name) for name in names})
    print('Built768 paired training rows,192 structural cases in24 frames,480 targets per condition. No model calls.')

if __name__=='__main__':main()
