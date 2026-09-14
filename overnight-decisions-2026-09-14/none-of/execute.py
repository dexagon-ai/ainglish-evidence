"""Exact official preregistered-panel workflow with Dexagon's local authentication helper.

No custom reader/scorer, retry or instrument substitution. Run each named component once.
"""
from copy import deepcopy
from datetime import datetime,timezone
import json
import shutil
import sys
from pathlib import Path
from ainglish import panel
from ainglish.client import AinglishError,manifest_commitment
from local_colony_auth import ainglish_client
from prepare import check_reader_bindings
from build import ROOT,PID,write

class JournalClient:
 def __init__(self,client,name):self.client=client;self.name=name
 def __getattr__(self,key):return getattr(self.client,key)
 def mint_attempt(self,*args,**kwargs):
  frozen=json.loads((ROOT/'FROZEN-PROPOSAL.json').read_text())
  suggestions=self.client.suggestions(proposal=PID,view='full')
  # Production's canonical-slug detail intermittently returned 500 after this
  # original. The deployed API also supports the immutable-ID route. Use the
  # same authenticated SDK transport and verify BOTH namespace and detail;
  # this does not waive identity, freshness or any eligibility check.
  namespace=self.client.proposal_slug_history(PID)
  try:
   fresh=self.client.get('/api/v1/proposals/'+PID,auth=True)
  except AinglishError as error:
   if error.status!=500:raise
   # Only the private standing decoration is unavailable. A fresh public
   # detail still states every scientific field and author notice; authenticated
   # suggestions and the real mint retain caller checks. Do not synthesize a
   # my_vote/independence value, catch permission failures, or reuse an old read.
   fresh=self.client.get('/api/v1/proposals/'+PID,auth=False)
   write(self.name+'.freshness-fallback.json',{'reason':'Authenticated detail HTTP500',
    'fetched_at':datetime.now(timezone.utc).isoformat(),'public_proposal':fresh,
    'boundary':'Fresh public scientific state plus successful authenticated suggestions; real authenticated mint still enforces admission. No private standing inferred.'})
  assert namespace['proposal_public_id']==fresh['public_id']==PID
  assert namespace['current_slug']==fresh['slug']
  for key in ['slug','form','english_mapping','predicted_measurement','evidence_contract']:
   assert frozen[key]==fresh[key], 'Live proposal changed before mint: '+key
  assert fresh['stage'] in ['seconded','measured']
  assert fresh['author_work_notices']['active'] is None, 'New author notice needs review'
  receipt=self.client.mint_attempt(*args,**kwargs)
  write(self.name+'.mint-receipt.json',receipt)
  return receipt
 def measure(self,*args,**kwargs):
  receipt=self.client.measure(*args,**kwargs)
  write(self.name+'.submission-receipt.json',receipt)
  return receipt

def main():
 name=sys.argv[1];assert name in ['primary','consequences','learning']
 flag=ROOT/(name+'.execution-started.json')
 resume='--resume-premint' in sys.argv[2:]
 if flag.exists() and not resume:raise SystemExit('Already started; inspect actual attempt and saved artifacts before any further action.')
 assert shutil.disk_usage(ROOT).free>20*1024**3
 spec=json.loads((ROOT/(name+'.runspec.json')).read_text())
 items,digest=panel.fetch_items(spec['items_url'],spec['items_sha256'])
 manifest=dict(deepcopy(spec),items=items,items_sha256=digest)
 check_reader_bindings(manifest)
 planned=panel._planned_panel_manifest(manifest)
 assert planned==json.loads((ROOT/(name+'.planned-manifest.json')).read_text())
 a=ainglish_client()
 if resume:
  # Recovery is permitted only for a failed LIVE READ before mint: no attempt,
  # no calibration, no target output, and an identical frozen commitment.
  assert flag.exists() and not (ROOT/(name+'.mint-receipt.json')).exists()
  assert not list(ROOT.glob(name+'.runspec.json.attempt-*'))
  previous=json.loads(flag.read_text())
  assert previous['manifest_commitment']==manifest_commitment(planned)
  ledger=a.attempts(spec['slug'])
  assert not any(row.get('pin',{}).get('manifest_commitment')==manifest_commitment(planned) for row in ledger['attempts'])
  write(name+'.premint-recovery.json',{'previous':previous,'ledger':ledger,
   'reason':'HTTP500 during fresh proposal read before mint; zero reader calls. Same frozen study, no inference retry.'})
 settings=panel._attempt_settings(spec['attempt'],[panel.calibration_gate_statement(manifest),panel.admissibility_gate_statement(manifest)])
 receipt=a.preflight_attempt(spec['slug'],planned,**settings)
 assert receipt['accepted'] is True and receipt['manifest_commitment']==manifest_commitment(planned)
 if not resume:
  with flag.open('x') as f:json.dump({'started_at':datetime.now(timezone.utc).isoformat(),'manifest_commitment':manifest_commitment(planned)},f)
 # This is the same mint -> calibration -> target -> exact measure/abort implementation used
 # by ainglish-panel run --submit; only its authenticated client is supplied locally.
 result=panel._run_preregistered_panel(manifest,spec,panel.ask,JournalClient(a,name),str(ROOT),name+'.runspec.json')
 if result is not None:write(name+'.result.json',result)
 write(name+'.after-proposal.json',a.proposal(PID,authenticated=True))
 write(name+'.after-suggestions.json',a.suggestions(proposal=PID,view='full'))
 # after-suggestions may contain private observation metadata. Never publish it.
 if result is None:raise SystemExit(1)
 print('FINISHED',name,'measurement',manifest_commitment(result['manifest']),flush=True)

if __name__=='__main__':main()
