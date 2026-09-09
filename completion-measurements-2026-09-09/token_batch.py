"""Freeze before fresh counts. Exact-source audits never count as replications."""
import argparse, hashlib, json, subprocess, urllib.request
from collections import defaultdict
from pathlib import Path
from unittest.mock import patch
from ainglish import estimand, token_measurement
from ainglish.client import _canonical_json, manifest_commitment
from local_colony_auth import ainglish_client

ROOT = Path(__file__).resolve().parent
PRIVATE = Path('/home/dexagon/codex/ainglish-completion-measurements-20260909-Fsr7t7L8')
TARGETS = {
 'rent': ('a-3zjcv2sz5g53nxxd', 'c7470fac03fa2ca7c81b74213a888dab6c99f3d38357278ca6ee5948a490b09b'),
 'choose': ('a-ppyzdf5qk6z67aty', '43cd8d393fa74c455b0f64d9a63a3e04b1b04542935b996d419a876a56f76b02'),
}
FIELDS = ('public_id', 'form', 'english_mapping', 'predicted_measurement', 'evidence_contract')
def save(path, value):
 path.parent.mkdir(parents=True, exist_ok=True)
 with path.open('x') as f: json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
def load(path): return json.loads(path.read_text())
def pairs(rows): return {(r['english'], r['ainglish']) if isinstance(r,dict) else tuple(r) for r in rows}
def fresh(name):
 pid,target=TARGETS[name]; c=ainglish_client(); s=c.suggestions(proposal=pid)
 p=c.proposal(load(PRIVATE/(name+'.proposal.json'))['slug'],authenticated=True)
 m=c.measurement(target)
 assert any(r.get('replicates_hash')==target for r in s['suggestions']), 'Exact source no longer offered'
 assert p['public_id']==pid and p['stage'] in ('seconded','measured')
 assert m['submitter']['sub']!=c.whoami()['sub'] and m['evidence_state']=='valid' and not m.get('retraction')
 assert manifest_commitment(m['manifest'])==target
 return c,p,s,m
def new_rows(name):
 if name=='rent':
  contexts=[('equipment','Nela','oscilloscope','laboratory','inspectors'),
            ('vehicles','Ivo','minibus','transport firm','tour guides'),
            ('rooms','Sora','studio','arts centre','musicians'),
            ('supplies','Tavi','benches','event depot','stallholders')]
  rows=[]
  for domain,person,asset,source,dest in contexts:
   for pole in ('borrow','lend'):
    ending=f'the {asset} '+(f'from the {source}' if pole=='borrow' else f'to the {dest}')+' for a fee.'
    rows.append({'id':f'rent-{domain}-{pole}','stratum':domain+'-'+pole,
      'english':f'{person} will '+('rent ' if pole=='borrow' else 'rent out ')+ending,
      'ainglish':f'{person} will rent-{pole} '+ending})
  return rows
 # Same eight-cell source pattern: 4 any/4 uniform; two long and two concise
 # uniform disclosures; the source's mixed disclosure styles stay visible.
 return [
  {'id':'choose-1','english':'Choose exactly one responsive cache; any eligible member is acceptable and no probability distribution is required.','ainglish':'choose-any(responsive-caches).'},
  {'id':'choose-2','english':'Draw exactly one eligible examiner using a random procedure that gives every distinct eligible examiner equal probability.','ainglish':'draw-uniform(eligible-examiners).'},
  {'id':'choose-3','english':'Please make one equal-probability draw from the frozen 2026-09-06 inspection-ticket set.','ainglish':'Please draw-uniform(inspection-tickets@2026-09-06).'},
  {'id':'choose-4','english':'Select exactly one reachable mirror; any mirror is acceptable and no probability distribution is required.','ainglish':'choose-any(reachable-mirrors).'},
  {'id':'choose-5','english':'Draw exactly one reserve facilitator using a random procedure that gives every facilitator equal probability.','ainglish':'draw-uniform(reserve-facilitators).'},
  {'id':'choose-6','english':'Pick exactly one inspection batch; any batch is acceptable without equal odds requirement.','ainglish':'choose-any(inspection-batches).'},
  {'id':'choose-7','english':'Please make one equal-probability draw from the available assessors for 2026-09-11.','ainglish':'draw-uniform(assessors@2026-09-11).'},
  {'id':'choose-8','english':'Choose exactly one standby gateway; any gateway is acceptable.','ainglish':'choose-any(standby-gateways).'},
 ]
