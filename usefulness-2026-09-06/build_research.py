"""Prospective research inputs; synthetic, non-normative, not settlement evidence."""
import hashlib
import importlib.util
import json
from pathlib import Path
import random

ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'ratified-learning-pilot-2026-09-06'
spec=importlib.util.spec_from_file_location('prior_case_grammar',OLD/'build.py')
grammar=importlib.util.module_from_spec(spec);spec.loader.exec_module(grammar)
SYSTEM='Use only the supplied facts and rules. Return exactly one offered option letter, with no explanation. Do not invent missing facts.'
FAMILIES=list(grammar.SLUGS)
TRAIN=['arboretum','lighthouse','pottery','herbarium']
TEST=['planetarium','hatchery','tapestry','windmill','aqueduct','boathouse']
SEED=2026090613


def save(name,value):
    path=ROOT/name;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as h:json.dump(value,h,indent=2,ensure_ascii=False);h.write('\n')


def write_rows(name,values):
    with (ROOT/name).open('x') as h:
        for value in values:h.write(json.dumps(value,ensure_ascii=False,sort_keys=True)+'\n')


def pin(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def options(values,gold,position):
    other=[v for i,v in enumerate(values) if i!=gold]
    ordered=other[:position]+[values[gold]]+other[position:]
    return dict(zip('ABCD',ordered)),'ABCD'[position]


def rows(split,contexts):
    result=[]
    for family in FAMILIES:
        cases=[];seen=set()
        for context in contexts:
            for variant in range(8):
                a,e,q,choices,gold,boundary=grammar.scenario(family,context,variant,split=='test')
                key=(a,e,q,tuple(choices))
                if key in seen:continue
                seen.add(key)
                cases.append({'id':f'{split}/{family}/{context}/{variant}','family':family,'frame':f'{family}/grammar-{variant}',
                              'ainglish':a,'english':e,'question':q,'choice_values':choices,'gold_index':gold,
                              'semantic_gold':choices[gold],'boundary_case':boundary})
        # Balance globally as well as within each family. Starting every family
        # at A accumulates remainder rows into an artificial label advantage.
        positions=[(len(result)+i)%3 for i in range(len(cases))]
        random.Random(SEED+FAMILIES.index(family)+(100 if split=='test' else 0)).shuffle(positions)
        for case,position in zip(cases,positions):
            case['options'],case['answer']=options(case.pop('choice_values'),case.pop('gold_index'),position)
            result.append(case)
    return result


def messages(case,arm):
    language=arm.split('-')[0]
    body=case[language]
    if arm.endswith('-reference'):
        body='Reading guide: '+grammar.GUIDES[case['family']][0 if language=='ainglish' else 1]+'\n\n'+body
    body+='\n\n'+case['question']+'\n'+'\n'.join(k+'. '+v for k,v in case['options'].items())
    return [{'role':'system','content':SYSTEM},{'role':'user','content':body}]


def simple(study,ident,family,body,question,values,gold,position,arm,frame=None):
    opts,answer=options(values,gold,position)
    text=body+'\n\n'+question+'\n'+'\n'.join(k+'. '+v for k,v in opts.items())
    return {'id':f'{study}/{ident}/{arm}','study':study,'case_id':str(ident),'family':family,
            'frame':frame or str(ident),'arm':arm,'options':opts,'answer':answer,'semantic_gold':values[gold],
            'messages':[{'role':'system','content':SYSTEM},{'role':'user','content':text}]}


def writer_and_wording():
    writer=[];wording=[]
    for ci,context in enumerate(TEST):
        for fi,family in enumerate(FAMILIES):
            for pole in range(2):
                ident=f'{family}/{context}/{pole}';task=context+'-check';ref=context+'-request'
                if family=='participants':
                    intents=['The announced group includes the addressed recipient.','The announced group excludes the addressed recipient.']
                    a=[f'we-including-you will inspect {task}.',f'we-excluding-you will inspect {task}.',f'we will inspect {task}.']
                    e=[f'We, including you, will inspect {task}.',f'We, excluding you, will inspect {task}.',f'We will inspect {task}.']
                    q='Is the addressed recipient in the announced group?';values=['Yes','No','Not determined'];gold=pole
                    bits=['we-including-you','we-excluding-you']
                elif family=='deadline':
                    intents=['The deadline constrains actual execution starting, with no finish deadline.','The deadline constrains successful completion, not mere termination.']
                    a=[f'Please execute {task} start-by(17:00Z).',f'Please execute {task} complete-by(17:00Z).',f'Please execute {task} by 17:00Z.']
                    e=[f'Begin actual execution of {task} no later than 17:00Z; no finish deadline is specified.',f'Successfully complete {task} no later than 17:00Z.',f'Please execute {task} by 17:00Z.']
                    q='Which event must happen by the deadline?';values=['Actual execution begins','Successful completion','Not determined'];gold=pole
                    bits=['start-by','complete-by']
                elif family=='unknown':
                    intents=['The board has already selected a region, but the speaker lacks evidence of which.','The board has not yet made its operative region selection.']
                    a=[f'fact-not-known — which region the board selected for {task}.',f'choice-not-made — which region the board will select for {task}.',f'The region for {task} is pending.']
                    e=[f'The board has selected a region for {task}, but I lack evidence of which.',f'The board has not yet made its operative region selection for {task}.',f'The region for {task} is pending.']
                    q='What kind of gap is described?';values=['Evidence of an existing answer','An authorized selection','Not determined'];gold=pole
                    bits=['fact-not-known','choice-not-made']
                elif family=='multiplicity':
                    intents=['Three inspectors each perform a separate check.','Three inspectors jointly perform one check.']
                    a=[f'Three inspectors verify {task}, each-alone.',f'Three inspectors verify {task}, as-one.',f'Three inspectors verify {task}.']
                    e=[f'Each of three inspectors independently verifies {task}.',f'Three inspectors jointly perform one verification of {task}.',f'Three inspectors verify {task}.']
                    q='How many separate verifications are stated?';values=['3','1','Not determined'];gold=pole
                    bits=['each-alone','as-one']
                elif family=='alternatives':
                    intents=['At least one of text and chart is required, and both are permitted.','Exactly one of text and chart is required; both are forbidden.']
                    a=[f'For {task}, supply text or a chart, or-both.',f'For {task}, supply text or a chart, not-both.',f'For {task}, supply text or a chart.']
                    e=[f'For {task}, supply text, a chart, or both; at least one is required.',f'For {task}, supply exactly one of text and a chart, but not both.',f'For {task}, supply text or a chart.']
                    q='Are both text and chart allowed together?';values=['Yes','No','Not determined'];gold=pole
                    bits=['or-both','not-both']
                else:
                    intents=[f'Retire all uncompleted obligations of active {ref} and issue the new archive request.',f'Keep active {ref} and add the new archive request without precedence.']
                    common=f'{ref} is an active, uncompleted instruction issued by the current speaker. This authorized update commits now; no work is in flight. '
                    a=[common+f'supersedes({ref}): Please archive {task}.',common+f'supplements({ref}): Please archive {task}.',common+f'Update: please archive {task}.']
                    e=[common+f'Replace the whole of {ref}, retiring its uncompleted obligations: please archive {task}.',common+f'Keep {ref} active and add without precedence: please archive {task}.',common+f'Update: please archive {task}.']
                    q=f'Does {ref} remain an active obligation?';values=['No','Yes','Not determined'];gold=pole
                    bits=['supersedes','supplements']
                for arm,candidates in [('ainglish',a),('english',e)]:
                    writer.append(simple('writer',ident,family,'Drafting brief: '+intents[pole],
                        'Which candidate faithfully and explicitly communicates the intended distinction?',candidates,pole,(ci+fi+pole)%3,arm,frame=f'{family}/{pole}'))
                forms={'english':e[pole],'ainglish':a[pole], 'spaces':a[pole]}
                for marker in bits:forms['spaces']=forms['spaces'].replace(marker,marker.replace('-',' '))
                forms['labels']=a[pole].replace(bits[pole],['type-alpha','type-beta'][pole])
                for form,body in forms.items():
                    for reference in [False,True]:
                        guide=grammar.GUIDES[family][1 if form=='english' else 0]
                        if form=='spaces':
                            for marker in bits:guide=guide.replace(marker,marker.replace('-',' '))
                        if form=='labels':
                            for marker,label in zip(bits,['type-alpha','type-beta']):guide=guide.replace(marker,label)
                        if reference:body2='Reading guide: '+guide+'\n\n'+body
                        else:body2=body
                        wording.append(simple('wording',ident,family,body2,q,values,gold,(ci+fi+pole)%3,
                            form+('-reference' if reference else '-cold'),frame=f'{family}/{pole}'))
    return writer,wording


def workflow():
    out=[]
    for n in range(32):
        addition=bool(n%2);inflight=bool((n//2)%2);completed=bool((n//4)%2)
        a_ref=f'job-{n}-upload';b_ref=f'job-{n}-checksum';c_ref=f'job-{n}-archive'
        base=f'Ledger {n}: active uncompleted A={a_ref}, B={b_ref}. Both were issued by the current sender. References resolve uniquely. The sender is authorized. All updates are whole clauses and commit at the stated ledger event. '
        logs=[]
        for phase in range(3):
            if phase==1:logs.append('Before event 1, the upload is '+('dispatched and in flight; no physical cancellation is promised.' if inflight else 'not dispatched.'))
            if phase==2:logs.append('Before event 2, '+('the upload completed, producing an external file. No deletion or compensation is requested.' if completed else 'no completion is observed and no deletion or compensation is requested.'))
            for lang in ['ainglish','english']:
                history=base+'\n'+'\n'.join(logs)
                if phase>=1:
                    history+='\nEvent 1, new clause C: '+(f'{"supplements" if addition else "supersedes"}(A): Please perform {c_ref}.' if lang=='ainglish' else (f'Keep A active and add without precedence: please perform {c_ref}.' if addition else f'Retire all uncompleted obligations of A and replace it with: please perform {c_ref}.'))
                if phase==2:history+='\nEvent 2: '+('supersedes(C): Please inspect the archive.' if lang=='ainglish' else 'Retire all uncompleted obligations of C and replace that whole clause with: please inspect the archive.')
                if phase==0:q='Which obligations are active now?';values=['A and B','Only A','Only B'];gold=0
                elif phase==1:q='Which obligations remain active after event 1?';values=['A, B and C','B and C','Only C'];gold=0 if addition else 1
                else:
                    q='Which operational conclusion is warranted after event 2?'
                    values=['A completed external file is not undone by this instruction update.','The instruction update does not establish that an in-flight upload stopped or that a file was deleted.','Event 2 proves that the old upload was physically cancelled and any file erased.']
                    gold=0 if completed else 1
                row=simple('workflow',f'episode-{n}/checkpoint-{phase}','update',history,q,values,gold,(n+phase)%3,lang,frame=f'episode-{n}')
                row.update(checkpoint=phase,addition=addition,inflight=inflight,completed=completed)
                out.append(row)
    return out


def composition():
    out=[]
    for ci,context in enumerate(TEST):
        for p in range(2):
            for d in range(2):
                for late in range(2):
                    task=context+'-upload';form=['start-by','complete-by'][d];time=['16:59Z','17:01Z'][late]
                    common=f'This is one group action called {task}. You are directly addressed. All times refer to 2032-02-03 UTC. '
                    log=f'Observed: actual execution began at {time}; successful completion occurred at {time}. '
                    a=common+f'we-{["including","excluding"][p]}-you will perform {task} {form}(17:00Z). '+log
                    e=common+f'We, {["including","excluding"][p]} you, will '+([f'begin actual execution of {task}',f'successfully complete {task}'][d])+' no later than 17:00Z. '+log
                    values=['Recipient included; deadline met','Recipient included; deadline missed','Recipient excluded; deadline met','Recipient excluded; deadline missed'];gold=p*2+late
                    for arm,body in [('ainglish',a),('english',e)]:out.append(simple('composition',f'actors/{context}/{p}/{d}/{late}','participants+deadline',body,'Which two facts follow together?',values,gold,(ci+p+d+late)%4,arm,frame=f'actors/{p}/{d}/{late}'))
                # Eight cases per context above; four multiplicity/choice cases below.
                n=3+ci;task=context+'-checks'
                a=f'The {n} inspectors verify {task}, {["each-alone","as-one"][p]}. For the report, provide text or a chart, {["or-both","not-both"][d]}.'
                e=(f'Each of {n} inspectors independently verifies {task}.' if p==0 else f'The {n} inspectors jointly perform one verification of {task}.')+' For the report, '+('provide text, a chart, or both; at least one is required.' if d==0 else 'provide exactly one of text and a chart, but not both.')
                values=[f'{n} acts; both formats permitted',f'{n} acts; both formats forbidden','1 act; both formats permitted','1 act; both formats forbidden'];gold=p*2+d
                for arm,body in [('ainglish',a),('english',e)]:out.append(simple('composition',f'counts/{context}/{p}/{d}','multiplicity+alternatives',body,'What are the number of checking acts and the permission for both report formats?',values,gold,(ci+p+d)%4,arm,frame=f'counts/{p}/{d}'))
    return out


def build():
    train=rows('train',TRAIN);test=rows('test',TEST)
    write_rows('curriculum.jsonl',train);write_rows('retention.jsonl',test)
    for lang in ['ainglish','english']:
        write_rows('train-'+lang+'.jsonl',[{'id':r['id'],'messages':messages(r,lang+'-cold')+[{'role':'assistant','content':r['answer']}]} for r in train])
    tasks=[]
    for case in test:
        for lang in ['ainglish','english']:
            tasks.append({**case,'id':case['id']+'/'+lang,'case_id':case['id'],'study':'retention','arm':lang,'messages':messages(case,lang+'-cold')})
    writer,wording=writer_and_wording();tasks+=writer+wording+workflow()+composition()
    # Counterfactual diagnostic: permuting options is NOT a new semantic sample.
    counterfactual=[]
    for row in [r for r in tasks if r['study']=='wording' and r['family']=='participants' and r['arm']=='ainglish-cold']:
        order=list(row['options']);new_order=order[1:]+order[:1]
        vals=[row['options'][x] for x in new_order];gold=vals.index(row['semantic_gold'])
        body=row['messages'][1]['content'].split('\n\n')[0]
        counterfactual.append(simple('option-permutation',row['case_id'],row['family'],body,'Is the addressed recipient in the announced group?',vals,gold,gold,row['arm'],frame=row['frame']))
    tasks+=counterfactual
    write_rows('research-tasks.jsonl',tasks)
    old_plan=json.loads((OLD/'PLAN.json').read_text())
    save('PLAN.json',{'kind':'ainglish.usefulness-research.v1','seed':SEED,'base_revision':old_plan['base_revision'],
        'training':old_plan['training'],'source_register':json.loads((OLD/'source-constructs.json').read_text())['source_url'],
        'source_mapping_sha256':pin(OLD/'source-constructs.json'),'grammar_sha256':pin(OLD/'build.py'),'runner_sha256':pin(OLD/'run.py'),
        'conditions':['base','ainglish','english'],'secondary_conditions':['prior-ainglish','prior-english'],
        'design':'Two new paired curricula, balanced decoded labels, exact repeats removed before training/evaluation. Same eight established case grammars with disjoint new domain words; this is template-level lexical transfer, NOT unseen semantic-family generalization.',
        'studies':{'retention':'Primary: A-trained minus matched E-trained cold-A accuracy; require overall and every family >= -5pp, plus English retention >= -5pp versus base. Report frame-cluster intervals; a point guard is not a non-inferiority proof.',
                   'writer':'Constrained sender choice among a faithful draft, a wrong-pole draft and an under-specified draft. Not free-form writing, natural uptake or human authoring.',
                   'wording':'Four information-bearing renderings crossed with cold/reference: careful English, exact Ainglish, hyphens-to-spaces, arbitrary type labels. Report reference budgets/native tokens; do not call this equal-compute training.',
                   'workflow':'32 authored three-checkpoint ledger traces. Active obligations, in-flight work and completed effects stay separate. Repeated checkpoints are clustered by episode; no actual production actions.',
                   'composition':'Participant/deadline and multiplicity/disjunction crossed worlds; complete four-option joint states. Not exhaustive composition or a parser conformance claim.',
                   'option-permutation':'Same participant cases with new answer-code assignment; diagnostic consistency only, never additional independent samples.'},
        'guards':{'control_items':12,'minimum_correct_controls':11,'max_invalid_controls':0,'target_retries':0,
                  'target_policy':'Retain every result, including malformed responses; score malformed as incorrect. Any transport/runtime exception stops the campaign with no target retry.',
                  'disk_reserve_gib':10,'downloads':0},
        'analysis':'All directions, absolute per-arm and per-family accuracy, decoded-label and semantic baselines, case and template/episode counts, raw outputs, input/output tokens, pair discordance. 2,000 frame-cluster bootstrap draws, seed2026090613. No settlement writes or claims of independent measurement.'})
    paths=['build_research.py','research_runner.py','audit_research.py','curriculum.jsonl','retention.jsonl','train-ainglish.jsonl','train-english.jsonl','research-tasks.jsonl','PLAN.json']
    save('FROZEN.json',{p:pin(ROOT/p) for p in paths})
    print(json.dumps({'training_distinct_rows':len(train),'retention_distinct_rows':len(test),'tasks_per_new_condition':len(tasks),'studies':{k:sum(r['study']==k for r in tasks) for k in sorted({r['study'] for r in tasks})}}))


if __name__=='__main__':build()
