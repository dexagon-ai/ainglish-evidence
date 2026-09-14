"""Prospective report helpers. No network, model calls or Ainglish writes."""
from collections import Counter, defaultdict
import json
import hashlib
import math
from pathlib import Path
import random
import sys

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

def decode(items, journal):
    """Recompute scores from saved raw SDK answers; do not trust the journal's correct flag."""
    lookup={i['id']:i for i in items if not i.get('calibration')}
    out=[]; seen=set()
    for cell in journal:
        iid=cell['item_id']; item=lookup[iid]
        identity=(iid,cell['reader'])
        if identity in seen: raise ValueError('Repeated reader/world cell')
        seen.add(identity)
        if cell['arm'] not in ['english','ainglish']: raise ValueError('Unknown arm')
        answer=cell.get('answer')
        absent=bool(cell.get('absence_reason')) or answer is None
        records=item['probe_contract']['option_records']
        # Match the SDK's case-insensitive exact-label scoring, without extracting prose.
        record=next((r for option,r in records.items() if str(answer).casefold()==option.casefold()),None) if not absent else None
        gold=item['probe_contract']['gold']
        row={'world_id':item['world_id'],'reader':cell['reader'],'arm':cell['arm'],
             'form':item['settlement_stratum'],'domain':item['domain'],'frame_family':item['frame_family'],
             'absent':absent,'absence_reason':cell.get('absence_reason'),
             'joint':None if absent else str(answer).casefold()==item['answer'].casefold(),
             'off_option':not absent and record is None,
             'policies':None if record is None else record['policies']==gold['policies'],
             'guarantees':None if record is None else record['guarantees']==gold['guarantees'],
             'decisions':{}}
        for field,key in [('policies','kind'),('guarantees','key')]:
            for candidate in item['probe_contract'][field]:
                label=candidate['label']
                if {label in r[field] for r in records.values()}!={False,True}: continue
                truth=label in gold[field]
                prediction=None if record is None else label in record[field]
                row['decisions'][candidate[key]]={'expected':truth,'chosen':prediction,
                    'error':None if prediction is None else prediction!=truth,'kind':field}
        row['wrong_pole_policy_choice']=None if record is None else any(
            d['error'] for d in row['decisions'].values() if d['kind']=='policies')
        out.append(row)
    return out

def rate_table(values):
    """Values: True=success/error under named table, False=no, None=unknown."""
    known=[v for v in values if v is not None]
    k=sum(known); n=len(known); u=len(values)-n
    return {'known':n,'yes':k,'unknown':u,'rate_known':k/n if n else None,
            'exact_binomial_95_known':interval(k,n),
            'unknown_all_no_rate':k/(n+u) if n+u else None,
            'unknown_all_yes_rate':(k+u)/(n+u) if n+u else None}

