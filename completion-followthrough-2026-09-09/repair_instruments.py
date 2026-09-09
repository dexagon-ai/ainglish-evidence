"""Prepare unrun prospective review packets; no tokenizers, readers or writes to Ainglish."""
from collections import Counter, defaultdict
from fractions import Fraction as F
import copy
import hashlib
import json
from pathlib import Path
from ainglish.experiment_audit import audit_items

ROOT=Path(__file__).resolve().parent
PRIOR=ROOT.parent/'completion-measurements-2026-09-09'

def digest(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:json.dump(obj,f,indent=2,ensure_ascii=False)

def position_report(rows):
    real=[r for r in rows if not r.get('calibration')]
    groups=defaultdict(list)
    for r in real:
        groups['all'].append(r)
        for k in ['form','domain','consequence_family','block']:
            if k in r.get('strata',{}):groups[k+'='+str(r['strata'][k])].append(r)
        if 'form' in r.get('strata',{}) and 'domain' in r['strata']:
            groups['form-domain='+r['strata']['form']+'/'+r['strata']['domain']].append(r)
    result={}
    for k,rs in groups.items():
        words=Counter(r['answer'] for r in rs)
        pos=Counter(r['options'].index(r['answer']) for r in rs)
        result[k]={'n':len(rs),'answer_counts':dict(words),'position_counts':dict(pos),
            'constant_answer_baseline':max(words.values())/len(rs),
            'constant_position_baseline':max(pos.values())/len(rs)}
    return result

def controls(prefix):
    destinations=['Alder','Birch','Cedar','Dahlia','Elm','Fir','Gorse','Hazel']
    out=[]
    for i,dest in enumerate(destinations):
        iid=prefix+'-'+str(i);symbol='vok'+str(41+i)
        options=destinations+['Not specified by this message']
        rotation=(2*i)%len(options)
        options=options[rotation:]+options[:rotation]
        out.append({'id':iid,'calibration':True,'calibration_scope':'target-independent',
            'calibration_construct':'novel-parcel-routing-dictionary',
            'english':f'Parcel {iid} is assigned symbol {symbol}. Its destination can be any of the listed locations. The routing dictionary is unavailable and no destination has been specified in this message.',
            'ainglish':f'The routing dictionary maps symbol {symbol} to {dest}. Parcel {iid} is assigned symbol {symbol}.',
            'question':f'Which destination, if any, is specified for parcel {iid} by this message?',
            'options':options,'answer':dest,
            'control_interpretation':{'english_correct_response':'Not specified by this message',
                'ainglish_correct_response':dest,
                'scoring':'Official calibration scores the planted destination; the cold arm has a truthful selectable not-specified response. This control intentionally changes information and is not a language comparison.'}})
    assert max(Counter(r['options'].index(r['answer']) for r in out).values())==1
    assert all(r['control_interpretation']['english_correct_response'] in r['options'] for r in out)
    return out

def rent():
    old=json.loads((PRIOR/'rent-learnability/items.json').read_text())
    rows=[copy.deepcopy(r) for r in old if not r.get('calibration')]
    assert len(rows)==64
    # No target was exposed in c2277818: retain its frozen 64 targets exactly,
    # replacing only the prospectively reviewed, demonstrably unanswerable controls.
    rows+=controls('rent-control-v2')
    save(ROOT/'rent-v2/items.json',rows)
    save(ROOT/'rent-v2/audit.json',audit_items(rows))
    save(ROOT/'rent-v2/positions.json',position_report(rows))
    save(ROOT/'rent-v2/status.json',{'status':'awaiting independent control review; unrun',
        'items_sha256':digest(rows),'target_items_sha256':digest(rows[:64]),
        'replaces_aborted_attempt':'c2277818-fdef-4170-a4cf-68c54e5fa6c6',
        'preserved_target_count':64,'new_controls':8,'target_calls':0,'attempts_minted':0,
        'change':'Each cold control now offers a truthful not-specified option. Do not label abstention from an underdetermined forced choice a learnability failure.',
        'hold':'Independent control review, official runspec/preflight/qualified-reader binding, resource gate and replication capability before mint.'})

def resume():
    rows=[];ledger=[]
    domains=[('reading','Read the manual','chapters'),('review','Review the checklist','checks'),
             ('media','Play the recording','segments'),('simulation','Perform the simulated workflow','steps')]
    for di,(domain,action,units) in enumerate(domains):
        for pi,policy in enumerate(['resume','redo']):
            for k in range(8):
                iid='Q-'+hashlib.sha256(f'resume-v2-{di}-{pi}-{k}'.encode()).hexdigest()[:10]
                cp='CP-'+hashlib.sha256(iid.encode()).hexdigest()[:8]
                names=['umber','mauve','ochre','silver'];progress=k//2
                done=names[:progress];target=names[0]
                performed=(policy=='redo' or target not in done)
                rule_performed=k%2==0
                yes=performed==rule_performed
                gold='Yes' if yes else 'No'
                # Balance response positions separately from truth and policy.
                correct_position=(k//2)%2
                options=[gold,'No' if yes else 'Yes'] if correct_position==0 else ['No' if yes else 'Yes',gold]
                common=(f'Fictional task {iid}, edition 4, has four {units} in order: '+', '.join(names)+'. '
                    f'The saved record {cp} belongs to this exact task and edition. '
                    + ('It records no completed unit. ' if not done else 'It records these completed units: '+', '.join(done)+'. ')
                    +f'The next unfinished unit is {names[progress]}. Earlier work was performed by '+['Neri','Olan'][k%2]+'. '
                    f'A lamp lights exactly when {target} is '+('performed' if rule_performed else 'left unperformed')+' during the forthcoming pass. '
                    'This is an authorised simulation; repeat execution is permitted and has no external effect. ')
                english=(f'{action} for {iid}, continuing from checkpoint {cp}.' if policy=='resume' else f'{action} for {iid} again from the beginning.')
                marked=f'{action} for {iid}, '+(f'resume-from({cp}).' if policy=='resume' else 'redo-from-start.')
                r={'id':iid,'english':common+english,'ainglish':common+marked,
                    'question':'Should the lamp light during the forthcoming pass?',
                    'options':options,'answer':gold,'settlement_stratum':policy+'-core',
                    'strata':{'form':policy,'domain':domain,'block':'core','progress':progress,'lamp_condition':'performed' if rule_performed else 'unperformed'}}
                rows.append(r);ledger.append({'id':iid,'completed':done,'new_pass_contains_target':performed,'lamp_if_performed':rule_performed,'gold':gold})
    core_count=len(rows)
    # Separately scored explicit boundary rules, balanced within each policy.
    cases=[('matching-record',True,'The required checkpoint is present and matches this exact task and edition.'),
           ('missing-record',False,'The required checkpoint record is missing.'),
           ('matching-edition',True,'The checkpoint names this task and its current edition.'),
           ('wrong-edition',False,'The checkpoint names an older edition, not this task edition.'),
           ('authorised',True,'The actor has current permission for this simulated pass.'),
           ('unauthorised',False,'The actor has no current permission for this pass.'),
           ('repeat-permitted',True,'The repeated steps are expressly permitted and have no outside effects.'),
           ('repeat-forbidden',False,'Repeating the steps would violate an explicit safety restriction.')]
    for pi,policy in enumerate(['resume','redo']):
        for ci,(case,allowed,fact) in enumerate(cases):
            if policy=='redo' and ci<4:
                case,allowed,fact=[
                    ('defined-task',True,'The task definition identifies exactly which work is required.'),
                    ('undefined-task',False,'No task definition is available, so the required work is unknown.'),
                    ('defined-start',True,'The task has a determinate starting point.'),
                    ('undefined-start',False,'The instruction does not identify a starting point, and no task convention supplies one.'),
                ][ci]
            for variant in range(2):
                iid='B-'+hashlib.sha256(f'resume-boundary-v2-{pi}-{ci}-{variant}'.encode()).hexdigest()[:10]
                common=(f'Simulated task {iid}. Execution requires a defined task with a determinate starting point, current authorisation and safe permission for required repeated steps. Continuing from a checkpoint additionally requires a saved completed-work/next-work record for this exact task and edition; starting again does not require a checkpoint. '
                    'All requirements not mentioned next are satisfied. '+fact+' ')
                gold='Yes' if allowed else 'No'
                options=[gold,'No' if allowed else 'Yes'] if variant==0 else ['No' if allowed else 'Yes',gold]
                english='Perform the task, continuing from checkpoint CP-B.' if policy=='resume' else 'Perform the task again from the beginning.'
                marked='Perform the task, '+('resume-from(CP-B).' if policy=='resume' else 'redo-from-start.')
                rows.append({'id':iid,'english':common+english,'ainglish':common+marked,
                    'question':'May this task proceed under the stated admission rule as things stand?',
                    'options':options,'answer':gold,'settlement_stratum':'boundary',
                    'boundary_case':True,'strata':{'form':policy,'domain':'shared-admission-rule','block':'boundary','case':case}})
                ledger.append({'id':iid,'shared_admission_all_conditions_met':allowed,'gold':gold})
    assert core_count==64 and len(rows)==96
    report=position_report(rows)
    assert all(v['constant_answer_baseline']==.5 and v['constant_position_baseline']==.5 for v in report.values())
    # IDs are opaque; the policy is visible only where it belongs, in the instruction.
    assert all('resume' not in r['id'] and 'redo' not in r['id'] for r in rows)
    prior=json.loads((PRIOR/'resume-comprehension/items.json').read_text())
    assert not ({(r['english'],r['ainglish']) for r in rows}&{(r['english'],r['ainglish']) for r in prior})
    save(ROOT/'resume-v2/careful-items.json',rows)
    learning=copy.deepcopy(rows)
    for r in learning:r['english']=r['ainglish']
    save(ROOT/'resume-v2/learning-items.json',learning)
    save(ROOT/'resume-v2/gold-ledger.json',ledger)
    save(ROOT/'resume-v2/positions.json',report)
    save(ROOT/'resume-v2/audit.json',audit_items(rows,require_balanced=True))
    save(ROOT/'resume-v2/status.json',{'status':'awaiting author semantic and boundary-scope review; unrun',
        'careful_items_sha256':digest(rows),'learning_items_sha256':digest(learning),
        'core':64,'boundary':32,'target_calls':0,'attempts_minted':0,
        'prior_original_retained':'a9d3a18007710d8701f083efe1db268c15f1aefddba53296e3e63e844838c4ec',
        'scope':'New prospective designs, not an exact replication or replacement of the prior neutral outcome. Canonical concise comparators. Boundary block covers missing/mismatched checkpoints for resume, missing task/start for redo, and authorisation/safe repetition for both; it is not a full force-context assessment.',
        'hold':'Author acceptance, separate matched claim/exposure/calibration/reader binding and independent replication route before any inference.'})

def outcome():
    families={
        'weighted-mean':('the probability-weighted average equals {x}',lambda d,x:sum(v*p for v,p in d)==x),
        'affine-average':('after every output v is converted to 2v+3, the probability-weighted average equals {y}',lambda d,x:sum((2*v+3)*p for v,p in d)==2*x+3),
        'possible-value':('the value {x} can occur on one draw',lambda d,x:any(v==x and p>0 for v,p in d)),
        'maximal-mass':('no other single output value has greater probability than {x}',lambda d,x:dict(d).get(x,F(0))>=max(p for v,p in d)),
    }
    rows=[];ledger=[]
    for pi,form in enumerate(['mean-outcome','likeliest-outcome']):
        for fi,(family,(template,prop)) in enumerate(families.items()):
            for k,x in enumerate(range(31,39)):
                known=family in (['weighted-mean','affine-average'] if pi==0 else ['possible-value','maximal-mass'])
                distributions=[[(x,F(1))],[(x-2,F(1,2)),(x+2,F(1,2))],
                    [(x-2,F(1,3)),(x+1,F(2,3))],[(x,F(3,5)),(x+5,F(2,5))]]
                valid=[d for d in distributions if (families['weighted-mean'][1](d,x) if pi==0 else families['possible-value'][1](d,x) and families['maximal-mass'][1](d,x))]
                witness=next(d for d in valid if prop(d,x))
                counter=next((d for d in valid if not prop(d,x)),None)
                assert (counter is None)==known
                iid='O-'+hashlib.sha256(f'outcome-v2-{pi}-{fi}-{k}'.encode()).hexdigest()[:10]
                common=(f'Distribution {iid} is a fixed finite distribution of toy numeric outputs under a named mathematical model. '
                    'The full table is retained by the writer but not shown here. The assertion is truthful relative to that table, not a guarantee about the real world. '
                    'A mean is the probability-weighted average; a likeliest value is a supported output of maximal probability, with ties allowed. ')
                english=(f'For {iid}, the probability-weighted mean is {x}.' if pi==0 else f'For {iid}, {x} has maximal output probability, ties allowed.')
                gold='Yes' if known else 'No'; options=['Yes','No'] if k%2==0 else ['No','Yes']
                rows.append({'id':iid,'english':common+english,'ainglish':common+f'{x} is {form}({iid}).',
                    'question':'Does the assertion alone guarantee that '+template.format(x=x,y=2*x+3)+'?',
                    'options':options,'answer':gold,'strata':{'form':form,'consequence_family':family,'block':'summary-only'},
                    'independent_semantic_cluster':family})
                encode=lambda d:[{'value':v,'probability':str(p)} for v,p in d]
                ledger.append({'id':iid,'entailed':known,'witness':encode(witness),
                    'counterexample':None if counter is None else encode(counter),
                    'proof':'Definition and linearity' if known else 'Truthful asserted statistic plus a counterexample falsifies entailment.'})
    assert len(rows)==64
    report=position_report(rows)
    assert all(v['constant_answer_baseline']==.5 and v['constant_position_baseline']==.5 for v in report.values())
    questions=defaultdict(list)
    for r in rows:questions[(r['question'],tuple(r['options']))].append(r)
    assert all(Counter(r['answer'] for r in rs)=={'Yes':1,'No':1} for rs in questions.values())
    save(ROOT/'outcome-v2/items.json',rows);save(ROOT/'outcome-v2/rational-ledger.json',ledger)
    save(ROOT/'outcome-v2/positions.json',report);save(ROOT/'outcome-v2/audit.json',audit_items(rows,require_balanced=True))
    save(ROOT/'outcome-v2/status.json',{'status':'new narrow diagnostic awaiting author review; unrun',
        'items_sha256':digest(rows),'target_calls':0,'attempts_minted':0,'semantic_families':4,
        'exact_question_and_options_only_majority_baseline':.5,
        'change':'Remove logically uninformative consequence families and reversed question wording; every exact question/options tuple has opposite golds across the two forms.',
        'limits':'This intentionally narrows to four distinguishing entailments, not the existing full prediction. Sixty-four renderings do not equal 64 independent semantic cases. Masked-label views cannot retain original golds as if fully informed.',
        'hold':'Author acceptance of scope and golds, independent review, frozen official runspec/readers/resources/replication capacity before inference.'})

if __name__=='__main__':
    rent();resume();outcome()
    print('Prepared rent controls, 96 resume items in two unrun exposure designs, and 64 narrow outcome items. Zero inference/mints.')
