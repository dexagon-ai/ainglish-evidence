"""One prospective five-comparison campaign. Retain mint before calls; never retry inference."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
from unittest.mock import patch
from ainglish import panel
from ainglish.client import manifest_commitment
from local_colony_auth import ainglish_client
from prepare import IDS, ORDER, COST, save
from validate_design import canonical, validate

ROOT = Path(__file__).resolve().parent

def now(): return datetime.now(timezone.utc).isoformat()

def live_models():
    with urllib.request.urlopen('http://127.0.0.1:11434/api/ps', timeout=10) as r:
        return json.load(r)['models']

def run(continue_unobserved=False):
    validate()
    prefix = 'unobserved-continuation' if continue_unobserved else 'campaign'
    order = [entry for entry in ORDER if entry != ('verdict', 'bare')] if continue_unobserved else ORDER
    assert not (ROOT / (prefix+'-start.json')).exists(), 'Campaign already started: reconcile retained records, never rerun'
    allowed = {r['model'] for r in json.loads((ROOT/'mean.careful.runspec.json').read_text())['panel']}
    assert all(m.get('name', m.get('model')) in allowed for m in live_models()), 'Do not displace another loaded inference workload'
    if continue_unobserved:
        for name, condition in order:
            stem = name+'.'+condition
            failure = json.loads((ROOT/(stem+'.exception.json')).read_text())
            assert failure['calls_retained'] == 0 and failure['attempt_id'] is None
            assert not any((ROOT/(stem+suffix)).exists() for suffix in ['.opened.json', '.intent.json', '.calls.jsonl'])
    gpu = subprocess.run(['nvidia-smi', '--query-gpu=memory.free', '--format=csv,noheader,nounits'],
                         check=True, capture_output=True, text=True).stdout
    assert sum(int(x) for x in gpu.splitlines()) > (14000 if live_models() else 40000)
    save(prefix+'-start.json', {'at': now(), 'pid': os.getpid(), 'order': order, 'gpu_free_mib': gpu.splitlines(),
         'downloads': 0, 'inference_retries': 0, 'sdk_panel_sha256': hashlib.sha256(Path(panel.__file__).read_bytes()).hexdigest()})
    client = ainglish_client(); outcomes = []
    for name, condition in order:
        stem = name + '.' + condition
        opened, count, journal = {}, 0, None
        try:
            spec = json.loads((ROOT / (stem+('.preflight-fixed.runspec.json' if continue_unobserved else '.runspec.json'))).read_text())
            sample = spec['attempt']['planned_sample']
            assert all(m.get('name', m.get('model')) in {r['model'] for r in spec['panel']} for m in live_models()), 'Unrelated loaded workload appeared'
            suggestions = client.suggestions(proposal=IDS[name])
            proposal = client.proposal(client.proposal_slug_history(IDS[name])['current_slug'], authenticated=True)
            assert proposal['stage'] in ['seconded', 'measured', 'ratified'] and proposal['publication_status'] == 'visible'
            assert hashlib.sha256(proposal['english_mapping'].encode()).hexdigest() == sample['mapping_sha256']
            cost = client.measurement(COST[name])
            assert cost['confirmed'] and not cost['is_replication'] and cost['metric'] == 'token_delta'
            assert cost['evidence_state'] == 'valid' and not cost.get('retraction') and cost['value'] < 0
            data, digest = panel.fetch_items(spec['items_url'], spec['items_sha256'])
            manifest = dict(spec, items=data, items_sha256=digest)
            panel.prepare_reader_instruments(manifest)
            for reader, qualification in zip(manifest['panel'], manifest['reader_qualifications']):
                assert datetime.fromisoformat(qualification['valid_until']) > datetime.now(timezone.utc)
                assert hashlib.sha256(canonical(panel.reader_receipt(reader))).hexdigest() == qualification['settings_sha256']
            planned = panel._planned_panel_manifest(manifest)
            settings = panel._attempt_settings(spec['attempt'], [panel.calibration_gate_statement(manifest), panel.admissibility_gate_statement(manifest)])
            save(stem+'.preflight.json', client.preflight_attempt(proposal['slug'], planned, **settings))
            save(stem+'.intent.json', {'at': now(), 'manifest_commitment': manifest_commitment(planned),
                'planned_manifest': planned, 'settings': settings, 'proposal': proposal['public_id'], 'suggestions': suggestions})
            original_mint = client.mint_attempt
            def mint(*args, **kwargs):
                receipt = original_mint(*args, **kwargs)
                save(stem+'.opened.json', receipt); opened.update(receipt)
                return receipt
            source = {(r[arm], r['question']): (r['id'], arm, bool(r.get('calibration'))) for r in data for arm in ['english', 'ainglish']}
            assert len(source) == 2*len(data)
            journal = (ROOT / (stem+'.calls.jsonl')).open('x')
            def ask(reader, text, question, options):
                nonlocal count
                assert opened, 'No model calls before retained mint'
                item, arm, calibration = source[text, question]; start = time.monotonic()
                record = {'at': now(), 'attempt_id': opened['attempt']['attempt_id'], 'reader': reader['name'],
                          'item_id': item, 'arm': arm, 'calibration': calibration}
                try:
                    answer = panel.ask(reader, text, question, options)
                    record['answer'] = str(answer)
                    record['absent_reason'] = getattr(answer, 'reason', None) if panel.is_absent(answer) else None
                    return answer
                except (Exception, SystemExit) as exc:
                    record['exception_type'] = type(exc).__name__; raise
                finally:
                    record['elapsed_seconds'] = round(time.monotonic()-start, 3)
                    journal.write(json.dumps(record, ensure_ascii=False)+'\n'); journal.flush(); os.fsync(journal.fileno())
                    count += 1
                    if count % 32 == 0: print(stem, count, 'calls retained', flush=True)
            with patch.object(client, 'mint_attempt', side_effect=mint):
                result = panel._run_preregistered_panel(manifest, spec, ask, client, receipt_dir=str(ROOT), receipt_stem=stem)
            if result is None:
                outcomes.append({'condition': stem, 'status': 'aborted', 'calls': count})
                print(stem, 'ABORTED; no retry', flush=True)
            else:
                summary = {k: result.get(k) for k in ['metric', 'value', 'value_lo', 'value_hi', 'arms', 'per_member', 'stratum_results', 'attempt_id']}
                summary['manifest_hash'] = manifest_commitment(result['manifest'])
                summary['server'] = client.measurement(summary['manifest_hash'])
                save(stem+'.result.json', summary)
                outcomes.append({'condition': stem, 'status': 'filed', 'calls': count, 'manifest_hash': summary['manifest_hash'], 'value': summary['value']})
                print(stem, 'FILED', summary['value'], summary['manifest_hash'], flush=True)
        except (Exception, SystemExit) as exc:
            save(stem+('.continuation-exception.json' if continue_unobserved else '.exception.json'), {'at': now(), 'exception_type': type(exc).__name__, 'message': str(exc),
                'calls_retained': count, 'attempt_id': opened.get('attempt', {}).get('attempt_id'),
                'recovery': 'inspect retained attempt and submission payload; no inference rerun'})
            outcomes.append({'condition': stem, 'status': 'exception-requires-reconciliation', 'calls': count})
            print(stem, type(exc).__name__, 'retained; no retry', flush=True)
        finally:
            if journal is not None: journal.close()
    save(prefix+'-finished.json', {'at': now(), 'outcomes': outcomes})
    print(json.dumps(outcomes), flush=True)

if __name__ == '__main__': run('--continue-unobserved' in sys.argv)