def analyse(items,journal,draws=20000):
    rows=decode(items,journal)
    groups=defaultdict(list)
    for row in rows:
        groups[(row['form'],row['reader'],row['arm'],'ALL')].append(row)
        groups[(row['form'],row['reader'],row['arm'],row['domain'])].append(row)
    tables=[]; ni_counts=defaultdict(lambda:defaultdict(dict))
    for (form,reader,arm,domain),members in sorted(groups.items()):
        live=[r for r in members if not r['absent']]
        table={'form':form,'reader':reader,'arm':arm,'domain':domain,'attempted':len(members),
               'live':len(live),'typed_absent':len(members)-len(live),
               'off_option':sum(r['off_option'] for r in live)}
        for outcome in ['joint','policies','guarantees','wrong_pole_policy_choice']:
            table[outcome]=rate_table([r[outcome] for r in live])
        table['decisions']={k:rate_table([r['decisions'][k]['error'] for r in live if k in r['decisions']])
            for k in sorted({k for r in members for k in r['decisions']})}
        table['scope']='Conditional per-reader distinct-world binomial intervals; authored-frame assumptions may fail.'
        tables.append(table)
        if domain=='ALL': ni_counts[form][reader][arm]={'correct':sum(r['joint'] for r in live),'live':len(live)}
    pooled=[]
    for form in sorted({r['form'] for r in rows}):
        for arm in ['english','ainglish']:
            members=[r for r in rows if r['form']==form and r['arm']==arm]
            live=[r for r in members if not r['absent']]
            pooled.append({'form':form,'arm':arm,'attempted':len(members),'live':len(live),
                'joint_correct':sum(r['joint'] for r in live),
                'joint_accuracy':sum(r['joint'] for r in live)/len(live) if live else None,
                'binomial_interval':None,'reason':'Two readers can share worlds; pooled counts are descriptive.'})
    return {'kind':'choose-any.supplementary-report.v2','official_result_changed':False,
        'recorded_target_cells':len(rows),'joint_contrast_pp':contrast(rows),'pooled_descriptive_counts':pooled,
        'conditional_ni':{f:conditional_ni(r) for f,r in ni_counts.items()},
        'per_reader_form_domain_tables':tables,'correlation_sensitivity':correlation_sensitivity(rows,draws=draws),
        'truth_boundary':'Report-only, fixed current readers/authored task; no automatic carrier pass or ratification.'}

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
    assert rate_table([True,False,None])['unknown_all_yes_rate']==2/3
    if (ROOT/'items.json').exists():
        items=[i for i in json.loads((ROOT/'items.json').read_text()) if not i.get('calibration')]
        # Every record is tested, including both partial-error directions and unknown responses.
        for item in items:
            for answer in item['options']+['off option',None]:
                row=decode([item],[{'item_id':item['id'],'reader':'EXCLUDED-UNIT-TEST',
                    'arm':'ainglish','answer':answer}])[0]
                if answer is None: assert row['absent'] and row['joint'] is None
                elif answer=='off option': assert row['joint'] is False and row['policies'] is None
                else:
                    record=item['probe_contract']['option_records'][answer]
                    assert row['joint']==(answer==item['answer'])
                    assert row['policies']==(record['policies']==item['probe_contract']['gold']['policies'])
                    assert row['guarantees']==(record['guarantees']==item['probe_contract']['gold']['guarantees'])
    return {'status':'FILE_ONLY_STATISTICAL_HELPER_TESTS_PASS','target_reader_calls':0}

if __name__=='__main__':
    print(json.dumps(selftest()))
    if len(sys.argv)>1:
        if len(sys.argv)!=3: raise SystemExit('Usage: report.py SDK_REAL_CELL_JOURNAL.json NEW_REPORT.json')
        output=Path(sys.argv[2])
        if output.exists(): raise SystemExit('Refusing to overwrite an existing report')
        journal=json.loads(Path(sys.argv[1]).read_text())
        if not isinstance(journal,dict) or journal.get('kind')!='ainglish.panel.cell-results.v1':
            raise SystemExit('Requires the official saved real-cell journal, not calibration or synthetic output')
        plan=json.loads((ROOT/'planned-cells.json').read_text())['cells']
        expected={(c['world_id'],c['reader']):c['arm'] for c in plan}
        for cell in journal['rows']:
            if expected.get((cell['item_id'],cell['reader']))!=cell['arm']:
                raise SystemExit('Journal cell does not match the frozen world/reader/arm assignment')
        items=json.loads((ROOT/'items.json').read_text())
        result=analyse(items,journal['rows'])
        result['items_sha256']=hashlib.sha256(json.dumps(items,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
        result['planned_target_cells']=len(plan)
        result['planned_cells_complete']=len(journal['rows'])==len(plan)
        if not result['planned_cells_complete']:
            result['conditional_ni']={'status':'unavailable_incomplete_run','reason':'Preserve partial/abort observations; do not certify preservation.'}
        result['source_attempt_id']=journal.get('attempt_id')
        output.write_text(json.dumps(result,indent=2)+'\n')
        raise SystemExit(0)
    path=ROOT/'planned-cells.json'
    if path.exists():
        result=planned_boundary(json.loads(path.read_text())['cells'])
        (ROOT/'PLANNED-PRECISION.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:v for k,v in result.items() if k!='zero_error_opportunity_upper_95'},indent=2))
