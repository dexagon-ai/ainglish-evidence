"""Freeze new task-isolation diagnostics. No target calls or token counting."""
from collections import Counter, defaultdict
from fractions import Fraction
import hashlib
from itertools import product
import json
from pathlib import Path

from ainglish import panel

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
BASE = REPO / 'reader-and-web-followthrough-2026-09-08'
SNAPSHOT = Path('/home/dexagon/codex/ainglish-completion-20260909-94mYcbI5')

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f: json.dump(value,f,indent=2,ensure_ascii=False,allow_nan=False)

def freeze(name,target,items,scope,seed):
    p=json.loads((SNAPSHOT/(target+'.proposal.json')).read_text())
    readers=[];qualifications=[]
    for n in ['mistral','gemma']:
        q=json.loads((BASE/'qualification'/(n+'.result.json')).read_text())
        assert q['status']=='passed'
        readers.append(json.loads((BASE/'qualification'/(n+'.screen.json')).read_text())['reader'])
        qualifications.append(q['receipt'])
    panel.prepare_reader_instruments({'panel':readers})
    for r,q in zip(readers,qualifications):assert digest(panel.reader_receipt(r))==q['settings_sha256']
    n=len(items);strata=Counter(x['settlement_stratum'] for x in items)
    assert len({x['id'] for x in items})==n
    assert all(x['answer'] in x['options'] for x in items)
    baseline=max(Counter(x['answer'] for x in items).values())/n
    for i in range(12):
        names=['Iona','Juri','Kade','Lumi'];person=names[i%4]
        items.append({'id':name+'-control-'+str(i),'calibration':True,
                      'calibration_scope':'target-independent','calibration_construct':'resolved custody',
                      'english':f'Receipt FU-{7600+i}: the custodian is not identified.',
                      'ainglish':f'Receipt FU-{7600+i}: the custodian is {person}.',
                      'question':f'Who holds the parcel on receipt FU-{7600+i}?',
                      'options':names+['not determined'],'answer':person})
    spec={'public_id':p['public_id'],'slug':p['slug'],'construct':p['form'],
          'metric':'comprehension_accuracy_delta','study_purpose':'diagnostic','study_scope':scope,
          'comparator':{'kind':'complete-careful-english-task-isolation-v1',
                        'description':'Both arms receive identical world facts, question, options and any declared teaching or supplied calculation. Only the registered expression versus its explicit English mapping differs.'},
          'seed':seed,'panel':readers,'models':[q['roster_id'] for q in qualifications],
          'reader_qualifications':qualifications,'panel_neff':2,'planted_arm':'ainglish',
          'calibration_min_gap':0.5,'calibration_min_recovered':1,
          'items':items,'items_sha256':digest(items),
          'settlement_strata':[{'id':s,'weight':1} for s in strata],
          'attempt':{'estimand':scope,'admissibility_gates':[
              'Active unchanged target mapping and prediction; authenticated measurement admission and remaining budget checked before mint',
              'Publicly frozen complete items, golds, analysis and exact cached reader configurations before any target call',
              'Both existing exact qualification receipts remain valid and settings-matched; no new models or configuration substitutions',
              'GPU 0 isolated service only; physical Windows disk remains above 15 GiB; do not evict unrelated workloads',
              'Official mint before calibration and targets, passing calibration before targets, one call per planned cell with no retries',
              'Retain all null, adverse, absent and floor cells; these diagnostics do not replace previous primary criteria or constitute independent confirmation',
          ],'planned_sample':{'target_items':n,'calibration_items':12,'readers':2,'target_calls':2*n,'calibration_calls':48,'strata':dict(strata)}}}
    folder=ROOT/'readers'/name
    save(folder/'items.json',items);save(folder/'unbound-runspec.json',spec)
    save(folder/'claim-lock.json',{k+'_sha256':hashlib.sha256(p[k].encode()).hexdigest() for k in ['english_mapping','predicted_measurement']})
    save(folder/'design-audit.json',{'targets':n,'strata':dict(strata),'constant_answer_baseline':baseline,
                                    'items_sha256':digest(items),'target_calls_so_far':0})
    print(name,n,'targets frozen; no inference')

