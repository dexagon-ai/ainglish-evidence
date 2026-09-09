"""Run frozen official panels once with a local resource-only cache policy."""
import argparse,copy,json,shutil,subprocess,urllib.request
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
from ainglish import panel
from ainglish.client import manifest_commitment
from local_colony_auth import ainglish_client

ROOT=Path(__file__).resolve().parent;REPO=ROOT.parent
OLD=REPO/'completion-paths-2026-09-09'
FLOOR=15*1024**3; START=22*1024**3
def save(path,value):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('x') as f:json.dump(value,f,indent=2,ensure_ascii=False,allow_nan=False)
def load(path):return json.loads(path.read_text())
def local(path,data=None):
 req=urllib.request.Request('http://127.0.0.1:11434'+path,data=None if data is None else json.dumps(data).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=180) as f:return json.load(f)
def prepare_retention():
 out=ROOT/'retention';spec=copy.deepcopy(load(OLD/'retention-replication/unbound-runspec.json'))
 c=ainglish_client();s=c.suggestions(proposal=spec['public_id']);p=c.proposal(spec['slug'],authenticated=True)
 source=c.measurement(spec['replicates_hash'])
 assert any(x.get('replicates_hash')==spec['replicates_hash'] for x in s['suggestions'])
 assert not source['confirmed'] and source['evidence_state']=='valid'
 spec=panel.prepare_reader_instruments(spec)
 access=c.reader_access(spec['replicates_hash'],[panel.reader_receipt(x) for x in spec['panel']])
 assert access['status']=='matching_inventory'
 # The scientific sample and target-independent qualifications were already frozen
 # and no scientific attempt existed for them. Reuse that disclosed preparation.
 spec['items_url']='https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/823d45f/completion-paths-2026-09-09/retention-replication/items.json'
 with urllib.request.urlopen(spec['items_url'],timeout=30) as f:assert json.load(f)==spec['items']
 spec['attempt']['admissibility_gates'] += [
  'Host free space must remain at least 15 GiB; stop on a resource violation.',
  'Serial execution with only one study model resident; no answer-affecting setting changes, downloads or retries.']
 mf=panel._planned_panel_manifest(spec);assert mf['replicates_hash']==spec['replicates_hash']
 save(out/'access.json',access);save(out/'claim-lock.json',load(OLD/'retention-replication/claim-lock.json'))
 assert {k:p[k] for k in load(out/'claim-lock.json')}==load(out/'claim-lock.json')
 save(out/'runspec.json',spec);save(out/'planned-manifest.json',mf)
 save(out/'preflight.json',c.preflight_attempt(spec['slug'],mf,**panel._attempt_settings(spec['attempt'],[panel.calibration_gate_statement(spec)])))
 save(out/'design.json',{'scope':'Exactly the previously frozen 12-item mixed bare/careful diagnostic, not the full claim.',
  'preparation':'Previous run stopped before mint on the missing SDK target pin. Zero scientific calls on these pairs.',
  'limits':load(OLD/'retention-replication/design.json')['limitations'],
  'resource_policy':'Only unload the explicit study model when moving to another reader, preserving stateless request contents and official scoring.'})
 print('PREPARED retention',manifest_commitment(mf),flush=True)
def run(name):
 out=ROOT/name;spec=load(out/'runspec.json');mf=load(out/'planned-manifest.json')
 assert not (out/'execution').exists(),'Prior execution exists: inspect/reconcile, never rerun'
 assert shutil.disk_usage('/mnt/c').free>=START,'Insufficient initial Windows headroom'
 assert not local('/api/ps')['models'],'Another model is loaded; shared workload is not ours to evict'
 commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
 url=f'https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{commit}/{ROOT.name}/{name}/runspec.json'
 with urllib.request.urlopen(url,timeout=30) as f:assert json.load(f)==spec,'Published freeze differs'
 c=ainglish_client();s=c.suggestions(proposal=spec['public_id']);p=c.proposal(spec['slug'],authenticated=True)
 assert {k:p[k] for k in load(out/'claim-lock.json')}==load(out/'claim-lock.json')
 if spec.get('replicates_hash'):
  assert any(x.get('replicates_hash')==spec['replicates_hash'] for x in s['suggestions']), 'Replication no longer offered'
  source=c.measurement(spec['replicates_hash']);assert source['evidence_state']=='valid' and not source.get('retraction')
  check=c.reader_access(spec['replicates_hash'],[panel.reader_receipt(x) for x in panel.prepare_reader_instruments(spec)['panel']])
  assert check['status']=='matching_inventory';save(out/'access-at-mint.json',check)
 else:
  assert any(x.get('evidence_work',{}).get('metric')==spec['metric'] for x in s['suggestions']), 'Original metric no longer offered'
 assert manifest_commitment(panel._planned_panel_manifest(spec))==manifest_commitment(mf)
 path=out/'execution';path.mkdir();original=panel.chat;loaded=None;ordinal=0
 with (path/'journal.jsonl').open('x') as journal:
  def emit(value):journal.write(json.dumps(value,ensure_ascii=False)+'\n');journal.flush()
  def guarded_chat(endpoint,prompt):
   nonlocal loaded,ordinal
   if shutil.disk_usage('/mnt/c').free<FLOOR:raise RuntimeError('Windows host free-space floor breached (15 GiB)')
   assert endpoint['provider']=='ollama' and endpoint['base_url']=='http://localhost:11434/v1'
   if loaded and loaded!=endpoint['model']:
    emit({'event':'release_previous_study_cache','model':loaded})
    local('/api/generate',{'model':loaded,'keep_alive':0,'stream':False});loaded=None
   loaded=endpoint['model'];ordinal+=1
   emit({'event':'begin','ordinal':ordinal,'reader':endpoint['name'],'prompt':prompt,'host_free_bytes':shutil.disk_usage('/mnt/c').free})
   raw,truncated=original(endpoint,prompt)
   emit({'event':'end','ordinal':ordinal,'raw':raw,'truncated':truncated,'host_free_bytes':shutil.disk_usage('/mnt/c').free})
   if ordinal%8==0:print('CELLS',name,ordinal,flush=True,file=__import__('sys').__stdout__)
   return raw,truncated
  try:
   with patch.object(panel,'chat',side_effect=guarded_chat),(path/'runner.log').open('x') as log,redirect_stdout(log):
    result=panel._run_preregistered_panel(spec,spec,panel.ask,c,receipt_dir=str(path),receipt_stem=name)
   save(out/'outcome.json',result or {'filed':False,'calls':ordinal})
   if result:
    row=c.measurement(manifest_commitment(result['manifest']));save(out/'measurement-after.json',row)
    if spec.get('replicates_hash'):save(out/'source-after.json',c.measurement(spec['replicates_hash']))
    print('FILED',name,row['manifest_hash'],row['value'],row.get('value_lo'),row.get('value_hi'),'eligible',row.get('settlement_eligible'),flush=True)
  except BaseException as exc:
   save(out/'exception.json',{'type':type(exc).__name__,'message':str(exc),'calls_started':ordinal});raise
  finally:
   if loaded:
    emit({'event':'release_final_study_cache','model':loaded})
    local('/api/generate',{'model':loaded,'keep_alive':0,'stream':False})
 save(out/'proposal-after.json',c.proposal(spec['slug'],authenticated=True))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare_retention','run']);p.add_argument('name',nargs='?');a=p.parse_args()
 if a.action=='run':run(a.name)
 else:globals()[a.action]()
