"""Execute the frozen new diagnostics through the official preregistered harness."""
import argparse
from contextlib import redirect_stdout
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import urllib.request
from unittest.mock import patch
from ainglish import panel
from ainglish.client import manifest_commitment
from local_colony_auth import ainglish_client

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parent
STUDIES=['attempt-exposure','outcome-raw-binary','outcome-raw-four-bit','outcome-facts-binary','outcome-facts-four-bit']

def now():return datetime.now(timezone.utc).isoformat()
def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:json.dump(value,f,indent=2,ensure_ascii=False,allow_nan=False)

def fresh(folder,spec):
    c=ainglish_client();s=c.suggestions(proposal=spec['public_id']);p=c.proposal(spec['slug'],authenticated=True)
    lock=json.loads((folder/'claim-lock.json').read_text())
    assert p['stage'] in ['seconded','measured'] and not p.get('superseded_by')
    for k in ['english_mapping','predicted_measurement']:assert hashlib.sha256(p[k].encode()).hexdigest()==lock[k+'_sha256']
    assert s['budgets']['measurements']['remaining']>0 and s['budgets']['attempts']['remaining']>0
    if folder.name.startswith('outcome-'):
        assert 'token_delta' in p['evidence_readiness']['satisfied'], 'Prior cost gate changed'
    assert shutil.disk_usage('/mnt/c').free>15*1024**3
    with urllib.request.urlopen('http://127.0.0.1:11435/api/ps',timeout=10) as f:loaded=json.load(f)['models']
    assert all(x['name'] in {r['model'] for r in spec['panel']} for x in loaded)
    panel.prepare_reader_instruments(spec)
    for reader,q in zip(spec['panel'],spec['reader_qualifications']):
        encoded=json.dumps(panel.reader_receipt(reader),sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
        assert hashlib.sha256(encoded).hexdigest()==q['settings_sha256']
        assert datetime.fromisoformat(q['valid_until'])>datetime.now(timezone.utc)
    return c,p,s

def prepare(name):
    folder=ROOT/'readers'/name;spec=json.loads((folder/'unbound-runspec.json').read_text())
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
    spec['items_url']='https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/'+commit+'/'+str(folder.relative_to(REPO))+'/items.json'
    with urllib.request.urlopen(spec['items_url'],timeout=30) as f:assert f.read()==(folder/'items.json').read_bytes()
    c,p,s=fresh(folder,spec)
    manifest=panel._planned_panel_manifest(spec)
    settings=panel._attempt_settings(spec['attempt'],[panel.calibration_gate_statement(spec)])
    preflight=c.preflight_attempt(spec['slug'],manifest,**settings)
    save(folder/'runspec.json',spec);save(folder/'planned-manifest.json',manifest)
    save(folder/'preflight.json',preflight)
    save(folder/'before.json',{'at':now(),'proposal':p,'suggestions':s,
         'selection_boundary':'Explicitly user-commissioned new diagnostic original; own-source replication reminders do not authorise self-confirmation. Authoritative attempt admission is checked separately.'})
    print(name,'preflight accepted; no reader calls',flush=True)

def run(name):
    folder=ROOT/'readers'/name;spec=json.loads((folder/'runspec.json').read_text());out=folder/'execution'
    assert not out.exists(),'Reconcile retained execution; never rerun the same freeze'
    c,p,s=fresh(folder,spec);manifest=panel._planned_panel_manifest(spec)
    assert manifest_commitment(manifest)==manifest_commitment(json.loads((folder/'planned-manifest.json').read_text()))
    settings=panel._attempt_settings(spec['attempt'],[panel.calibration_gate_statement(spec)])
    save(out/'preflight.json',c.preflight_attempt(spec['slug'],manifest,**settings))
    save(out/'intent.json',{'at':now(),'manifest_hash':manifest_commitment(manifest),'retries':0,
                          'scope':'Prospective task-isolation diagnostic, no independent confirmation or replacement of prior criteria.'})
    count=0;chat=panel.chat
    with (out/'execution-journal.jsonl').open('x') as journal:
        def event(x):journal.write(json.dumps({'at':now(),**x},ensure_ascii=False)+'\n');journal.flush()
        def recorded_chat(endpoint,prompt):
            nonlocal count
            assert shutil.disk_usage('/mnt/c').free>15*1024**3,'Physical-host disk floor'
            count+=1;ordinal=count
            event({'event':'begin','ordinal':ordinal,'reader':panel.reader_receipt(endpoint),'prompt':prompt})
            try:raw,truncated=chat(endpoint,prompt)
            except BaseException as exc:
                event({'event':'fault','ordinal':ordinal,'type':type(exc).__name__,'error':str(exc)[:350]});raise
            event({'event':'end','ordinal':ordinal,'raw':raw,'truncated':truncated})
            if ordinal%64==0:print(name,'completed calls',ordinal,flush=True)
            return raw,truncated
        print('Starting',name,'official mint/calibration/targets',flush=True)
        # Keep harness logs bounded in the interactive session; full journal stays on disk.
        with patch.object(panel,'chat',side_effect=recorded_chat),(out/'runner.log').open('x') as log,redirect_stdout(log):
            result=panel._run_preregistered_panel(spec,spec,panel.ask,c,receipt_dir=str(out),receipt_stem=name)
        event({'event':'finished','calls':count,'measurement_emitted':result is not None})
    save(out/'outcome.json',result if result is not None else {'measurement_filed':False,'calls':count})
    if result is not None:
        row=c.measurement(manifest_commitment(result['manifest']));save(out/'measurement-after.json',row)
        print(name,'FILED',row['manifest_hash'],row['value'],row['value_lo'],row['value_hi'],flush=True)
    save(out/'proposal-after.json',c.proposal(spec['slug'],authenticated=True))
    save(out/'suggestions-after.json',c.suggestions(proposal=spec['public_id']))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','run']);parser.add_argument('study',choices=STUDIES+['all'])
    args=parser.parse_args()
    for name in STUDIES if args.study=='all' else [args.study]:(prepare if args.action=='prepare' else run)(name)
