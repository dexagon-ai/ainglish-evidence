"""Replay official frozen diagnostics and all raw answers without any inference."""
from collections import Counter,defaultdict
from pathlib import Path
from unittest.mock import patch
import json,re
from ainglish import panel
from ainglish.client import manifest_commitment

ROOT=Path(__file__).resolve().parent
STUDIES=['attempt-exposure','outcome-raw-binary','outcome-raw-four-bit','outcome-facts-binary','outcome-facts-four-bit']
def analyze(name):
    folder=ROOT/'readers'/name;out=folder/'execution'
    if not (out/'measurement-after.json').exists():return None
    spec=json.loads((folder/'runspec.json').read_text());filed=json.loads((out/'measurement-after.json').read_text())
    fs=[p for p in out.glob('*.cells.json') if '.calibration.' not in p.name];assert len(fs)==1
    cells=json.loads(fs[0].read_text())['rows'];items=[i for i in spec['items'] if not i.get('calibration')]
    byid={i['id']:i for i in items};readers={r['name']:r for r in spec['panel']}
    assert Counter((r['item_id'],r['reader']) for r in cells)==Counter((i['id'],r['name']) for i in items for r in spec['panel'])
    journal=[json.loads(x) for x in (out/'execution-journal.jsonl').read_text().splitlines()]
    assert journal[-1]['event']=='finished' and not any(x['event']=='fault' for x in journal)
    begins={x['ordinal']:x for x in journal if x['event']=='begin'}
    ends={x['ordinal']:x for x in journal if x['event']=='end'}
    assert begins.keys()==ends.keys() and len(begins)==journal[-1]['calls']
    # Exactly reconstruct the official prompt, then decode the retained raw answer with ask().
    retained={}
    for ordinal,b in begins.items():
        key=(b['reader']['name'],b['prompt'])
        assert key not in retained,'Duplicate reader/prompt invalidates simple one-to-one replay'
        retained[key]=ends[ordinal]
    normalized=[];consumed=set()
    for r in cells:
        i=byid[r['item_id']];assert r['expected']==i['answer']
        assert r['arm']==panel.arm_for(spec['seed'],r['reader'],i['id'])
        def chat(ep,prompt):
            key=(r['reader'],prompt);answer=retained[key];assert key not in consumed
            consumed.add(key);return answer['raw'],answer['truncated']
        with patch.object(panel,'chat',side_effect=chat):
            decoded=panel.ask(dict(readers[r['reader']]),i[r['arm']],i['question'],i['options'],allow_unbound=True)
        if panel.is_absent(decoded):assert panel.is_absent(r['answer'])
        else:assert decoded==r['answer']
        assert r['correct']==(None if panel.is_absent(r['answer']) else str(r['answer']).casefold()==i['answer'].casefold())
        normalized.append((i['id'],r['arm'],r['reader'],r['answer']))
    assert manifest_commitment(filed['manifest'])==manifest_commitment(json.loads((folder/'planned-manifest.json').read_text()))
    contract=panel._settlement_contract(spec,items,spec['panel'],spec['seed'])
    value,arms,strata=panel._stratified_accuracy(normalized,items,contract)
    assert value==filed['value'] and arms==filed['arms']
    lo,hi,att=panel.attested_bootstrap_accuracy(normalized,items,spec['panel'],contract=contract,seed=spec['seed'])
    assert [panel._register_round(lo,4),panel._register_round(hi,4)]==[filed['value_lo'],filed['value_hi']]
    assert att==filed['interval_provenance_attestation']
    for a,b in zip(strata,filed['stratum_results']):assert all(a[k]==b[k] for k in ['id','value','arms'])
    def summary(rows):
        result={}
        for arm in ['english','ainglish']:
            rr=[r for r in rows if r['arm']==arm];counts=Counter()
            for r in rr:
                counts['exact_correct']+=r['correct'] is True
                if panel.is_absent(r['answer']):counts['absent']+=1;continue
                i=byid[r['item_id']];answer=r['answer']
                if name=='attempt-exposure':
                    parsed=re.fullmatch(r'Instruction discharged: (yes|no); outcome attained: (yes|no)\.',answer)
                    gold=[i['oracle']['discharged'],i['oracle']['outcome']];labels=['discharge','outcome']
                elif name.endswith('four-bit'):
                    parsed=re.fullmatch(r'Claim true: (yes|no); x possible: (yes|no); x unique most probable: (yes|no); next result guaranteed x under D: (yes|no)\.',answer)
                    gold=i['oracle']['flags'];labels=['truth','possible','unique_mode','model_probability_one']
                else:
                    counts['truth_correct']+=answer==i['answer'];continue
                if not parsed:counts['off_option']+=1;continue
                for label,pred,g in zip(labels,parsed.groups(),gold):counts[label+'_correct']+=(pred=='yes')==g
            n=len(rr);result[arm]={'n':n,'exact_correct':counts['exact_correct'],**dict(counts),
                'accuracy_percent':round(100*counts['exact_correct']/n,4) if n else None}
        return result
    groups={}
    for field in ['settlement_stratum','form','exposure','boundary','domain']:
        if all(field in i for i in items):groups[field]={str(k):summary([r for r in cells if byid[r['item_id']][field]==k]) for k in sorted({i[field] for i in items})}
    groups['reader']={k:summary([r for r in cells if r['reader']==k]) for k in readers}
    return {'study':name,'manifest_hash':filed['manifest_hash'],'attempt_id':filed['attempt_id'],
        'raw_answer_and_official_estimator_replay':True,'target_items':len(items),'target_calls':len(cells),
        'all_calls':len(begins),'calibration_calls':len(begins)-len(cells),
        'headline':{'value':value,'interval_95':[filed['value_lo'],filed['value_hi']],'arms':arms,'resolution_bound':filed['resolution_bound']},
        'official_strata':strata,'counts':summary(cells),'groups':groups,
        'constant_answer_baseline':max(Counter(i['answer'] for i in items).values())/len(items),
        'limits':['Two cached model families; not humans or independently confirmed results.',
                  'Item bootstrap does not correct shared scenario/template dependence or multiple comparisons.',
                  'All four outcome studies share worlds; do not pool as independent replications.',
                  'Supplying calculations and definitions is not weight training or tokenizer adaptation.',
                  'All outcome probability-one golds are no; the constant-no component baseline is 100%.']}
def main():
    rows=[]
    for name in STUDIES:
        result=analyze(name)
        if result is None:print(name,'not finished');continue
        path=ROOT/'readers'/name/'execution'/'analysis.json'
        if path.exists():assert json.loads(path.read_text())==result
        else:
            with path.open('x') as f:json.dump(result,f,indent=2)
        rows.append(result)
        print(json.dumps({k:result[k] for k in ['study','all_calls','headline','official_strata','counts']},indent=2))
    print('Replayed',sum(x['all_calls'] for x in rows),'recorded calls')
if __name__=='__main__':main()
