"""Deterministic semantic-review packets. No reader/tokenizer/API calls.

These are synthetic, parameterized design cases, not independent observations,
corpus samples, preregistrations, or certified official-panel instruments.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
YESNO=['Yes','No','Cannot tell from the supplied information']
STATES=['Rejection rule only','Materiality rule only','Both rules','Neither rule','Cannot determine both rules']
ORIGINS=['An explicit assignment','The fallback rule','Neither: resolution was rejected','Cannot determine provenance']


def canon(x): return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def sha(x): return hashlib.sha256(canon(x)).hexdigest()
def dump(name,x): (ROOT/name).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')


def row(ident, domain, family, form, context, marked, careful, bare, question, options, answer, bare_answer, record):
    # All visible context is in the actual arm string, never a hidden context field.
    prompt=lambda report: context+'\nReport: '+report
    desired_position=int(ident.rsplit('-',1)[-1])%len(options)
    order=(options.index(answer)-desired_position)%len(options)
    return {'id':ident,'world_id':ident,'template_id':family,'domain':domain,
            'form':form,'settlement_stratum':form, 'english':prompt(careful),
            'ainglish':prompt(marked),'bare':prompt(bare),'question':question,
            'options':options[order:]+options[:order],'answer':answer,
            'bare_answer':bare_answer,
            'record':record,'scope':'synthetic semantic-review case; not an executed study'}


def sequence_oracle(r):
    task=r['task']; members=r['admitted']; ordered=r['order_available']
    latest=ordered and r['candidate'] in members and r['candidate']==max(members)
    if task=='may_append':
        return YESNO[2] if r['closure']=='unknown' else YESNO[0 if r['closure'] in ('open','reopened') else 1]
    if task=='operative_closure': return YESNO[0 if r['closure']=='closed' and r['authority'] and r['closure_sequence']==r['sequence'] else 1]
    if task=='historical_invalidated': return YESNO[1]
    if task=='current_final': return YESNO[0 if r['closure']=='closed' and r['authority'] else 1]
    if task=='other_branch_invalidates': return YESNO[1]
    if task=='latest': return YESNO[2] if not ordered else YESNO[0 if latest else 1]
    if task=='safe': return YESNO[2]
    if task=='final_implies_latest': return YESNO[0]
    raise ValueError(task)


def latest_bank():
    domains=['software builds','policy drafts','transport services','episodes','invoices','model checkpoints','protocol versions','software builds']
    tasks=['may_append','may_append','may_append','operative_closure','operative_closure','historical_invalidated',
           'current_final','other_branch_invalidates','latest','latest','latest','latest','operative_closure','safe','safe','final_implies_latest']
    forms=['latest','latest','final','final','final','final','final','final','latest','latest','latest','latest','final','latest','latest','final']
    out=[]
    for d,domain in enumerate(domains):
        for k,task in enumerate(tasks):
            n=d*16+k; seq=f'{domain.replace(" ","-")}-S{d}'; x=20+d; time=f'2026-10-{d+1:02}T12:00Z'; c=f'C-{d}-{k}'
            r={'task':task,'sequence':seq,'candidate':x,'admitted':[x-1,x], 'order_available':True,
               'closure':'closed' if forms[k]=='final' else 'unknown','authority':True,'closure_sequence':seq}
            facts=f'Sequence {seq} orders admitted items by increasing integer rank. At {time}, its complete ledger admits ranks {x-1} and {x}. X denotes rank {x}. '
            form=forms[k]
            if k==0:
                facts+='No closure state is supplied.';q='Is it established that a new higher-ranked member can enter without changing a closure?'
                # Epistemic wording is intentionally not "is it established": unknown, not false.
                q='Can a higher-ranked member enter without changing any governing closure?'
            elif k==1:
                r['closure']='open';facts+='The governing record explicitly keeps this sequence open.';q='Can a higher-ranked member enter without changing any governing closure?'
            elif k==2:
                facts+=f'Authorised operative closure {c} makes X terminal at that time and has not been reopened.';q='Can a higher-ranked member enter this same sequence while that closure remains unchanged?'
            elif k in (3,4):
                r['closure']='planned' if k==3 else 'claimed';r['authority']=k==3
                facts+=f'{c} is '+('only a plan to close, not an operative act.' if k==3 else 'a closing announcement by an actor with no authority to close the sequence.')
                q='Does the supplied record establish operative closure of this sequence?'
            elif k==5:
                r['closure']='reopened';facts+=f'Authorised closure {c} made X terminal at {time}; a later authorised act reopened it. The report below is explicitly historical, anchored to the original closure.'
                q='Does the later reopening make that correctly anchored historical report false at its original point?'
            elif k==6:
                r['closure']='reopened';facts+=f'{c} originally closed this sequence but was explicitly superseded by reopening. The report below asserts present finality.';q='Is the report of present finality supported by the current governing record?'
            elif k==7:
                facts+=f'Authorised operative closure {c} makes X terminal. A separately identified successor {seq}-branch contains rank {x+1}, which is not a member of {seq}.';q='Does that successor item itself invalidate the original sequence closure?'
            elif k==8:
                facts+=f'Rank {x-1} was discovered later than X. Discovery time does not determine sequence rank.';q='Is X the admitted maximum at the named observation point?'
            elif k==9:
                r['admitted'].append(x+1);facts=f'Sequence {seq} uses increasing rank. The complete authoritative ledger at {time} admits ranks {x-1}, {x}, {x+1}; a stale local snapshot omits rank {x+1}. X is rank {x}.';q='Is X the admitted maximum at the named observation point?'
            elif k==10:
                facts+=f'Rank {x+1} exists only as an unadmitted draft.';q='Is X the admitted maximum at the named observation point?'
            elif k==11:
                r['order_available']=False;facts=f'{seq} identifies two incompatible order rules. No disambiguating order record is supplied. X and Y are members.';q='Can X be identified as the current maximum from these records?'
            elif k==12:
                r['closure_sequence']=seq+'-other';facts+=f'{c} is an authorised operative closure of {seq}-other only, not of {seq}.';q='Does the supplied closure establish operative closure of this sequence?'
            elif k==13:
                facts+='No quality or safety assessment is supplied.';q='Does the information establish that X is safe?'
            elif k==14:
                facts+='A later deployment replaced X. No safety assessment is supplied.';q='Does the information establish that X is safe?'
            else:
                facts+=f'Authorised operative closure {c} makes X terminal at that same point.';q='Was X also the admitted maximum at that closure point?'
            marked=f'X is latest-so-far({seq}, {time}).' if form=='latest' else f'X is final-in-sequence({seq}, {c}).'
            careful=f'X is the highest-ranked admitted member of {seq} at {time}.' if form=='latest' else f'Under closure {c}, X is the terminal admitted member of {seq}.'
            # Records here decide the questions; mark this ablation limitation openly.
            bare='X is last.'
            answer=sequence_oracle(r)
            out.append(row(f'latest-{n}',domain,f'latest-archetype-{k}',form,facts,marked,careful,bare,q,YESNO,answer,answer,r))
    return out


def statistical_oracle(r):
    rejects=r['decision_p']<r['alpha']
    practical=r['decision_effect']>=r['criterion_threshold']
    return STATES[2 if rejects and practical else 0 if rejects else 1 if practical else 3]


def statistical_bank():
    domains=['medicine','safety','A/B testing','model evaluation','manufacturing','public policy','finance','energy','education','service latency']
    families=['superiority','multiplicity-adjusted superiority','noninferiority','equivalence']
    out=[]
    for d,domain in enumerate(domains):
        for family_id,family in enumerate(families):
            for state in range(4):
                n=d*16+family_id*4+state; yes_s=state in (0,2);yes_p=state in (1,2)
                test=f'T-{d}-{family_id}';analysis=f'A-{d}-{family_id}-{state}';criterion=f'C-{d}-{family_id}';scope=f'S-{d}'
                p=.01 if yes_s else .20; threshold=10+d; effect=threshold+(2 if yes_p else -2)
                uncertain=family_id%2==1; direction='reduction' if d%2 else 'increase'
                r={'family':family,'decision_p':p,'alpha':.05,'decision_effect':effect,'criterion_threshold':threshold,
                   'criterion_uses':'lower confidence bound' if uncertain else 'point estimate',
                   'post_hoc':(d+family_id)%2==1,'scope':scope}
                context=(f'Domain: {domain}. {test} names a {family} test with rejection rule decision p < alpha; '
                    f'for equivalence, decision p is the larger of the two required one-sided p-values; '
                    f'for adjusted testing it is the specified adjusted p. Alpha is .05. {analysis} identifies the exact data and analysis version; '
                    f'it was chosen '+('after' if r['post_hoc'] else 'before')+' seeing results. '
                    f'{criterion} requires a {direction} of at least {threshold} units using the {r["criterion_uses"]} '
                    f'in scope {scope}. The following report is stipulated accurate about those named threshold decisions; '
                    'no methodological validity, causality, null probability, authority to act or desirability is supplied.')
                marked=(f'F '+('' if yes_s else 'not ')+f'stat-significant(test={test}, alpha=.05, analysis={analysis}); '
                    'F '+('' if yes_p else 'not ')+f'practically-important(criterion={criterion}, scope={scope}).')
                careful=(f'Under {analysis}, F '+('meets' if yes_s else 'does not meet')+f' {test}\'s rejection rule at .05; '
                    f'in {scope}, F '+('meets' if yes_p else 'does not meet')+f' materiality criterion {criterion}.')
                answer=statistical_oracle(r)
                # Same visible baseline never receives a hidden-state-specific key.
                bare='F: significance discussed.'
                out.append(row(f'stat-{n}',domain,f'stat-{family_id}', 'statistical-and-practical',context,marked,careful,bare,
                    'Which of the two named threshold rules are met?',STATES,answer,STATES[4],r))
    return out


def resolve(r):
    if not r['trace_available']: return ORIGINS[3],None
    candidates=[a for a in r['assignments'] if a['applicable']]
    if candidates:
        winner=max(candidates,key=lambda a:a['priority'])
        if winner['value'] is None:
            if r['null_rule']=='reject': return ORIGINS[2],None
            if r['null_rule']=='absent': return ORIGINS[1],r['fallback']
        return ORIGINS[0],winner['value']
    return ORIGINS[1],r['fallback']


def assignment_bank():
    domains=['command-line flags','environment variables','configuration files','API optional fields','database defaults',
             'CSS-like inheritance','model parameters','deployment profiles','organisation policy','schedulers','user preferences','command-line flags']
    out=[]
    for d,domain in enumerate(domains):
        for k in range(14):
            n=d*14+k;value=30+d;key=f'run-{d}/boundary-{k}/timeout';rule=f'fallback-{d}-{k}'
            assignments=[] if k in (1,6,9,12,13) else [{'id':f'run-{d}/retained-input/field-{k}','value':value,'priority':1,'applicable':True,'writer':'human' if k%2 else 'generated'}]
            r={'assignments':assignments,'fallback':value if k in (0,1,4,5) else value+10,
               'null_rule':'present','trace_available':k!=10,'materialised':k in (0,1,9), 'key':key}
            if k in (3,4,5): assignments[0]['value']=None;r['null_rule']={3:'absent',4:'present',5:'reject'}[k]
            if k==6: assignments.append({'id':f'run-{d}/retained-input/unrelated','value':value,'priority':9,'applicable':False,'writer':'human'})
            if k==7: assignments.append({'id':f'run-{d}/argv/second-flag','value':value+2,'priority':2,'applicable':True,'writer':'generated'})
            if k==8: assignments[0]['id']=f'run-{d}/environment/TIMEOUT'
            if k==11: assignments[0]['value']=value+10
            if k==13: assignments.append({'id':f'run-{d}/documentation/example','value':value,'priority':1,'applicable':False,'writer':'documentation'})
            answer,effective=resolve(r)
            form='assignment' if answer==ORIGINS[0] else 'default' if answer==ORIGINS[1] else 'boundary'
            trace={'key':key,'fallback_ref':rule,'fallback_value':r['fallback'],'null_rule':r['null_rule'],
                   'assignments':assignments if r['trace_available'] else 'not retained',
                   'precedence':'highest priority applicable assignment wins; null applies the named null rule',
                   'future_policy':'retain this materialised value' if r['materialised'] else 'not specified'}
            context=f'Domain: {domain}. Complete record for the named resolution boundary: '+json.dumps(trace,sort_keys=True)+'. '
            if k==9:context+='An outer boundary explicitly selected this profile; that does not supply an assignment at the inner timeout boundary. '
            if k==10:context+='The rule reference resolves, but the actual input trace is unavailable. Do not guess how the observed value was obtained. '
            if k==12:context+='The optional field was omitted from the retained request; the named fallback is evaluated now. '
            if k==13:context+='An example in documentation mentions a value but is not an input to this resolution. '
            if answer==ORIGINS[0]:
                source=max([a for a in assignments if a['applicable']],key=lambda a:a['priority'])['id']
                marked=f'{key} resolved-by-assignment({json.dumps(effective)}, source={source}).'
                careful=f'At {key}, assignment {source} supplied effective value {json.dumps(effective)}.'
            elif answer==ORIGINS[1]:
                marked=f'{key} resolved-by-default({effective}, rule={rule}).'
                careful=f'At {key}, no applicable assignment supplied a value; fallback rule {rule} supplied {effective}.'
            else:
                marked=careful=f'No supported provenance marker is supplied for {key}.'
            bare=f'{key} = {json.dumps(effective) if effective is not None else "unreported"}.'
            out.append(row(f'assignment-{n}',domain,f'assignment-archetype-{k}',form,context,marked,careful,bare,
                           'Which provenance class does this boundary record support?',ORIGINS,answer,answer,r))
    return out


def supplemental_checks():
    # Concrete semantic regression expectations, not scored target observations.
    return [
        {'id':'S-null-probability','input':'F stat-significant(T,.05,A). No prior probability is supplied.','question':'Is P(null true)=.05 established?','answer':'No'},
        {'id':'S-fixed-mean-bound-change','input':'C requires lower bound >=10. Estimate stays 12; lower bound changes from 8 to 11.','question':'Does satisfaction of C change?','answer':'Yes'},
        {'id':'S-fixed-mean-point-only','input':'C requires estimate >=10. Estimate remains 12; only interval width changes.','question':'Does satisfaction of C change from that alone?','answer':'No'},
        {'id':'S-alpha-boundary','input':'T requires p<.05, p=.05.','question':'Does T reject?','answer':'No'},
        {'id':'S-adjustment','input':'T uses adjusted p<.05. Raw p=.01; adjusted p=.08.','question':'Does T reject?','answer':'No'},
        {'id':'S-posthoc','input':'A was chosen after results; its named rule rejects.','question':'Does the threshold decision establish preregistration?','answer':'No'},
        {'id':'S-wrong-scope','input':'C is defined only for population P. Finding is solely from Q; no transport rule.','question':'Is satisfaction of C in P established?','answer':'No'},
        {'id':'S-missing-analysis','input':'Analysis A cannot be resolved.','question':'Can its threshold classification be recovered?','answer':'Clarification required'},
        {'id':'A-materialised-default','input':'Fallback R supplies 40 at t1. The value is copied and never re-resolved. R later becomes 50.','question':'Does the retained value change to 50?','answer':'No'},
        {'id':'A-dynamic-assignment','input':'Assignment A supplies 40; resolver re-runs whenever A changes. A becomes 50.','question':'Does the next resolution change to 50?','answer':'Yes'},
        {'id':'A-equal-default','input':'Assignment A=40 overrides fallback R=40. Remove A and resolve again.','question':'Can provenance change without value changing?','answer':'Yes'},
        {'id':'A-edit-not-unique','input':'A=40 overrides R=50; next resolution reads both. Editing A or removing it can change the value.','question':'Is there one uniquely necessary edit?','answer':'No'},
        {'id':'A-reference-wrong','input':'Trace records assignment A supplied K. Reference B resolves to a different key.','question':'Does citing B correctly identify K provenance?','answer':'No'},
        {'id':'A-machine-explicit','input':'A generated configuration field is applicable and wins precedence.','question':'Must its writer have been human?','answer':'No'},
        {'id':'L-anchor','input':'Finality at t1 is true; closure reopens at t2.','question':'Does historical finality establish current finality?','answer':'No'},
        {'id':'L-unknown-not-open','input':'Latest-so-far(S,t); no closure information.','question':'Is openness established?','answer':'No'}]


def verify(banks):
    assert {name:len(rows) for name,rows in banks.items()}=={'latest':128,'stat':160,'assignment':168}
    assert len({r['id'] for rows in banks.values() for r in rows})==456
    for name,rows in banks.items():
        f={'latest':sequence_oracle,'stat':statistical_oracle,'assignment':lambda r:resolve(r)[0]}[name]
        by_visible={}
        for r in rows:
            assert r['answer']==f(r['record']) and r['answer'] in r['options'] and r['bare_answer'] in r['options']
            for arm in ('english','ainglish','bare'):
                key=(r[arm],r['question'],tuple(r['options']))
                answer=r['bare_answer'] if arm=='bare' else r['answer']
                assert by_visible.setdefault(key,answer)==answer
    # Independent hand-checked semantic expectations per archetype and state.
    assert [r['answer'] for r in banks['latest'][:16]]==[YESNO[i] for i in (2,0,1,1,1,1,1,1,0,1,0,2,1,2,2,0)]
    assert [r['answer'] for r in banks['assignment'][:14]]==[ORIGINS[i] for i in (0,1,0,1,0,2,1,0,0,1,3,0,1,1)]
    for d in range(10):
        for family in range(4): assert [r['answer'] for r in banks['stat'][d*16+family*4:d*16+family*4+4]]==STATES[:4]
    # Provenance and mutations are different questions; equal fallback is explicit.
    r=dict(banks['assignment'][0]['record']);assert resolve(r)==(ORIGINS[0],30)
    assert resolve(dict(r,assignments=[]))==(ORIGINS[1],30)
    # Per-form strata are not silently inflated with boundary/nonclaim diagnostics.
    assert Counter(r['form'] for r in banks['latest'])=={'latest':64,'final':64}
    assert Counter(r['form'] for r in banks['assignment'])=={'assignment':72,'default':72,'boundary':24}


def build():
    banks={'latest':latest_bank(),'stat':statistical_bank(),'assignment':assignment_bank()};verify(banks)
    outputs={}
    for name,rows in banks.items():
        dump(name+'.review-bank.json',rows)
        panel_rows=[{k:r[k] for k in ('id','world_id','template_id','domain','form','settlement_stratum','english','ainglish','question','options','answer')} for r in rows]
        dump(name+'.careful-panel-draft.json',panel_rows)
        declarations={'kind':'ainglish.study-declarations.v1','expected_target_rows':len(rows),'expected_control_rows':0,
            'counts':{field:dict(Counter(r[field] for r in rows)) for field in ('domain','form','template_id')}}
        dump(name+'.declarations.json',declarations)
        outputs[name]={'rows':len(rows),'template_families':len({r['template_id'] for r in rows}),
            'review_bank_sha256':sha(rows),'careful_items_sha256':sha(panel_rows),
            'forms':dict(Counter(r['form'] for r in rows)),
            'bare_differs_in_gold':sum(r['answer']!=r['bare_answer'] for r in rows),
            'study_status':'review draft; no launch approval, final scientific freeze, qualification, attempt or inference'}
    dump('semantic-checks.json',supplemental_checks())
    report={'kind':'three-candidate-preparation.v1','cases':outputs,'supplemental_semantic_checks':len(supplemental_checks()),
        'reader_calls':0,'tokenizer_calls':0,'independently_sampled_worlds':0,
        'interpretation':'456 labelled parameterized design worlds, not 456 independently sampled observations. Context alone answers latest/assignment core questions; useful semantic checks, not a demonstrated language-effect instrument.'}
    dump('candidate-manifest.json',report);print(json.dumps(report))


if __name__=='__main__':build()
