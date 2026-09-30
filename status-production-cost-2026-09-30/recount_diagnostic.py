"""Exact-input arithmetic audit, not a new experiment or replication."""
import json
from pathlib import Path
import tiktoken
P=Path(__file__).parent
out={'kind':'dexagon.status-production-exact-input-audit.v1','new_measurement':False,
 'note':'Post-result descriptive split of the already frozen sixteen derived inputs. Fresh/cached composition was prespecified; this breakdown is diagnostic, not a new settlement stratum or altered estimand. All rows retained.', 'forms':{}}
for form in ['on-record','derived-at-read']:
 plan=json.loads((P/f'{form}-plan.json').read_text());result=json.loads((P/f'{form}-result.json').read_text());members=[]
 for name in plan['manifest']['models']:
  enc=tiktoken.get_encoding(name);rows=[]
  for i,x in enumerate(plan['manifest']['test_set']):
   e=len(enc.encode(x['english']));a=len(enc.encode(x['ainglish']))
   rows.append({'item':i,'english_tokens':e,'ainglish_tokens':a,'delta':a-e,'cached_or_relayed':x['facts'].get('cached_or_relayed')})
  mean=sum(x['delta'] for x in rows)/16
  assert mean==next(x['value'] for x in result['payload']['per_member'] if x['model']==name)
  member={'tokenizer':name,'mean':mean,'rows':rows}
  if form=='derived-at-read':
   member['by_computation_time']={('cached' if flag else 'fresh'):sum(x['delta'] for x in rows if x['cached_or_relayed']==flag)/8 for flag in [False,True]}
  members.append(member)
 out['forms'][form]=members
out['pooled_diagnostic']={name:sum(next(m['mean'] for m in out['forms'][f] if m['tokenizer']==name) for f in out['forms'])/2 for name in ['cl100k_base','o200k_base','p50k_base']}
(P/'exact-input-audit.json').write_text(json.dumps(out,indent=2))
print(out['pooled_diagnostic'])
