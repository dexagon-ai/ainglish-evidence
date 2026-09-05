"""One frozen modern primary per invocation. No reader retry or implicit continuation."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import urllib.request
from ainglish import panel
from ainglish.client import manifest_commitment
from local_colony_auth import ainglish_client
from prepare_primary import canonical

ROOT=Path(__file__).resolve().parent

def individually_gated_reader(data, readers, ask):
    """Additional prospective guard: the SDK reports individual gaps but gates the pool.

    Calls/decoding are unchanged. Inspect only frozen positive controls, never real answers,
    before allowing the first real call. Failure raises into the SDK's retained abort path.
    """
    controls={(row[arm],row['question']):(row['id'],arm,row['answer'])
              for row in data if row.get('calibration') for arm in ['english','ainglish']}
    expected={(r['name'],ident,arm) for r in readers for ident,arm,_ in controls.values()}
    observed={}
    passed=False
    def ask_once(reader,text,question,options):
        nonlocal passed
        key=(text,question)
        if key not in controls and not passed:
            assert set(observed)==expected,'every named calibration cell must precede real spend'
            for r in readers:
                cells={arm:[v for (name,_,a),v in observed.items() if name==r['name'] and a==arm]
                       for arm in ['english','ainglish']}
                gap=sum(cells['ainglish'])/len(cells['ainglish'])-sum(cells['english'])/len(cells['english'])
                if gap<0.5: raise RuntimeError('Prospective per-reader calibration gap failed: '+r['name'])
            passed=True
        answer=ask(reader,text,question,options)
        # The ordinary SDK yield guard permits a bounded proportion of off-option answers.
        # Our stricter prospective zero-off-option rule must be enforced here, not merely
        # written in a runspec. Added after auditing/retracting the first will study; no rerun.
        if panel.is_absent(answer) or str(answer) not in options:
            raise RuntimeError('Declared zero-off-option gate: reader '+reader['name']+
                ', answer '+repr(str(answer))+', question '+question)
        if key in controls:
            ident,arm,gold=controls[key]
            cell=(reader['name'],ident,arm)
            assert cell not in observed,'no calibration cell retry'
            observed[cell]=str(answer).casefold()==str(gold).casefold()
        return answer
    return ask_once

def save(name,data):
    with (ROOT/name).open('x') as f:json.dump(data,f,ensure_ascii=False,indent=2)

def main(name):
    assert name in ['regime','some','will']
    stem=name+'-primary'
    assert not list(ROOT.glob(stem+'.attempt-*.json')),'receipt exists: inspect and recover; do not run twice'
    spec=json.loads((ROOT/(name+'.runspec.json')).read_text())
    c=ainglish_client();s=c.suggestions();p=c.proposal(spec['slug'],authenticated=True)
    assert p['stage'] in ['seconded','measured'] and not p.get('superseded_by')
    assert 'token_delta' in p['evidence_readiness']['satisfied']
    assert not p['evidence_readiness']['evidence_ready']
    assert s['budgets']['attempts']['remaining']>0 and s['budgets']['measurements']['remaining']>0
    with urllib.request.urlopen('http://127.0.0.1:11434/api/ps') as response:
        assert not json.load(response)['models'],'do not displace another Ollama workload'
    gpu=subprocess.run(['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout
    assert sum(int(x) for x in gpu.splitlines())>40000
    data,digest=panel.fetch_items(spec['items_url'],spec['items_sha256'])
    manifest=dict(spec,items=data,items_sha256=digest)
    panel.prepare_reader_instruments(manifest)
    for reader,qualification in zip(manifest['panel'],manifest['reader_qualifications']):
        assert datetime.fromisoformat(qualification['valid_until'])>datetime.now(timezone.utc)
        assert hashlib.sha256(canonical(panel.reader_receipt(reader))).hexdigest()==qualification['settings_sha256']
    planned=panel._planned_panel_manifest(manifest)
    settings=panel._attempt_settings(spec['attempt'],(panel.calibration_gate_statement(manifest),))
    preflight=c.preflight_attempt(spec['slug'],planned,**settings)
    save(stem+'-preflight.json',{'at':datetime.now(timezone.utc).isoformat(),'preflight':preflight,
        'proposal_stage':p['stage'],'manifest_commitment':manifest_commitment(planned)})
    ask_once=individually_gated_reader(data,manifest['panel'],panel.ask)
    result=panel._run_preregistered_panel(manifest,spec,ask_once,c,receipt_dir=str(ROOT),receipt_stem=stem)
    if result is None:
        print('ABORTED; retained receipts; no retry',flush=True);return
    summary={k:result.get(k) for k in ['value','value_lo','value_hi','arms','per_member','attempt_id','stratum_results']}
    summary['manifest_hash']=manifest_commitment(result['manifest'])
    summary['server']=c.measurement(summary['manifest_hash'])
    save(stem+'-result.json',summary)
    print('FILED',json.dumps({k:v for k,v in summary.items() if k!='server'}),flush=True)

if __name__=='__main__':main(sys.argv[1])
