"""Bind/preflight, then separately execute the publicly frozen study once."""
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

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as out:
        json.dump(value, out, indent=2, ensure_ascii=False, allow_nan=False)
        out.write('\n')


def fresh(spec):
    from local_colony_auth import ainglish_client, colony_client
    client = ainglish_client()
    suggestions = client.suggestions(proposal=spec['public_id'])
    proposal = client.proposal(spec['slug'], authenticated=True)
    lock = json.loads((ROOT / 'claim-lock.json').read_text())
    for field in ['english_mapping', 'predicted_measurement']:
        assert hashlib.sha256(proposal[field].encode()).hexdigest() == lock[field + '_sha256'], 'Claim changed'
    assert proposal['stage'] == 'seconded' and not proposal['superseded_by'], 'Stage changed'
    action = proposal['progression_path']['current_action']
    assert action['metric'] == 'comprehension_accuracy_delta' and action['method'] == 'POST'
    assert 'original' in action['what'], 'Current action changed'
    colony_client().get_all_comments(proposal['colony_thread_url'].rsplit('/', 1)[-1])
    assert shutil.disk_usage('/mnt/c').free > 15 * 1024 ** 3, 'Physical disk floor'
    with urllib.request.urlopen('http://127.0.0.1:11434/api/ps', timeout=10) as response:
        loaded = json.load(response)['models']
    assert all(r['name'] in {x['model'] for x in spec['panel']} for r in loaded), 'Unrelated workload; no eviction'
    panel.prepare_reader_instruments(spec)
    for endpoint, q in zip(spec['panel'], spec['reader_qualifications']):
        instrument = panel.reader_receipt(endpoint)
        digest = hashlib.sha256(json.dumps(instrument, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
        assert digest == q['settings_sha256'], 'Qualification settings changed'
        assert datetime.fromisoformat(q['valid_until']) > datetime.now(timezone.utc), 'Qualification expired'
    return client, proposal, suggestions


def prepare():
    spec = json.loads((ROOT / 'unbound-runspec.json').read_text())
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip()
    spec['items_url'] = ('https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/' + commit +
                         '/next-actions-2026-09-08/attempt-ensure/items.json')
    # Verify the published answer-bearing input bytes before attempting registration.
    with urllib.request.urlopen(spec['items_url'], timeout=20) as response:
        assert response.read() == (ROOT / 'items.json').read_bytes()
    client, proposal, suggestions = fresh(spec)
    planned = panel._planned_panel_manifest(spec)
    settings = panel._attempt_settings(spec['attempt'], [panel.calibration_gate_statement(spec)])
    result = client.preflight_attempt(spec['slug'], planned, **settings)
    save(ROOT / 'runspec.json', spec)
    save(ROOT / 'planned-manifest.json', planned)
    save(ROOT / 'preflight.json', result)
    save(ROOT / 'before.json', {'at': now(), 'proposal': proposal, 'suggestions': suggestions})
    print('Prepared without inference:', manifest_commitment(planned), flush=True)
    print('Preflight:', json.dumps(result)[:2500], flush=True)


def run():
    out = ROOT / 'execution'
    assert not out.exists(), 'Existing execution must be reconciled, never automatically rerun'
    spec = json.loads((ROOT / 'runspec.json').read_text())
    client, proposal, suggestions = fresh(spec)
    expected = manifest_commitment(json.loads((ROOT / 'planned-manifest.json').read_text()))
    assert manifest_commitment(panel._planned_panel_manifest(spec)) == expected
    settings = panel._attempt_settings(spec['attempt'], [panel.calibration_gate_statement(spec)])
    save(out / 'preflight.json', client.preflight_attempt(spec['slug'], panel._planned_panel_manifest(spec), **settings))
    save(out / 'intent.json', {'at': now(), 'manifest_hash': expected, 'retries': 0,
                              'public_freeze': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip()})
    ordinal = 0
    original_chat = panel.chat
    with (out / 'execution-journal.jsonl').open('x', encoding='utf-8') as journal:
        def event(value):
            journal.write(json.dumps({'at': now(), **value}, ensure_ascii=False, allow_nan=False) + '\n')
            journal.flush()

        def journal_chat(endpoint, prompt):
            nonlocal ordinal
            assert shutil.disk_usage('/mnt/c').free > 15 * 1024 ** 3, 'Physical disk floor during run'
            ordinal += 1
            cell = ordinal
            event({'event': 'begin', 'ordinal': cell, 'reader': panel.reader_receipt(endpoint), 'prompt': prompt})
            try:
                raw, truncated = original_chat(endpoint, prompt)
            except BaseException as exc:
                event({'event': 'fault', 'ordinal': cell, 'error_type': type(exc).__name__, 'error': str(exc)[:500]})
                raise
            event({'event': 'end', 'ordinal': cell, 'raw': raw, 'truncated': truncated})
            return raw, truncated

        print('Starting preregistered controls, then 512 target calls only if admitted.', flush=True)
        with patch.object(panel, 'chat', side_effect=journal_chat), (out / 'runner.log').open('x') as log, redirect_stdout(log):
            result = panel._run_preregistered_panel(spec, spec, panel.ask, client,
                                                   receipt_dir=str(out), receipt_stem='attempt-ensure')
        event({'event': 'finished', 'calls': ordinal, 'measurement_emitted': result is not None})
    if result is not None:
        save(out / 'outcome.json', result)
        row = client.measurement(manifest_commitment(result['manifest']))
        save(out / 'measurement-after.json', row)
        print('Filed', row['manifest_hash'], result['value'], result['value_lo'], result['value_hi'], flush=True)
    else:
        save(out / 'outcome.json', {'at': now(), 'measurement_filed': False, 'calls': ordinal, 'retries': 0})
        print('Honest refusal/abort retained; no retry.', flush=True)
    save(out / 'proposal-after.json', client.proposal(spec['slug'], authenticated=True))
    save(out / 'suggestions-after.json', client.suggestions(proposal=spec['public_id']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'run'])
    args = parser.parse_args()
    prepare() if args.action == 'prepare' else run()
