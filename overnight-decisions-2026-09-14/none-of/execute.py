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
from ainglish.client import manifest_commitment
from local_colony_auth import ainglish_client
from prepare import check_reader_bindings
from build import ROOT,PID,write

class JournalClient:
 def __init__(self,client,name):self.client=client;self.name=name
 def __getattr__(self,key):return getattr(self.client,key)
 def mint_attempt(self,*args,**kwargs):
  frozen=json.loads((ROOT/'FROZEN-PROPOSAL.json').read_text())
  self.client.suggestions(proposal=PID,view='full')
  fresh=self.client.proposal(PID,authenticated=True)
  for key in ['slug','form','english_mapping','predicted_measurement','evidence_contract']:
   assert frozen[key]==fresh[key], 'Live proposal changed before mint: '+key
  assert fresh['stage'] in ['seconded','measured']
  assert fresh['author_work_notices']['active'] is None, 'New author notice needs review'
  receipt=self.client.mint_attempt(*args,**kwargs)
  write(self.name+'.mint-receipt.json',receipt)
  return receipt

def main():
 name=sys.argv[1];assert name in ['primary','consequences','learning']
 flag=ROOT/(name+'.execution-started.json')
 if flag.exists():raise SystemExit('Already started; inspect actual attempt and saved artifacts before any further action.')
 assert shutil.disk_usage(ROOT).free>20*1024**3
 spec=json.loads((ROOT/(name+'.runspec.json')).read_text())
 items,digest=panel.fetch_items(spec['items_url'],spec['items_sha256'])
 manifest=dict(deepcopy(spec),items=items,items_sha256=digest)
 check_reader_bindings(manifest)
 planned=panel._planned_panel_manifest(manifest)
 assert planned==json.loads((ROOT/(name+'.planned-manifest.json')).read_text())
 a=ainglish_client()
 settings=panel._attempt_settings(spec['attempt'],[panel.calibration_gate_statement(manifest),panel.admissibility_gate_statement(manifest)])
 receipt=a.preflight_attempt(spec['slug'],planned,**settings)
 assert receipt['accepted'] is True and receipt['manifest_commitment']==manifest_commitment(planned)
 with flag.open('x') as f:json.dump({'started_at':datetime.now(timezone.utc).isoformat(),'manifest_commitment':manifest_commitment(planned)},f)
 # This is the same mint -> calibration -> target -> exact measure/abort implementation used
 # by ainglish-panel run --submit; only its authenticated client is supplied locally.
 result=panel._run_preregistered_panel(manifest,spec,panel.ask,JournalClient(a,name),str(ROOT),name+'.runspec.json')
 write(name+'.after-proposal.json',a.proposal(PID,authenticated=True))
 write(name+'.after-suggestions.json',a.suggestions(proposal=PID,view='full'))
 # after-suggestions may contain private observation metadata. Never publish it.
 if result is None:raise SystemExit(1)
 write(name+'.result.json',result)
 print('FINISHED',name,'measurement',manifest_commitment(result['manifest']),flush=True)

if __name__=='__main__':main()