def attempt():
    items=[]
    domains=[('archive','archive record FX-801','record FX-801 is archived'),
             ('deliver','deliver parcel FX-802','parcel FX-802 has been delivered'),
             ('reserve','reserve berth FX-803','berth FX-803 is reserved'),
             ('copy','copy document FX-804','document FX-804 has been copied'),
             ('close','close ticket FX-805','ticket FX-805 is closed'),
             ('sign','sign receipt FX-806','receipt FX-806 is signed'),
             ('save','save draft FX-807','draft FX-807 is saved'),
             ('publish','publish bulletin FX-808','bulletin FX-808 is published')]
    cases={'failure-reported':(True,False,True),'success-reported':(True,True,True),
           'failure-unreported':(True,False,False),'success-unreported':(True,True,False),
           'no-effort-failure':(False,False,True),'no-effort-success':(False,True,True)}
    options=[f'Instruction discharged: {a}; outcome attained: {b}.' for a,b in product(['yes','no'],repeat=2)]
    for form,exposure,(domain,action,goal),(case,(effort,success,report)) in product(
            ['attempt','ensure'],['unintroduced','shared-definition'],domains,cases.items()):
        common='Fictional completed run. All relevant effort, outcome and reporting facts are stated. '
        if exposure=='shared-definition':
            common+='Shared glossary: attempt: requires an adequate effort and an honest report either way, not success. ensure: requires the outcome to hold at completion, not effort alone. Both English and tagged instructions follow those contracts. '
        english=(f'Try to {action}; make an adequate effort and report either way. Success is not required.' if form=='attempt'
                 else f'The instruction is satisfied exactly when {goal} at completion; a failed attempt alone is insufficient.')
        record=(' The worker made an adequate authorized effort.' if effort else ' The worker made no effort, although an adequate authorized attempt was available.')
        record+=(f' At completion, it is true that {goal}.' if success else f' At completion, it is false that {goal}.')
        record+=(' An honest report of the effort and outcome was sent.' if report else ' No report was sent.')
        record+=' No further action is authorized in this closed run. Outcome truth supplies no permission to act.'
        discharged=effort and report if form=='attempt' else success
        answer=f'Instruction discharged: {"yes" if discharged else "no"}; outcome attained: {"yes" if success else "no"}.'
        offset=len(items)%4
        items.append({'id':f'fx-{form}-{exposure}-{domain}-{case}','english':common+'Instruction: '+english+record,
                      'ainglish':common+f'Instruction: {form}: {action}.'+record,
                      'question':'Did the completed run discharge this instruction, and separately attain its requested outcome?',
                      'options':options[offset:]+options[:offset],'answer':answer,
                      'settlement_stratum':form+'-'+exposure,'form':form,'exposure':exposure,'domain':domain,'boundary':case,
                      'oracle':{'effort':effort,'outcome':success,'report':report,'discharged':discharged}})
    assert len(items)==192
    freeze('attempt-exposure','attempt',items,
           'Prospective 192-item task-isolation diagnostic: attempt/ensure x unintroduced tag/shared exact definition x eight domains x six effort/outcome/report cases. Complete careful-English instructions in both exposure conditions. Exact outcome-only ensure rule follows Rosetta public review 53f2c42e, not a rescoring of old data. Tests two-bit discharge/outcome interpretation, not authorized execution or a bare-instruction advantage. Two cached reader families; 384 target calls. Human intuition and future weight training are unmeasured.',2026090991)

