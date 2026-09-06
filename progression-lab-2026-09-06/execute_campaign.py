"""Once-only mint-before-spend execution of the frozen token and replication work."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
from unittest.mock import patch
import urllib.request

from ainglish import panel, token_measurement
from ainglish.client import manifest_commitment
from local_colony_auth import ainglish_client
from snapshot import ROOT, save


def now(): return datetime.now(timezone.utc).isoformat()


def committed(path, commit):
    name = path.relative_to(ROOT.parent).as_posix()
    raw = subprocess.check_output(['git', 'show', f'{commit}:{name}'], cwd=ROOT.parent)
    assert raw == path.read_bytes(), f'Frozen source changed: {name}'


def prepare(commit):
    template = ROOT/'frozen/construction.runspec.template.json'
    items = ROOT/'frozen/construction.items.json'
    for path in [template, items, ROOT/'execute_campaign.py']: committed(path, commit)
    spec = json.loads(template.read_text())
    spec['items_url'] = f'https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{commit}/{ROOT.name}/frozen/construction.items.json'
    fetched, digest = panel.fetch_items(spec['items_url'], spec['items_sha256'])
    manifest = dict(spec, items=fetched, items_sha256=digest)
    panel.prepare_reader_instruments(manifest)
    planned = panel._planned_panel_manifest(manifest)
    assert planned['calibration']['rule'] == 'absolute-gap-v1'
    assert planned['calibration']['min_gap'] == 0.5
    assert planned['settlement_strata'] == spec['settlement_strata']
    settings = panel._attempt_settings(spec['attempt'], [panel.calibration_gate_statement(manifest), panel.admissibility_gate_statement(manifest)])
    client = ainglish_client()
    save('frozen/construction.runspec.json', spec)
    save('frozen/construction.planned.json', planned)
    save('frozen/construction.preflight.json', client.preflight_attempt(spec['slug'], planned, **settings))
    print('Live preflight retained; no mint or reader call.')


def token(commit):
    for path in [ROOT/'frozen/instance-token.prepared.json', ROOT/'execute_campaign.py']: committed(path, commit)
    if (ROOT/'execution/token.intent.json').exists(): raise SystemExit('Existing token intent; reconcile, do not rerun')
    client = ainglish_client()
    client.suggestions(proposal='a-sbff0j0jj24dtxbh')
    p = client.proposal('a-sbff0j0jj24dtxbh', authenticated=True)
    before = json.loads((ROOT/'snapshot/instance.proposal.json').read_text())
    assert p['stage'] in ('seconded', 'measured') and p['english_mapping'] == before['english_mapping']
    plan = json.loads((ROOT/'frozen/instance-token.prepared.json').read_text())
    save('execution/token.preflight.json', client.preflight_attempt(p['slug'], plan['manifest'], **plan['mint']))
    save('execution/token.intent.json', {'at': now(), 'freeze': commit, 'retries': 0})
    opened = client.mint_attempt(p['slug'], plan['manifest'], **plan['mint'])
    save('execution/token.opened.json', opened)
    attempt = opened['attempt']['attempt_id']
    try:
        result = token_measurement.run_prepared(plan, attempt)
        save('execution/token.result.json', result)
        receipt = client.measure(p['slug'], result['payload'])
        save('execution/token.receipt.json', receipt)
        print('Token measurement filed', result['payload']['value'], attempt, flush=True)
    except Exception as exc:
        save('execution/token.error.json', {'at': now(), 'type': type(exc).__name__, 'message': str(exc), 'attempt_id': attempt,
              'next': 'Reconcile saved result without recounting, or abort on evidenced declared gate failure.'})
        raise


def replication(commit):
    for path in [ROOT/'frozen/construction.runspec.json', ROOT/'frozen/construction.planned.json', ROOT/'execute_campaign.py']: committed(path, commit)
    if (ROOT/'execution/construction.intent.json').exists(): raise SystemExit('Existing reader intent; reconcile, never retry targets')
    client = ainglish_client()
    spec = json.loads((ROOT/'frozen/construction.runspec.json').read_text())
    tasks = client.suggestions(proposal='a-0w08sbp8900wxtqb')
    assert any(r.get('replicates_hash') == spec['replicates_hash'] for r in tasks['suggestions']), 'No eligible source seat'
    fresh = client.proposal(spec['slug'], authenticated=True)
    assert fresh['stage'] in ('seconded', 'measured')
    assert hashlib.sha256(fresh['english_mapping'].encode()).hexdigest() == spec['attempt']['planned_sample']['mapping_sha256']
    source = client.measurement(spec['replicates_hash'])
    assert source['evidence_state'] == 'valid' and not source['voided_at']
    with urllib.request.urlopen('http://127.0.0.1:11434/api/ps', timeout=10) as response:
        loaded = json.load(response)['models']
    assert all(m.get('name', m.get('model')) in {r['model'] for r in spec['panel']} for m in loaded), 'Unrelated model loaded; no eviction'
    items, sha = panel.fetch_items(spec['items_url'], spec['items_sha256'])
    manifest = dict(spec, items=items, items_sha256=sha)
    panel.prepare_reader_instruments(manifest)
    for reader, qualification in zip(manifest['panel'], manifest['reader_qualifications']):
        assert datetime.fromisoformat(qualification['valid_until']) > datetime.now(timezone.utc)
        canonical = json.dumps(panel.reader_receipt(reader), sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
        assert hashlib.sha256(canonical).hexdigest() == qualification['settings_sha256']
    planned = panel._planned_panel_manifest(manifest)
    assert planned == json.loads((ROOT/'frozen/construction.planned.json').read_text())
    save('execution/construction.intent.json', {'at': now(), 'freeze': commit, 'manifest_hash': manifest_commitment(planned), 'retries': 0})
    opened = {}
    original_mint, original_chat = client.mint_attempt, panel.chat
    calls = 0
    with (ROOT/'execution/construction.raw.jsonl').open('x') as journal:
        def mint(*args, **kwargs):
            receipt = original_mint(*args, **kwargs)
            save('execution/construction.opened.json', receipt)
            opened.update(receipt)
            return receipt
        def chat(reader, prompt):
            nonlocal calls
            assert opened, 'No target or calibration before mint'
            record = {'at': now(), 'reader': reader['name'], 'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest()}
            try:
                raw, truncated = original_chat(reader, prompt)
                record.update(raw=raw, truncated=truncated)
                return raw, truncated
            except BaseException as exc:
                record['error_type'] = type(exc).__name__
                raise
            finally:
                journal.write(json.dumps(record, ensure_ascii=False)+'\n'); journal.flush(); os.fsync(journal.fileno())
                calls += 1
                if calls % 24 == 0: print('construction', calls, 'reader calls retained', flush=True)
        with patch.object(client, 'mint_attempt', side_effect=mint), patch.object(panel, 'chat', side_effect=chat):
            result = panel._run_preregistered_panel(manifest, spec, panel.ask, client,
                receipt_dir=str(ROOT/'execution'), receipt_stem='construction')
    if result is not None:
        save('execution/construction.result.json', result)
        save('execution/construction.receipt.json', client.attempt(result['attempt_id']))
    save('execution/construction.finished.json', {'at': now(), 'status': 'filed' if result else 'aborted', 'calls': calls,
        'value': result['value'] if result else None})
    print('Construction', 'filed' if result else 'aborted', calls, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'token', 'replication'])
    parser.add_argument('--commit', required=True)
    args = parser.parse_args()
    globals()[args.action](args.commit)