def audit():
 import tiktoken
 reports={}
 with patch('tiktoken.load.read_file',side_effect=RuntimeError('No downloads allowed')):
  for name in ('rent','resume','choose'):
   source=load(PRIVATE/(name+'.source.json')); rows=source['manifest']['test_set']; groups={}
   for model in source['manifest']['models']:
    enc=tiktoken.get_encoding(model); by=defaultdict(list)
    for i,r in enumerate(rows):
     v=len(enc.encode(r['ainglish']))-len(enc.encode(r['english']))
     key=('borrow' if 'rent-borrow' in r['ainglish'] else 'lend') if name=='rent' else (
         ('resume' if 'resume-from' in r['ainglish'] else 'redo') if name=='resume' else ('uniform' if 'draw-uniform' in r['ainglish'] else 'any'))
     by[key].append(v);by['all'].append(v)
    groups[model]={k:{'n':len(v),'mean':sum(v)/len(v),'values':v} for k,v in by.items()}
   reports[name]={'source':source['manifest_hash'],'source_headline':source['value'],'groups':groups,
    'scope':'Exact-input descriptive recount, not a new independent sample, preregistered study or confirming voice.'}
 save(ROOT/'source-cost-audits.json',reports); print(json.dumps(reports,indent=2))
def prepare(name):
 c,p,s,m=fresh(name); rows=new_rows(name); out=ROOT/('cost-'+name)
 assert len(rows)==8 and len(pairs(rows))==8 and not pairs(rows)&pairs(m['manifest']['test_set'])
 mf=c.measurement_template('token_delta',models=m['manifest']['models'])['manifest']
 mf.update(test_set=rows,replicates_hash=TARGETS[name][1],
  test_set_note='Wholly fresh complete pairs preserving the eight-cell source frame and aggregate-only estimator. This does not establish the full reader claim or untested cost strata.',
  proposal_scope_sha256=hashlib.sha256(json.dumps({k:p[k] for k in FIELDS},ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest(),
  proposal_scope_hash_rule='SHA-256 of UTF-8 Python JSON, sorted keys, compact separators, non-ASCII preserved; separate from the scientific manifest commitment.')
 declaration=m['manifest'].get('estimand_contract') or estimand.declaration(
  unit_span='one complete utterance pair',contrast='rent-borrow/rent-lend minus concise rent from/rent out; fee context held identical',
  population='8 fresh complete messages, four source domains crossed with both roles; all counterparties named',
  reducer='least_favourable',aggregation_rule='Unrounded mean over the 8 messages per tokenizer, then maximum tokenizer mean')
 mf=estimand.attach(mf,declaration)
 plan=token_measurement.prepare({'manifest':mf,'replication_target_manifest':m['manifest']},
  token_limits=c.protocols()['measurement_submission']['manifest']['token_delta_limits'],expected_replicates_hash=TARGETS[name][1])
 plan['mint']['admissibility_gates'] += ['Exact target still eligible, current meaning/prediction unchanged, no prior complete-pair overlap.',
  'All named tokenizer vocabularies must already be cached; abort rather than downloading.']
 save(out/'source.json',m);save(out/'claim-lock.json',{k:p[k] for k in FIELDS});save(out/'plan.json',plan)
 save(out/'preflight.json',c.preflight_attempt(p['slug'],plan['manifest'],**plan['mint']))
 print('PREPARED',name,plan['manifest_commitment'],'without fresh token counts')
def run(name):
 out=ROOT/('cost-'+name); assert not (out/'mint.json').exists(),'Reconcile prior execution, never rerun'
 plan=load(out/'plan.json');commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT.parent,text=True).strip()
 url=f'https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{commit}/{ROOT.name}/cost-{name}/plan.json'
 with urllib.request.urlopen(url,timeout=30) as f: assert json.load(f)==plan,'Frozen artifact not publicly retrievable'
 c,p,s,m=fresh(name);assert {k:p[k] for k in FIELDS}==load(out/'claim-lock.json')
 assert not pairs(plan['manifest']['test_set'])&pairs(m['manifest']['test_set'])
 opened=c.mint_attempt(p['slug'],plan['manifest'],**plan['mint']);save(out/'mint.json',opened); aid=opened['attempt']['attempt_id']
 try:
  with patch('tiktoken.load.read_file',side_effect=RuntimeError('No downloads permitted')):
   result=token_measurement.run_prepared(plan,aid,token_limits=plan.get('transport_limits'),expected_replicates_hash=TARGETS[name][1])
   token_measurement.verify_payload(result['payload'])
  save(out/'result.json',result)
 except Exception as exc:
  evidence={'kind':'token-runner-refusal','type':type(exc).__name__,'message':str(exc)}
  save(out/'refusal.json',evidence);save(out/'abort.json',c.abort_attempt(aid,'Frozen token run could not complete',evidence,failed_gate_kind='harness_refuse'));raise
 receipt=c.measure(p['slug'],result['payload']);save(out/'receipt.json',receipt)
 row=c.measurement(manifest_commitment(result['payload']['manifest']));save(out/'measurement-after.json',row)
 save(out/'source-after.json',c.measurement(TARGETS[name][1]));save(out/'proposal-after.json',c.proposal(p['slug'],authenticated=True))
 save(PRIVATE/(name+'.suggestions-after.json'),c.suggestions(proposal=TARGETS[name][0]))
 print('FILED',name,row['manifest_hash'],row['value'],'reproduced',row.get('reproduced_ok'),'eligible',row.get('settlement_eligible'))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['audit','prepare','run']);ap.add_argument('name',nargs='?',choices=list(TARGETS));a=ap.parse_args()
 if a.action=='audit':audit()
 else:globals()[a.action](a.name)
