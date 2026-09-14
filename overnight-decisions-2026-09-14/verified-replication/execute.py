"""One official mint/run/file-or-abort; no retries or population substitution."""
from copy import deepcopy
from datetime import datetime,timezone
import json,shutil
from ainglish import panel
from local_colony_auth import ainglish_client
from build import ROOT,PID,SOURCE,write
from prepare import bindings

class Journal:
 def __init__(self,a):self.a=a
 def __getattr__(self,k):return getattr(self.a,k)
 def mint_attempt(self,*args,**kwargs):
  s=self.a.suggestions(proposal=PID,view='full')
  assert any(SOURCE in r.get('evidence_work',{}).get('target_hashes',[]) and r.get('executable_now') for r in s['suggestions'])
  p=self.a.proposal(PID,authenticated=True)
  for k,v in json.loads((ROOT/'FROZEN-PROPOSAL.json').read_text()).items():assert p[k]==v,'Scientific state changed: '+k
  assert p['author_work_notices']['active'] is None
  source=self.a.measurement(SOURCE)
  assert source['evidence_state']=='valid' and source['retraction'] is None
  r=self.a.mint_attempt(*args,**kwargs);write('mint-receipt.json',r);return r
 def measure(self,*args,**kwargs):
  r=self.a.measure(*args,**kwargs);write('submission-receipt.json',r);return r

def main():
 flag=ROOT/'run.execution-started.json'
 if flag.exists():raise SystemExit('Already started; reconcile receipts, never rerun automatically.')
 assert shutil.disk_usage(ROOT).free>20*1024**3
 spec=json.loads((ROOT/'runspec.json').read_text())
 items,digest=panel.fetch_items(spec['items_url'],spec['items_sha256'])
 manifest=dict(deepcopy(spec),items=items,items_sha256=digest);bindings(manifest)
 assert panel._planned_panel_manifest(manifest)==json.loads((ROOT/'planned-manifest.json').read_text())
 a=ainglish_client()
 with flag.open('x') as f:json.dump({'started_at':datetime.now(timezone.utc).isoformat()},f)
 result=panel._run_preregistered_panel(manifest,spec,panel.ask,Journal(a),str(ROOT),'runspec.json')
 if result is None:raise SystemExit('Typed failure; inspect official abort and all cells.')
 write('result.json',result)
 write('after-proposal.private.json',a.proposal(PID,authenticated=True))
 print('Finished verified-state replication',flush=True)

if __name__=='__main__':main()