def outcome():
    frames={
      'mean-outside':[(0,Fraction(1,2)),(6,Fraction(1,2))],
      'mode-below-half':[(0,Fraction(2,5)),(4,Fraction(3,10)),(10,Fraction(3,10))],
      'tied-modes':[(0,Fraction(2,5)),(6,Fraction(2,5)),(9,Fraction(1,5))],
      'mean-is-mode':[(0,Fraction(1,4)),(4,Fraction(1,2)),(8,Fraction(1,4))],
      'duplicate-paths':[(1,Fraction(1,4)),(1,Fraction(1,4)),(7,Fraction(1,3)),(10,Fraction(1,6))],
    }
    domains=['toy output','queue delay','retry count','resource use','simulated inventory','batch size']
    for supplied,format_ in product([False,True],['binary','four-bit']):
        items=[];name='outcome-'+('facts' if supplied else 'raw')+'-'+format_
        for domain_index,domain in enumerate(domains):
            for boundary,base in frames.items():
                paths=[(Fraction(x+13*domain_index+2),p) for x,p in base]
                masses=defaultdict(Fraction)
                for x,p in paths:masses[x]+=p
                assert sum(masses.values())==1
                mean=sum(x*p for x,p in masses.items())
                assert mean==sum(x*p for x,p in paths) # independent aggregated/path calculation
                modes=sorted(x for x,p in masses.items() if p==max(masses.values()))
                assert set(modes)=={x for x,p in masses.items() if all(p>=q for q in masses.values())}
                for form,true_claim in product(['mean-outcome','likeliest-outcome'],[True,False]):
                    if form=='mean-outcome':x=mean if true_claim else mean+1
                    elif true_claim:x=modes[domain_index%len(modes)]
                    else:x=next((v for v in sorted(masses) if v not in modes),min(masses)-1) if domain_index%2 else min(masses)-1
                    truth=(x==mean) if form=='mean-outcome' else x in modes
                    assert truth==true_claim
                    flags=[truth,x in masses,len(modes)==1 and x in modes, masses.get(x,0)==1]
                    ref=f'FI-{domain_index}-{boundary}'
                    common=('Shared definitions for this stateless question: mean-outcome(D) denotes the exact probability-weighted arithmetic mean; likeliest-outcome(D) denotes any value with maximal aggregated probability mass, with ties allowed. The same definitions govern the English expressions. '
                            +f'Fictional {domain} model {ref}, version v9, under its stated fixed conditioning, in units. Exact exhaustive mutually exclusive paths: '
                            +'; '.join(f'value {v} with probability {p}' for v,p in paths)+'. Sum masses for equal values. '
                            +f'The candidate x is {x} units. ')
                    if supplied:
                        common+=(f'Independently computed facts supplied for this question: exact weighted mean = {mean}; full set of modes = '+', '.join(map(str,modes))
                                 +'; full support = '+', '.join(map(str,sorted(masses)))+f'; probability of candidate x = {masses.get(x,Fraction(0))}. ')
                    english=(f'Under {ref}, the probability-weighted mean is {x} units.' if form=='mean-outcome'
                             else f'Under {ref}, {x} units has highest outcome probability, ties allowed.')
                    if format_=='binary':
                        options=['The statement is true under D.','The statement is false under D.']
                        answer=options[0 if truth else 1]
                        question='Is the statistic statement true under the exact declared distribution?'
                    else:
                        options=[f'Claim true: {a}; x possible: {b}; x unique most probable: {c}; next result guaranteed x under D: {d}.' for a,b,c,d in product(['yes','no'],repeat=4)]
                        answer='Claim true: {}; x possible: {}; x unique most probable: {}; next result guaranteed x under D: {}.'.format(*['yes' if f else 'no' for f in flags])
                        question='Under the exact declared model D, evaluate statement truth, possibility of x, whether x is the unique mode, and whether a trial from D equals x with probability one.'
                    offset=len(items)%len(options)
                    items.append({'id':name+f'-{domain_index}-{boundary}-{form}-{true_claim}',
                                  'english':common+'Statement: '+english,'ainglish':common+f'Statement: {x} units is {form}({ref}).',
                                  'question':question,'options':options[offset:]+options[:offset],'answer':answer,
                                  'settlement_stratum':form,'form':form,'domain':domain,'boundary':boundary,
                                  'supplied_facts':supplied,'response_format':format_,
                                  'world_id':f'{domain_index}-{boundary}-{form}-{true_claim}',
                                  'oracle':{'mean':str(mean),'modes':list(map(str,modes)),'x':str(x),
                                            'masses':{str(v):str(p) for v,p in masses.items()},'flags':flags}})
        assert len(items)==120 and sum(i['oracle']['flags'][0] for i in items)==60
        freeze(name,'outcome',items,
               'Prospective calculation/response-format isolation diagnostic: 120 fresh authored cases, 60 per predicate, six domains and five boundary frames, balanced true/false claims. '
               +('Exact verified mean/modes/support/candidate mass supplied equally to both arms. ' if supplied else 'Exact raw path distribution only; readers must derive its statistics. ')
               +('Binary statement-truth response. ' if format_=='binary' else 'Four-bit statement truth/possibility/unique mode/model-relative probability-one response. ')
               +'All four diagnostics share underlying worlds intentionally and are not independent replications. Definitions are shared in all conditions; neither cold reading nor changed model weights. No result replaces the earlier 240-item primary, guarantee semantics or noninferiority criteria. Two cached qualified families; 240 target calls.',
               2026090992+int(supplied)*2+int(format_=='four-bit'))

if __name__=='__main__':
    attempt();outcome()
