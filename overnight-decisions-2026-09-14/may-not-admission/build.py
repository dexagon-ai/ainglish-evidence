"""Create an unadmitted, no-reader candidate bank. No intended senses or golds exist yet."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
rows=[];domain=None
for line in (ROOT/'candidates.txt').read_text().splitlines():
 if not line:continue
 if line.startswith('['):domain=line[1:-1];continue
 assert domain and line.count(' may not ')==1
 rows.append({'id':f'clause-{len(rows)+1:03d}','domain':domain,'clause':line})
assert len(rows)==len({r['clause'].casefold() for r in rows})==160
assert all(sum(r['domain']==d for r in rows)==20 for d in {r['domain'] for r in rows})
payload=json.dumps(rows,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
digest=hashlib.sha256(payload).hexdigest()
doc={'kind':'unadmitted-blind-clause-candidates','candidate_array_sha256':digest,'candidates':rows,
 'scope':'160 distinct authored clauses, 20 per domain. No empirical admission, independent-sampling or comprehension claim. No assigned intention, context or gold has been created.'}
(ROOT/'blind-candidates.json').write_text(json.dumps(doc,indent=2,ensure_ascii=False)+'\n')
template={'candidate_array_sha256':digest,'reviewer':None,'prior_exposure':None,
 'decisions':[{'id':r['id'],'prohibition_plausible':None,'possibility_plausible':None,'reason':None} for r in rows],
 'admitted_clause_count':None,'frozen_at':None}
(ROOT/'review-template.json').write_text(json.dumps(template,indent=2)+'\n')
print('160 distinct unadmitted clauses, 8 authored domain groups; digest',digest)
