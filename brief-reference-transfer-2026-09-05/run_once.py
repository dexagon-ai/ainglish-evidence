"""One predeclared four-condition campaign; no retries or continuation after a machine crash."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.request
from unittest.mock import patch
from ainglish import panel
from ainglish.client import manifest_commitment
from local_colony_auth import ainglish_client
from prepare import IDS, ORDER
from build import canonical

ROOT = Path(__file__).resolve().parent

def save(name, value):
    with (ROOT / name).open('x') as f:
        json.dump(value, f, indent=2, ensure_ascii=False); f.write('\n')

def live_models():
    with urllib.request.urlopen('http://127.0.0.1:11434/api/ps', timeout=10) as r:
        return json.load(r)['models']

def now():
    return datetime.now(timezone.utc).isoformat()

def main():
    assert not (ROOT / 'campaign-start.json').exists(), 'Campaign started already; recover existing attempts, never rerun'
    assert not live_models(), 'Do not displace another loaded inference workload'
    gpu = subprocess.run(['nvidia-smi', '--query-gpu=memory.free', '--format=csv,noheader,nounits'],
                         text=True, capture_output=True, check=True).stdout
    assert sum(int(x) for x in gpu.splitlines()) > 40000, 'Insufficient free GPU memory'
    save('campaign-start.json', {'at': now(), 'pid': os.getpid(), 'gpu_free_mib': gpu.splitlines(),
        'order': ORDER, 'downloads': 0, 'retries_permitted': 0,
        'sdk_panel_sha256': hashlib.sha256(Path(panel.__file__).read_bytes()).hexdigest()})
    client = ainglish_client()
    outcomes = []
    for name, exposure in ORDER:
        stem = name + '.' + exposure
        spec = json.loads((ROOT / (stem + '.runspec.json')).read_text())
        assert not (ROOT / (stem + '.intent.json')).exists()
        allowed = {r['model'] for r in spec['panel']}
        assert all(m.get('name', m.get('model')) in allowed for m in live_models()), 'An unrelated model appeared; stop without unloading it'
        suggestions = client.suggestions(proposal=IDS[name])
        proposal = client.proposal(client.proposal_slug_history(IDS[name])['current_slug'], authenticated=True)
        assert proposal['stage'] == 'ratified' and proposal['publication_status'] == 'visible'
        assert hashlib.sha256(proposal['english_mapping'].encode()).hexdigest() == spec['attempt']['planned_sample']['mapping_sha256']
        assert any(m['metric'] == 'token_delta' and not m['is_replication'] and m['confirmed']
                   and m['evidence_state'] == 'valid' and not m.get('retraction') and m['value'] < 0
                   for m in proposal['measurements']), 'No remaining active confirmed supporting cost original'
        data, digest = panel.fetch_items(spec['items_url'], spec['items_sha256'])
        manifest = dict(spec, items=data, items_sha256=digest)
        panel.prepare_reader_instruments(manifest)
        for reader, qualification in zip(manifest['panel'], manifest['reader_qualifications']):
            assert datetime.fromisoformat(qualification['valid_until']) > datetime.now(timezone.utc)
            assert hashlib.sha256(canonical(panel.reader_receipt(reader))).hexdigest() == qualification['settings_sha256']
        planned = panel._planned_panel_manifest(manifest)
        settings = panel._attempt_settings(spec['attempt'], [panel.calibration_gate_statement(manifest), panel.admissibility_gate_statement(manifest)])
        preflight = client.preflight_attempt(proposal['slug'], planned, **settings)
        save(stem + '.preflight.json', preflight)
        save(stem + '.intent.json', {'at': now(), 'manifest_commitment': manifest_commitment(planned),
            'planned_manifest': planned, 'settings': settings, 'proposal': proposal['public_id'], 'suggestions': suggestions})
        opened = {}
        real_mint = client.mint_attempt
        def mint_and_retain(*args, **kwargs):
            result = real_mint(*args, **kwargs)
            save(stem + '.opened.json', result)
            opened.update(result)
            return result
        source = {(r[arm], r['question']): (r['id'], arm, bool(r.get('calibration')))
                  for r in data for arm in ['english', 'ainglish']}
        assert len(source) == 2 * len(data), 'Ambiguous journal-to-input identity'
        journal = (ROOT / (stem + '.calls.jsonl')).open('x')
        count = 0
        def ask_and_retain(reader, text, question, options):
            nonlocal count
            assert opened, 'No inference before retained mint receipt'
            start = time.monotonic()
            ident, arm, control = source[(text, question)]
            record = {'at': now(), 'attempt_id': opened['attempt']['attempt_id'], 'reader': reader['name'],
                'item_id': ident, 'arm': arm, 'calibration': control}
            try:
                answer = panel.ask(reader, text, question, options)
                record['answer'] = str(answer)
                record['absent_reason'] = getattr(answer, 'reason', None) if panel.is_absent(answer) else None
                return answer
            except (Exception, SystemExit) as exc:
                record['exception_type'] = type(exc).__name__
                raise
            finally:
                record['elapsed_seconds'] = round(time.monotonic() - start, 3)
                journal.write(json.dumps(record, ensure_ascii=False) + '\n'); journal.flush(); os.fsync(journal.fileno())
                count += 1
                if count % 32 == 0:
                    print(stem, count, 'calls retained', flush=True)
        try:
            with patch.object(client, 'mint_attempt', side_effect=mint_and_retain):
                result = panel._run_preregistered_panel(manifest, spec, ask_and_retain, client,
                    receipt_dir=str(ROOT), receipt_stem=stem)
            if result is None:
                outcomes.append({'condition': stem, 'status': 'aborted', 'calls': count})
                print(stem, 'ABORTED; no retry', flush=True)
            else:
                summary = {k: result.get(k) for k in ['metric', 'value', 'value_lo', 'value_hi', 'arms', 'per_member', 'stratum_results', 'attempt_id']}
                summary['manifest_hash'] = manifest_commitment(result['manifest'])
                summary['server'] = client.measurement(summary['manifest_hash'])
                save(stem + '.result.json', summary)
                outcomes.append({'condition': stem, 'status': 'filed', 'calls': count,
                                 'manifest_hash': summary['manifest_hash'], 'value': summary['value']})
                print(stem, 'FILED', summary['value'], summary['manifest_hash'], flush=True)
        except (Exception, SystemExit) as exc:
            save(stem + '.exception.json', {'at': now(), 'exception_type': type(exc).__name__,
                'message': str(exc), 'calls_retained': count, 'attempt_id': opened.get('attempt', {}).get('attempt_id'),
                'recovery': 'inspect retained attempt and any submission payload; no inference retry'})
            outcomes.append({'condition': stem, 'status': 'exception-requires-reconciliation', 'calls': count})
            print(stem, type(exc).__name__, 'retained; no retry', flush=True)
        finally:
            journal.close()
    save('campaign-finished.json', {'at': now(), 'outcomes': outcomes})
    print(json.dumps(outcomes), flush=True)

if __name__ == '__main__':
    main()
