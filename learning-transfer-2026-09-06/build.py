"""Prospective synthetic reasoning-transfer and communication experiments."""
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PRIOR=ROOT.parent/'ratified-learning-pilot-2026-09-06'
spec=importlib.util.spec_from_file_location('original_teaching_grammar',PRIOR/'build.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
SYSTEM='Use only the supplied facts and rules. Return exactly one offered option letter, without explanation. Do not invent missing facts.'
TRAIN=['orchard','kiln','quarry','marina','weavery','bakery','greenhouse','foundry']
TEST=['turbine','aviary','archive','ceramics','reservoir','tramway']
FAMILIES=list(old.SLUGS)

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def dump(path,value):
    # Generated runtime receipts, never authored or frozen inputs.
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def save(name,value):
    path=ROOT/name;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
def write_rows(name,values):
    with (ROOT/name).open('x') as f:
        for value in values:f.write(json.dumps(value,ensure_ascii=False,sort_keys=True)+'\n')
def messages(row,lang):
    return [{'role':'system','content':SYSTEM},{'role':'user','content':row[lang]+'\n\n'+row['question']+'\n'+'\n'.join(k+'. '+v for k,v in row['options'].items())}]
def row(ident,family,frame,a,e,q,values,gold,index,**more):
    assert len(values)==len(set(values)) and 0<=gold<len(values)
    position=index%len(values);others=[x for i,x in enumerate(values) if i!=gold]
    opts=others[:position]+[values[gold]]+others[position:]
    return dict(id=ident,family=family,frame=frame,ainglish=a,english=e,question=q,
                options=dict(zip('ABCD',opts)),answer='ABCD'[position],semantic_gold=values[gold],**more)

def novel(family,context,v):
    """Six manually specified reasoning structures per family, not just new nouns."""
    name=context+'-task';yes=['Yes','No','Not determined'];n=4
    if family=='participants':
        a='we-including-you';e='we, including you,'
        if v==0:
            prefix='Kai originally addressed Leo. Mira later reads a verbatim forwarded copy; forwarding does not change the original addressee. '
            tail=f' will inspect {name}. No other group membership is recorded.'
            return prefix+a+tail,prefix+e+tail,'Does the original announcement establish that Mira belongs to the group?',yes,2
        if v==1:
            a='we-excluding-you';e='we, excluding you,'
            prefix=f'Ada addresses you. A separate active instruction already requires you to submit {context}-notes. '
            tail=f' will inspect {name}. Nothing changes the separate instruction.'
            return prefix+a+tail,prefix+e+tail,'Does exclusion from the inspecting group cancel your separate submission duty?',yes,1
        if v==2:
            prefix='One sender makes two announcements to the same directly addressed recipient. '
            return prefix+f'For {name}-red: we-including-you will inspect. For {name}-blue: we-excluding-you will inspect.',prefix+f'For {name}-red: we, including you, will inspect. For {name}-blue: we, excluding you, will inspect.','In which announced group is that recipient included?',['Red only','Blue only','Both'],0
        if v==3:
            prefix='A coordinator addresses Leo; Mira observes but is not addressed. '
            tail=f' will inspect {name}.'
            return prefix+a+tail,prefix+e+tail,'Which named person is explicitly included by the address-sensitive wording?',['Leo','Mira','Neither'],0
        if v==4:
            prefix='On Monday Ada addressed Leo. On Tuesday Ada addresses Mira and quotes the unchanged Monday sentence. '
            tail=f' will inspect {name}.'
            return prefix+a+tail,prefix+e+tail,'Does the later quotation replace Leo with Mira in the original announced group?',yes,1
        prefix='A team announcement is addressed to you, but access to the secure room independently requires a badge that you do not hold. '
        tail=f' will inspect {name}.'
        return prefix+a+tail,prefix+e+tail,'Does group membership itself waive the separate badge requirement?',yes,1
    if family=='deadline':
        common=f'All times are for one UTC day. Task {name}. '
        scenarios=[
            ('start-by(09:00Z)','Begin actual execution no later than09:00Z.','Actual execution starts08:59Z and succeeds09:20Z.','Is the stated start deadline met?',0),
            ('start-by(09:00Z) and complete-by(10:00Z)','Begin actual execution no later than09:00Z and successfully finish no later than10:00Z.','Execution starts08:59Z but fails09:30Z; no successful finish occurs that day.','Are both stated deadlines met?',1),
            ('complete-by(10:00Z)','Successfully finish no later than10:00Z.','The first attempt fails09:00Z; a retry successfully finishes09:45Z.','Is the successful-completion deadline met?',0),
            ('complete-by(10:00Z)','Successfully finish no later than10:00Z.','The only attempt is cancelled09:50Z and never succeeds.','Does this satisfy the completion deadline?',1),
            ('start-by(09:00Z)','Begin actual execution no later than09:00Z.','Acknowledgement is08:30Z. No execution timestamp or bound is available.','Is actual execution known to have met the deadline?',2),
            ('complete-by(09:00Z)','Successfully finish no later than09:00Z.','Success is recorded10:00 at UTC+01:00, exactly09:00Z.','Is the deadline met?',0)]
        a,e,log,q,g=scenarios[v]
        return common+'Instruction: '+a+'. '+log,common+'Instruction: '+e+' '+log,q,yes,g
    if family=='unknown':
        if v==0:
            common=f'The board made the {name} choice in private. Its secretary knows it; the speaker does not. '
            return common+'fact-not-known — the selected region.',common+'The selected region is already determined, but I lack evidence of which region it is.','Must the board choose again merely to close the speaker\'s evidence gap?',yes,1
        if v==1:
            common=f'A displayed draft preference for {name} is non-operative; only the board may decide. '
            return common+'choice-not-made — the operative region selection.',common+'No operative authorized region selection has yet been made.','Does the displayed preference itself close the reported decision gap?',yes,1
        if v==2:
            common=f'A report about {name} says: '
            a=common+'fact-not-known — yesterday\'s checksum match. The speaker then receives a conclusive authentic match record.'
            e=common+'Yesterday\'s match is determined, but I lack evidence of it. The speaker then receives a conclusive authentic match record.'
            return a,e,'Does the new receipt close that particular evidence gap without a new selection?',yes,0
        if v==3:
            common=f'A former region selection for {name} was explicitly annulled, with no replacement. '
            return common+'choice-not-made — the new operative selection.',common+'No new operative authorized selection has yet been made.','Does knowing the annulled historical choice settle the new operative choice?',yes,1
        if v==4:
            common=f'A board status note about {name} is only descriptive. You have no decision authority. '
            return common+'choice-not-made — the region selection.',common+'No operative authorized region selection has yet been made.','Which act would close the described gap?',['An authorized operative selection','An unauthorized observer selecting a region','Repeating the status note'],0
        common=f'For {name}, two speakers report on two different questions. '
        return common+'First: fact-not-known — yesterday\'s checksum. Second: choice-not-made — tomorrow\'s approved region.',common+'First: yesterday\'s checksum is determined but the speaker lacks evidence. Second: tomorrow\'s operative region has not yet been selected.','Which gap requires an operative selection rather than evidence about an existing answer?',['First','Second','Both'],1
    if family=='multiplicity':
        if v==0:
            return f'The {n} inspectors check {name}, as-one, then sign {context}-receipts, each-alone.',f'The {n} inspectors jointly perform one check of {name}, then each independently performs one receipt-signing act.','How many check and signing acts are stated in total?',[str(n+1),str(2*n),'2'],0
        if v==1:
            return f'Two disjoint teams of {n} inspect {name}. Within each team the inspectors act as-one; the two team inspections are separate.',f'Two disjoint teams of {n} each perform one collective inspection of {name}; the two team inspections are separate.','How many inspection acts are established?',['2',str(2*n),'1'],0
        if v==2:
            return f'In each of two separate rounds, the {n} inspectors verify {name}, each-alone.',f'In each of two separate rounds, each of the {n} inspectors independently verifies {name}.','How many separate verifications are stated across both rounds?',[str(2*n),str(n),'2'],0
        if v==3:
            return f'The {n} inspectors complete one agreed inspection of {name}, as-one. They carry out its substeps in sequence, not simultaneously.',f'The {n} inspectors complete one collective inspection of {name}. They carry out its substeps in sequence, not simultaneously.','Does sequential timing alone turn this into one independent inspection per person?',yes,1
        if v==4:
            return f'The {n} inspectors check the whole two-part {name} packet, each-alone. Each person\'s check is one act over the entire packet.',f'Each of the {n} inspectors independently performs one check of the entire two-part {name} packet.','How many checking acts, rather than packet parts, are stated?',[str(n),str(2*n),'1'],0
        return f'The {n} inspectors verify {name}, each-alone. Their separately signed results happen to be identical.',f'Each of the {n} inspectors independently verifies {name}. Their separately signed results happen to be identical.','Do identical result values merge the distinct checking acts into one?',yes,1
    if family=='alternatives':
        a=f'For {name}, provide text or a chart, or-both.';e=f'For {name}, provide text, a chart, or both; at least one is required.'
        if v==0:
            suffix=' A separate binding rule prohibits charts. The plan provides text only.'
            return a+suffix,e+suffix,'Does the plan meet both requirements?',yes,0
        if v==1:
            suffix=' A separate binding rule prohibits charts. The plan provides nothing.'
            return a+suffix,e+suffix,'Does prohibiting charts make providing nothing permissible?',yes,1
        if v==2:
            a=f'In each of two rounds for {name}, choose text or chart, not-both.';e=f'In each of two rounds for {name}, choose exactly one of text and chart, not both.'
            suffix=' Round1 supplies text only; round2 supplies chart only.'
            return a+suffix,e+suffix,'Does each round satisfy its own choice requirement?',yes,0
        if v==3:
            suffix=' Independently, the transport must be local or remote, not-both.'
            esuffix=' Independently, exactly one of local and remote transport is required.'
            return a+suffix+' Plan: both report formats with local transport only.',e+esuffix+' Plan: both report formats with local transport only.','Does that plan satisfy both choice requirements?',yes,0
        if v==4:
            a=f'For {name}, provide text or chart, not-both.';e=f'For {name}, provide exactly one of text and chart, not both.'
            suffix=' The plan first provides text, then adds a chart to the same final submission; both remain present.'
            return a+suffix,e+suffix,'Does delivering the formats at different times make the final submission valid?',yes,1
        suffix=' A separate binding constraint requires a chart.'
        return a+suffix,e+suffix,'Which listed final submission meets every requirement?',['Text alone','A chart alone','Neither'],1
    if family=='update':
        common=f'Instruction ledger for {name}: active uncompleted clauses A=upload and B=checksum. References are unique; the sender is authorized; whole-clause updates commit in the stated order. '
        def event(ref,new,addition=False):
            return (f'{new}: {"supplements" if addition else "supersedes"}({ref}): perform {new}-task.',
                    f'{new}: '+(f'Keep {ref} active and add without precedence: perform {new}-task.' if addition else f'Retire every uncompleted obligation of active {ref} and replace its whole clause: perform {new}-task.'))
        if v in (0,1):
            c,ec=event('A','C',v==1);d,ed=event('C','D')
            return common+c+' Then '+d,common+ec+' Then '+ed,'Which clauses remain active after both commits?',['B and D','A, B and D','Only D'],int(v==1)
        if v==2:
            c,ec=event('A','C');d,ed=event('B','D',True)
            return common+c+' Then '+d,common+ec+' Then '+ed,'Does the separate B clause remain active after the addition?',['Yes','No','Neither update is valid'],0
        if v==3:
            common+='An identifier X ambiguously names two clauses. An unresolved reference makes the whole marked update invalid; its body is not an executable fallback. '
            c,ec=event('X','C')
            return common+c,common+ec,'Which operational plan follows?',['Keep A and B; ask to repair X','Drop both old clauses and perform C','Perform C anyway'],0
        if v==4:
            common=f'For {name}, active clause A has an already completed upload and an uncompleted checksum duty. The sender is authorized. An uploaded external file exists. '
            c,ec=event('A','C')
            return common+c,common+ec,'What does this update itself establish?',['Retire the remaining checksum duty; the uploaded file is not undone','Delete the uploaded file','Keep every uncompleted A duty'],0
        c,ec=event('A','C');d,ed=event('A','D')
        common+='Two update requests were sent but neither receipt nor commit order is available; do not assume send order is commit order. '
        return common+c+' '+d,common+ec+' '+ed,'Which replacement is known to be the current active one?',['C','D','Not determined from missing commit receipts'],2
    raise ValueError(family)

def composition():
    out=[]
    for context,included,finish,timing in itertools.product(TEST,[True,False],[False,True],range(3)):
        task=context+'-transfer';start=['08:58','08:58','09:02'][timing];end=['08:59','09:03','09:04'][timing]
        met=(timing==0 if finish else timing!=2)
        common=f'One group task {task}; you are directly addressed. All times refer to one UTC day. '
        log=f' Actual execution starts{start}Z; successful completion occurs{end}Z.'
        a=common+f'we-{ "including" if included else "excluding"}-you will perform the task {"complete-by" if finish else "start-by"}(09:00Z).'+log
        e=common+f'We, {"including" if included else "excluding"} you, will '+('successfully finish' if finish else 'begin actual execution of')+' the task no later than09:00Z.'+log
        values=['Included; deadline met','Included; deadline missed','Excluded; deadline met','Excluded; deadline missed'];gold=(0 if included else 2)+(0 if met else 1)
        frame=f'phase/{included}/{finish}/{timing}'
        out.append(row(f'{frame}/{context}','participants+deadline',frame,a,e,'Which joint state is correct?',values,gold,len(out),study='composition',included=included,finish=finish,timing=timing))
    for context,collective,inclusive,pick in itertools.product(TEST[:4],[False,True],[True,False],range(3)):
        n=4;acts=1 if collective else n;allowed=pick==1 or pick==2 and inclusive
        a=f'The {n} inspectors check {context}, {"as-one" if collective else "each-alone"}. Supply text or chart, {"or-both" if inclusive else "not-both"}.'
        e=(f'The {n} inspectors jointly perform one check of {context}.' if collective else f'Each of the {n} inspectors independently checks {context}.')+(' Supply text, chart, or both; at least one is required.' if inclusive else ' Supply exactly one of text and chart, not both.')
        log=' The final plan supplies '+['neither format.','text only.','both formats.'][pick]
        values=[f'{n} acts; submission valid',f'{n} acts; submission invalid','1 act; submission valid','1 act; submission invalid'];gold=(2 if collective else 0)+(0 if allowed else 1)
        frame=f'choice/{collective}/{inclusive}/{pick}'
        out.append(row(f'{frame}/{context}','multiplicity+alternatives',frame,a+log,e+log,'Which joint state is correct?',values,gold,len(out),study='composition',collective=collective,inclusive=inclusive,pick=pick))
    return out

def build():
    assert not (ROOT/'results').exists(), 'Never rebuild after exposure'
    train=[]
    for family in FAMILIES:
        seen=set()
        for context in TRAIN:
            for v in range(8):
                a,e,q,choices,gold,_=old.scenario(family,context,v,False)
                identity=(a,e,q,tuple(choices))
                if identity in seen:continue
                seen.add(identity)
                train.append(row(f'train/{family}/{context}/{v}',family,f'established/{family}/{v}',a,e,q,choices,gold,len(train)))
    test=[]
    for family,context,v in itertools.product(FAMILIES,TEST,range(6)):
        a,e,q,choices,gold=novel(family,context,v)
        test.append(row(f'novel/{family}/{v}/{context}',family,f'novel/{family}/{v}',a,e,q,choices,gold,len(test),study='retention'))
    tasks=[dict(case,id=case['id']+'/'+lang,case_id=case['id'],arm=lang,messages=messages(case,lang)) for case in test+composition() for lang in ['ainglish','english']]
    write_rows('curriculum.jsonl',train);write_rows('novel-reasoning.jsonl',test);write_rows('tasks.jsonl',tasks)
    for lang in ['ainglish','english']:
        write_rows('train-'+lang+'.jsonl',[{'id':r['id'],'messages':messages(r,lang)+[{'role':'assistant','content':r['answer']}]} for r in train])
    source=json.loads((PRIOR/'source-constructs.json').read_text());save('source-constructs.json',source)
    oldplan=json.loads((PRIOR/'PLAN.json').read_text())
    save('PLAN.json',{'kind':'ainglish.multi-seed-reasoning-transfer.v1','seed':17,'seeds':[17,29,43],
        'base_revision':oldplan['base_revision'],'training':oldplan['training'],
        'conditions':['base','ainglish-17','english-17','ainglish-29','english-29','ainglish-43','english-43'],
        'sources':{'register':source['source_url'],'source_mapping_sha256':digest(PRIOR/'source-constructs.json'),'training_grammar_sha256':digest(PRIOR/'build.py'),'trainer_sha256':digest(PRIOR/'run.py')},
        'scope':'Six ratified families only.336 distinct lexical training cases from established grammars;216 held-out cases from36 newly authored reasoning structures. They are synthetic single-author cases, not216 independent templates or a human study. Training domains and test domains are disjoint.',
        'primary':'For each seed, cold-A accuracy after A-training minus matched E-training on the new reasoning holdout; also English retention versus base. Report every family and seed, not the best seed.',
        'guards':{'family_point_floor_pp':-5,'overall_point_floor_pp':-5,'minimum_correct_controls':11,'control_items':12,'target_retries':0,'downloads':0,'physical_gpu':0,'host_disk_reserve_gib':10,'max_prompt_tokens':2048},
        'composition':'Full participant inclusion x deadline event x physically distinct start/finish traces; and multiplicity x disjunction x submitted choice. Separate marginal and joint accuracy; repeated domain variants cluster by authored frame.',
        'analysis':'Keep all outcomes including malformed and truncated outputs. 2,000 paired frame-cluster bootstrap draws at seed2026090633. Three training seeds are not three base-model families. Family point floors are screens, not proofs of non-inferiority. No governance or ratification effect.'})
    names=['build.py','audit.py','run.py','analyse.py','source-constructs.json','curriculum.jsonl','novel-reasoning.jsonl','tasks.jsonl','train-ainglish.jsonl','train-english.jsonl','PLAN.json']
    save('FROZEN.json',{name:digest(ROOT/name) for name in names})
    print(json.dumps({'train':len(train),'novel':len(test),'tasks_per_condition':len(tasks),'frames':len({r['frame'] for r in test})}))

if __name__=='__main__':build()
