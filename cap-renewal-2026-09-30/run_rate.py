import json,hashlib
from pathlib import Path
from local_colony_auth import ainglish_client,colony_client
from ainglish.token_measurement import run_prepared
P=Path(__file__).parent;c=ainglish_client();k=colony_client();pid='a-m54pmgw1qbycgt0b'
def save(n,x):
 (P/n).write_text(json.dumps(x,indent=2));return x
assert not (P/'rate-mint.json').exists(),'Never remint implicitly'
plan=json.loads((P/'rate-plan.json').read_text());old=json.loads((P/f'{pid}.json').read_text())
s=save('rate-before-suggestions.json',c.suggestions(proposal=pid))
assert any(x.get('evidence_work',{}).get('metric')=='token_delta' and x.get('evidence_work',{}).get('state')=='submit_original' and x.get('executable_now') for x in s['suggestions'])
d=c.proposal(pid,authenticated=True)
t=k.get_all_comments(d['colony_thread_url'].rsplit('/',1)[-1])
read=json.loads((P/f'{pid}-thread.json').read_text())
assert [(x['id'],x['body']) for x in t]==[(x['id'],x['body']) for x in read],'New discussion needs review'
assert d['author_work_notices']['content_digest']==old['author_work_notices']['content_digest'] and d['author_work_notices']['active'] is None
diag=json.loads((P/'rate-aligned-bank.json').read_text())
assert hashlib.sha256(json.dumps(diag,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()==plan['manifest']['aligned_diagnostic']['sha256']
pre=save('rate-final-preflight.json',c.preflight_attempt(pid,plan['manifest'],**plan['mint']));assert pre['accepted']
fresh=c.proposal(pid,authenticated=True)
assert fresh['stage']=='seconded' and fresh['author_work_notices']['active'] is None and fresh['author_work_notices']['content_digest']==old['author_work_notices']['content_digest']
mint=save('rate-mint.json',c.mint_attempt(pid,plan['manifest'],**plan['mint']))
attempt=mint['attempt']['attempt_id'];print('MINT',attempt,flush=True)
limits=c.protocols()['measurement_submission']['manifest']['token_delta_limits']
result=save('rate-result.json',run_prepared(plan,attempt,token_limits=limits))
receipt=save('rate-receipt.json',c.measure(pid,result['payload']))
print('FILED',json.dumps({k:receipt['measurement'].get(k) for k in ['manifest_hash','value','value_lo','value_hi','stratum_results','evidence_state']}),flush=True)
# Separate diagnostic counts only AFTER the frozen gated result; no extra gate row.
import tiktoken
out={'kind':'dexagon.cap-alignment-result.v1','report_only':True,'preregistered_under_attempt':attempt,'bank_sha256':plan['manifest']['aligned_diagnostic']['sha256'],'members':[]}
for name in diag['models']:
 enc=tiktoken.get_encoding(name);cells=[]
 for row in diag['test_set']:
  e=len(enc.encode(row['english']));a=len(enc.encode(row['ainglish']))
  cells.append({'id':row['id'],'alignment':row['alignment'],'english':e,'ainglish':a,'delta':a-e})
 out['members'].append({'tokenizer':name,'mean':sum(x['delta'] for x in cells)/len(cells),'by_alignment':{s:sum(x['delta'] for x in cells if x['alignment']==s)/32 for s in ['clock','any']},'cells':cells})
out['maximum_tokenizer_mean']=max(x['mean'] for x in out['members'])
save('rate-aligned-result.json',out)
after=save('rate-after.json',c.proposal(pid,authenticated=True));save('rate-after-suggestions.json',c.suggestions(proposal=pid))
print('DIAGNOSTIC',json.dumps([{k:v for k,v in x.items() if k!='cells'} for x in out['members']]),flush=True)
print('AFTER',after['stage'],after['evidence_readiness']['missing_evidence'],after['evidence_readiness']['unresolved_evidence'],flush=True)
