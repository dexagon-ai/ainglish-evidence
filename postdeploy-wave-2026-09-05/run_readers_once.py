"""One attempt per frozen comparison. Retain mint and every cell; never retry inference."""
from datetime import datetime,timezone
import hashlib,json,os,time,urllib.request
from pathlib import Path
from unittest.mock import patch
from ainglish import panel
from ainglish.client import manifest_commitment
from local_colony_auth import ainglish_client
from analyse import ORDER
from prepare_readers import IDS,save
from validate_studies import validate,canonical

ROOT=Path(__file__).resolve().parent
STOP_ON_ABORT=False
def now():return datetime.now(timezone.utc).isoformat()
def main():
 validate();save('reader-campaign-start.json',{'at':now(),'order':ORDER,'pid':os.getpid(),'new_models':0,'retries':0})
 outcomes=[]
 for stem in ORDER:
  name=stem.split('.')[0];c=ainglish_client();opened={};count=0;journal=None
  try:
   spec=json.loads((ROOT/(stem+'.runspec.json')).read_text())
   assert not (ROOT/(stem+'.opened.json')).exists()
   with urllib.request.urlopen('http://127.0.0.1:11434/api/ps',timeout=10) as r:loaded=json.load(r)['models']
   assert all(m.get('name',m.get('model')) in {r['model'] for r in spec['panel']} for m in loaded),'Unrelated inference workload'
   suggestions=c.suggestions(proposal=IDS[name])
   p=c.proposal(c.proposal_slug_history(IDS[name])['current_slug'],authenticated=True)
   assert p['stage'] in ['seconded','measured'] and p['publication_status']=='visible'
   assert hashlib.sha256(p['english_mapping'].encode()).hexdigest()==spec['attempt']['planned_sample']['mapping_sha256']
   evidence=p['evidence_readiness']
   assert all((x if isinstance(x,str) else x['metric']) in evidence['satisfied'] for x in evidence['prerequisites'])
   data,sha=panel.fetch_items(spec['items_url'],spec['items_sha256']);manifest=dict(spec,items=data,items_sha256=sha)
   panel.prepare_reader_instruments(manifest)
   for reader,q in zip(manifest['panel'],manifest['reader_qualifications']):
    assert datetime.fromisoformat(q['valid_until'])>datetime.now(timezone.utc)
    assert hashlib.sha256(canonical(panel.reader_receipt(reader))).hexdigest()==q['settings_sha256']
   planned=panel._planned_panel_manifest(manifest)
   settings=panel._attempt_settings(spec['attempt'],[panel.calibration_gate_statement(manifest),panel.admissibility_gate_statement(manifest)])
   save(stem+'.preflight.json',c.preflight_attempt(p['slug'],planned,**settings))
   save(stem+'.intent.json',{'at':now(),'manifest_commitment':manifest_commitment(planned),'manifest':planned,'settings':settings,'suggestions':suggestions})
   original_mint=c.mint_attempt
   def mint(*args,**kwargs):
    receipt=original_mint(*args,**kwargs);save(stem+'.opened.json',receipt);opened.update(receipt);return receipt
   source={(r[arm],r['question']):(r['id'],arm,bool(r.get('calibration'))) for r in data for arm in ['english','ainglish']}
   assert len(source)==len(data)*2
   journal=(ROOT/(stem+'.calls.jsonl')).open('x')
   def ask(reader,text,question,options):
    nonlocal count
    assert opened,'No target call before retained mint'
    ident,arm,control=source[text,question];started=time.monotonic()
    record={'at':now(),'item_id':ident,'arm':arm,'calibration':control,'reader':reader['name'],'attempt_id':opened['attempt']['attempt_id']}
    try:
     answer=panel.ask(reader,text,question,options);record['answer']=str(answer)
     record['absent_reason']=getattr(answer,'reason',None) if panel.is_absent(answer) else None
     return answer
    except (Exception,SystemExit) as exc:record['exception_type']=type(exc).__name__;raise
    finally:
     record['elapsed_seconds']=round(time.monotonic()-started,3)
     journal.write(json.dumps(record)+'\n');journal.flush();os.fsync(journal.fileno());count+=1
     if count%32==0:print(stem,count,'calls retained',flush=True)
   with patch.object(c,'mint_attempt',side_effect=mint):
    result=panel._run_preregistered_panel(manifest,spec,ask,c,receipt_dir=str(ROOT),receipt_stem=stem)
   if result is not None:
    save(stem+'.result.json',result);save(stem+'.server.json',c.attempt(result['attempt_id']))
   out={'study':stem,'state':'filed' if result is not None else 'aborted','calls':count,'value':None if result is None else result['value']}
   outcomes.append(out);print(json.dumps(out),flush=True)
   if result is None and STOP_ON_ABORT:
    print('Stopping remaining campaign after abort; no redesign or target retry.',flush=True)
    break
  except (Exception,SystemExit) as exc:
   save(stem+'.exception.json',{'at':now(),'type':type(exc).__name__,'message':str(exc),'calls_retained':count,
    'attempt_id':opened.get('attempt',{}).get('attempt_id'),'recovery':'Reconcile retained attempt/submission; no reader retry.'})
   outcomes.append({'study':stem,'state':'reconciliation-required','calls':count})
   print(stem,type(exc).__name__,'retained; no retry',flush=True)
   if STOP_ON_ABORT:break
  finally:
   if journal is not None:journal.close()
 save('reader-campaign-finished.json',{'at':now(),'outcomes':outcomes});print(json.dumps(outcomes),flush=True)
if __name__=='__main__':main()
