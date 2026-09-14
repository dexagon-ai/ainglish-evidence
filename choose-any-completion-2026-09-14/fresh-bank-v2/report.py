"""Prospective report helpers. No network, model calls or Ainglish writes."""
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parent

def binom_cdf(k, n, probability):
    if k < 0: return 0.0
    if k >= n: return 1.0
    return sum(math.comb(n,j)*probability**j*(1-probability)**(n-j) for j in range(k+1))

def cp_upper(k, n, alpha=.05):
    if not 0 < alpha < 1 or not 0 <= k <= n: raise ValueError('Invalid binomial arguments')
    if not n: return None
    if k == n: return 1.0
    lo, hi = 0., 1.
    for _ in range(70):
        mid = (lo+hi)/2
        if binom_cdf(k,n,mid) > alpha: lo=mid
        else: hi=mid
    return (lo+hi)/2

def cp_lower(k, n, alpha=.05):
    if not n: return None
    return 1-cp_upper(n-k,n,alpha)

def interval(k,n):
    return [cp_lower(k,n,.025),cp_upper(k,n,.025)]

def conditional_ni(counts):
    """counts={reader: {arm: {'correct':k, 'live':n}}}; no pooling of binomial trials."""
    readers=sorted(counts)
    alpha=.05/(2*len(readers))
    if any(not counts[r].get(a,{}).get('live',0) for r in readers for a in ['ainglish','english']):
        return {'status':'unavailable_missing_reader_arm'}
    totals={a:sum(counts[r][a]['live'] for r in readers) for a in ['ainglish','english']}
    components={}
    lower=0
    for r in readers:
        ar,er=counts[r]['ainglish'],counts[r]['english']
        la=cp_lower(ar['correct'],ar['live'],alpha)
        ue=cp_upper(er['correct'],er['live'],alpha)
        lower += ar['live']/totals['ainglish']*la-er['live']/totals['english']*ue
        components[r]={'ainglish_lower':la,'english_upper':ue,'individual_lower_delta_pp':100*(la-ue)}
    return {'status':'conditional_binomial_world_model','tail_per_component':alpha,
            'lower_delta_pp':100*lower,'passes_minus_5pp':lower>-.05,'components':components}

def planned_boundary(plan):
    counts=defaultdict(lambda:defaultdict(lambda:defaultdict(lambda:{'correct':0,'live':0})))
    opp=Counter()
    for cell in plan:
        form,r,a=cell['form'],cell['reader'],cell['arm']
        counts[form][r][a]['live']+=1
        counts[form][r][a]['correct']+=1
        for kind in cell['offered_contrasts']:
            opp[(form,r,a,kind)]+=1
    return {'status':'PLANNING_ONLY_NO_TARGET_RESPONSES',
            'even_if_every_target_answer_were_correct':{f:conditional_ni(rows) for f,rows in counts.items()},
            'zero_error_opportunity_upper_95':[
                {'form':f,'reader':r,'arm':a,'contrast':k,'planned_worlds':n,
                 'zero_errors_upper':cp_upper(0,n)} for (f,r,a,k),n in sorted(opp.items())],
            'target_calls':len(plan),'target_reader_calls_observed':0}

def contrast(rows):
    cells=defaultdict(lambda:defaultdict(lambda:[0,0]))
    for row in rows:
        if row.get('absent'): continue
        cell=cells[row['form']][row['arm']]
        cell[0]+=int(row['joint']);cell[1]+=1
    if set(cells) != {'choose-any','draw-uniform'}: return None
    differences=[]
    for form in cells:
        if any(not cells[form][arm][1] for arm in ['ainglish','english']): return None
        differences.append(sum(sign*cells[form][a][0]/cells[form][a][1]
                               for a,sign in [('ainglish',1),('english',-1)]))
    return 100*sum(differences)/2

def correlation_sensitivity(rows, draws=20000, seed=2026091463):
    worlds=defaultdict(list)
    for row in rows: worlds[row['world_id']].append(row)
    strata=defaultdict(list); frames=defaultdict(list)
    for wid,group in worlds.items():
        strata[(group[0]['form'],group[0]['domain'])].append(wid)
        frames[group[0]['frame_family']].extend(group)
    def summary(values,undefined):
        values.sort()
        return {'accepted_draws':len(values),'undefined_draws':undefined,
                'percentile_95':([values[int(.025*len(values))],values[int(.975*len(values))]] if values else None),
                'not_a_noninferiority_certificate':True}
    result={}
    for method in ['world_within_form_domain','frame_family']:
        rng=random.Random(f'{seed}:{method}'); values=[]; undefined=0
        for _ in range(draws):
            if method=='world_within_form_domain':
                sample=[r for ids in strata.values() for wid in rng.choices(ids,k=len(ids)) for r in worlds[wid]]
            else:
                sample=[r for frame in rng.choices(sorted(frames),k=len(frames)) for r in frames[frame]]
            value=contrast(sample)
            if value is None: undefined+=1
            else: values.append(value)
        result[method]=summary(values,undefined)
    result['leave_one_frame_out']={f:contrast([r for r in rows if r['frame_family']!=f]) for f in sorted(frames)}
    return result

def selftest():
    for n in [1,2,8,18,36,72,144]:
        assert abs(cp_upper(0,n)-(1-.05**(1/n)))<1e-12
        assert abs(cp_lower(n,n)-.05**(1/n))<1e-12
        assert cp_lower(0,n)==0
        assert cp_upper(n,n)==1
    assert interval(0,0)==[None,None]
    # NIST's 4/20, two-sided 90% interval example.
    assert abs(cp_lower(4,20,.05)-.071354)<1e-6
    assert abs(cp_upper(4,20,.05)-.401029)<1e-6
    counts={r:{a:{'correct':36,'live':36} for a in ['english','ainglish']} for r in ['A','B']}
    assert conditional_ni(counts)['passes_minus_5pp'] is False
    assert conditional_ni({'A':{'english':{'correct':1,'live':1}}})['status']=='unavailable_missing_reader_arm'
    return {'status':'FILE_ONLY_STATISTICAL_HELPER_TESTS_PASS','target_reader_calls':0}

if __name__=='__main__':
    print(json.dumps(selftest()))
    path=ROOT/'planned-cells.json'
    if path.exists():
        result=planned_boundary(json.loads(path.read_text())['cells'])
        (ROOT/'PLANNED-PRECISION.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items() if k!='zero_error_opportunity_upper_95'},indent=2))
