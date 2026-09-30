"""Historical-input audit, not fresh-input replication or a new governance result."""
import json,csv,math
from pathlib import Path
from collections import defaultdict,Counter
import tiktoken
P=Path(__file__).parent
rows=[]; studies=[]
for f in sorted((P/'measurements').glob('*.json')):
    m=json.loads(f.read_text()); manifest=m['manifest']; strata=defaultdict(list)
    for model in manifest['models']:
        enc=tiktoken.get_encoding(model)
        for n,item in enumerate(manifest['test_set']):
            e=enc.encode(item['english']); a=enc.encode(item['ainglish'])
            row={'hash':m['manifest_hash'],'construct':manifest.get('construct'), 'submitter':m['submitter']['name'], 'model':model,'pair':n,
                'stratum':item['stratum'],'english':item['english'],'ainglish':item['ainglish'],
                'english_tokens':len(e),'ainglish_tokens':len(a),'delta':len(a)-len(e)}
            rows.append(row); strata[(model,item['stratum'])].append(row['delta'])
    cells=[{'model':model,'stratum':s,'n':len(v),'mean':sum(v)/len(v),'minimum':min(v),'maximum':max(v),
            'delta_counts':dict(sorted(Counter(v).items())),'one_token_one_pair_mean_increment':1/len(v)} for (model,s),v in strata.items()]
    per_member={model:sum(r['delta'] for r in rows if r['hash']==m['manifest_hash'] and r['model']==model)/len(manifest['test_set']) for model in manifest['models']}
    # These nine banks have equal-sized equally weighted strata; do not generalize this reducer.
    assert len({x['n'] for x in cells})==1
    assert len({x['weight'] for x in manifest['settlement_strata']})==1
    stored={x['model']:x['value'] for x in m['per_member']}
    assert all(math.isclose(per_member[k],v,abs_tol=1e-9) for k,v in stored.items()),(f,per_member,stored)
    assert math.isclose(max(per_member.values()),m['value'],abs_tol=1e-9)
    studies.append({'hash':m['manifest_hash'],'construct':manifest.get('construct'),'submitter':m['submitter']['name'],
        'source':m['replicates_hash'],'filed_value':m['value'],'recount_per_member':per_member,'cells':cells,'all_filed_members_reproduced':True})
(P/'token-replay.json').write_text(json.dumps({'scope':'Historical submitted inputs recounted; no new study, no settlement write. No causal attribution to lexical boundaries established by this audit.','studies':studies},indent=2))
with (P/'token-pair-audit.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print('RECOUNTED',len(studies),'studies',len(rows),'tokenizer-pairs; all filed member means matched')
for m in studies:
    print(m['hash'][:8],m['submitter'],m['filed_value'],[(x['stratum'],x['mean'],x['minimum'],x['maximum']) for x in m['cells'] if x['model']=='p50k_base'])
