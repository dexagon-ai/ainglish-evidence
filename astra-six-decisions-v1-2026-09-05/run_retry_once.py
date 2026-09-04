#!/usr/bin/env python3
"""Mint and execute one frozen eligible replication. Never rerun a consumed attempt."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request
from ainglish import panel
from ainglish.client import manifest_commitment
from local_colony_auth import ainglish_client
from build_retry import TARGET, SLUG, canonical

ROOT = Path(__file__).resolve().parent

def main():
    assert not list(ROOT.glob('runspec-retry.attempt-*.json')), 'a receipt already exists; recover it, never rerun'
    spec = json.loads((ROOT / 'runspec-retry.json').read_text())
    c = ainglish_client()
    suggestions = c.suggestions()
    source = c.measurement(TARGET)
    p = c.proposal(SLUG, authenticated=True)
    assert p['stage'] in ['seconded', 'measured'] and not p.get('superseded_by')
    assert source['evidence_state'] == 'valid' and source['settlement_state'] in ['awaiting','disputed']
    assert source['submitter']['sub'] != suggestions['sub'] and not source['is_replication']
    assert all(r['submitter']['sub'] != suggestions['sub'] for r in source['replications'])
    assert any(TARGET in w['target_hashes'] for w in p['evidence_readiness']['work_items'])
    assert suggestions['budgets']['attempts']['remaining'] > 0 and suggestions['budgets']['measurements']['remaining'] > 0
    with urllib.request.urlopen('http://127.0.0.1:11434/api/ps') as response:
        assert not json.load(response)['models'], 'do not displace another local user'
    gpu = subprocess.run(['nvidia-smi','--query-gpu=memory.free','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout
    assert sum(int(x) for x in gpu.splitlines()) > 40_000
    data, digest = panel.fetch_items(spec['items_url'], spec['items_sha256'])
    manifest = dict(spec, items=data, items_sha256=digest)
    panel.prepare_reader_instruments(manifest)  # Metadata only, no reader spend.
    for reader, qualification in zip(manifest['panel'], manifest['reader_qualifications']):
        assert datetime.fromisoformat(qualification['valid_until']) > datetime.now(timezone.utc)
        receipt = panel.reader_receipt(reader)
        assert hashlib.sha256(canonical(receipt)).hexdigest() == qualification['settings_sha256'], 'qualified settings changed'
    planned = panel._planned_panel_manifest(manifest)
    settings = panel._attempt_settings(spec['attempt'], (panel.calibration_gate_statement(manifest),))
    preflight = c.preflight_attempt(SLUG, planned, **settings)
    with (ROOT / 'retry-preflight.json').open('x') as f:
        json.dump({'at':datetime.now(timezone.utc).isoformat(),'suggestions':suggestions,
                   'source_state':source['settlement_state'],'preflight':preflight,
                   'manifest_commitment':manifest_commitment(planned)},f,indent=2)
    measurement = panel._run_preregistered_panel(manifest, spec, panel.ask, c,
        receipt_dir=str(ROOT), receipt_stem='runspec-retry')
    if measurement is not None:
        result = {k:measurement.get(k) for k in ['value','value_lo','value_hi','arms','per_member','attempt_id']}
        result['manifest_hash'] = manifest_commitment(measurement['manifest'])
        result['server'] = c.measurement(result['manifest_hash'])
        with (ROOT / 'retry-result.json').open('x') as f:json.dump(result,f,indent=2)
        print('FILED',json.dumps({k:v for k,v in result.items() if k!='server'}),flush=True)
    else:
        print('NO MEASUREMENT; inspect the preserved abort receipt',flush=True)

if __name__ == '__main__':
    main()
