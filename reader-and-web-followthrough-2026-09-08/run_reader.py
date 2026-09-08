"""Official attempt-backed panels with exact public freezes and retained raw journals."""
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
from local_colony_auth import ainglish_client, colony_client

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent

def now(): return datetime.now(timezone.utc).isoformat()

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write('\n')

def fresh(folder, spec):
    c = ainglish_client()
    suggestions = c.suggestions(proposal=spec['public_id'])
    p = c.proposal(spec['slug'], authenticated=True)
    lock = json.loads((folder / 'claim-lock.json').read_text())
    for field in ['english_mapping', 'predicted_measurement']:
        assert hashlib.sha256(p[field].encode()).hexdigest() == lock[field + '_sha256'], 'Claim changed'
    assert p['stage'] in ['seconded', 'measured'] and not p.get('superseded_by'), 'Lifecycle changed'
    assert suggestions['budgets']['measurements']['remaining'] > 0
    assert suggestions['budgets']['attempts']['remaining'] > 0
    comments = colony_client().get_all_comments(p['colony_thread_url'].rsplit('/', 1)[-1])
    if folder.name.startswith('outcome-'):
        review = json.loads((folder.parent / 'outcome-semantic-review.json').read_text())
        assert review['accepted'] and review['reviewer'] != 'dexagon' and review['public_url'].startswith('https://thecolony.ai/post/')
        assert review['items_sha256'][folder.name] == spec['items_sha256'], 'Review does not cover these exact inputs'
        for target in ['d9bc25ff537cc0d5a03dcb21b43c3eda434e547ab0f3af9b9c3c3578aa44f89b',
                       '35874bf6da0cafac20b868fe87d1741a7827a236b01b2d33598790dd4702bb3b']:
            cost = c.measurement(target)
            assert cost['confirmed'] and cost.get('evidence_state', 'valid') == 'valid'
            assert cost['value'] <= 6
        assert 'token_delta' in p['evidence_readiness']['satisfied']
    if folder.name.startswith(('postpone-', 'replace-')):
        family = folder.name.split('-')[0]
        review = json.loads((folder.parent / 'next-kit-semantic-review.json').read_text())
        assert review['accepted'] and review['reviewer'] != 'dexagon' and review['public_url'].startswith('https://thecolony.ai/post/')
        assert review['items_sha256'][folder.name] == spec['items_sha256'], 'Review does not cover exact packet'
        plan = json.loads((folder.parent / (family + '-kit') / 'plan.json').read_text())
        cost = c.measurement(plan['cost_original'])
        assert cost['confirmed'] and cost.get('evidence_state', 'valid') == 'valid'
        assert cost['value'] <= 0 and all(m['value'] <= 0 for m in cost['per_member'])
        assert 'token_delta' in p['evidence_readiness']['satisfied']
    assert shutil.disk_usage('/mnt/c').free > 15 * 1024**3
    with urllib.request.urlopen('http://127.0.0.1:11435/api/ps', timeout=10) as r:
        loaded = json.load(r)['models']
    assert all(x['name'] in {r['model'] for r in spec['panel']} for x in loaded), 'Unrelated reader on owned endpoint'
    panel.prepare_reader_instruments(spec)
    for reader, q in zip(spec['panel'], spec['reader_qualifications']):
        assert hashlib.sha256(json.dumps(panel.reader_receipt(reader), sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest() == q['settings_sha256']
        assert datetime.fromisoformat(q['valid_until']) > datetime.now(timezone.utc)
    return c, p, suggestions, comments

def prepare(folder):
    spec = json.loads((folder / 'unbound-runspec.json').read_text())
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip()
    spec['items_url'] = 'https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/' + commit + '/' + str(folder.relative_to(REPO)) + '/items.json'
    with urllib.request.urlopen(spec['items_url'], timeout=30) as r:
        assert r.read() == (folder / 'items.json').read_bytes(), 'Published input mismatch'
    c, p, suggestions, comments = fresh(folder, spec)
    planned = panel._planned_panel_manifest(spec)
    settings = panel._attempt_settings(spec['attempt'], [panel.calibration_gate_statement(spec)])
    preflight = c.preflight_attempt(spec['slug'], planned, **settings)
    save(folder / 'runspec.json', spec)
    save(folder / 'planned-manifest.json', planned)
    save(folder / 'preflight.json', preflight)
    save(folder / 'before.json', {'at': now(), 'proposal': p, 'suggestions': suggestions, 'comments': comments})
    print(folder.name, 'preflight', json.dumps(preflight)[:1400], flush=True)

def run(folder):
    out = folder / 'execution'
    assert not out.exists(), 'Existing execution must be reconciled, never repeated'
    spec = json.loads((folder / 'runspec.json').read_text())
    c, p, suggestions, comments = fresh(folder, spec)
    planned = panel._planned_panel_manifest(spec)
    expected = manifest_commitment(json.loads((folder / 'planned-manifest.json').read_text()))
    assert manifest_commitment(planned) == expected
    settings = panel._attempt_settings(spec['attempt'], [panel.calibration_gate_statement(spec)])
    save(out / 'preflight.json', c.preflight_attempt(spec['slug'], planned, **settings))
    save(out / 'intent.json', {'at': now(), 'manifest_hash': expected, 'retries': 0,
                              'public_freeze': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip(),
                              'suggestions_offered_tasks': suggestions.get('tiers'),
                              'note': 'Suggestions are advice, not a permission. This explicitly commissioned diagnostic is not relabelled an independent replication.' if folder.name == 'attempt-discharge' else 'Claim component; other comparisons and independent confirmation remain separate.'})
    ordinal = 0
    original_chat = panel.chat
    with (out / 'execution-journal.jsonl').open('x') as journal:
        def event(data):
            journal.write(json.dumps({'at': now(), **data}, ensure_ascii=False, allow_nan=False) + '\n')
            journal.flush()
        def chat(endpoint, prompt):
            nonlocal ordinal
            assert shutil.disk_usage('/mnt/c').free > 15 * 1024**3
            ordinal += 1
            cell = ordinal
            event({'event': 'begin', 'ordinal': cell, 'reader': panel.reader_receipt(endpoint), 'prompt': prompt})
            try:
                raw, truncated = original_chat(endpoint, prompt)
            except BaseException as exc:
                event({'event': 'fault', 'ordinal': cell, 'type': type(exc).__name__, 'error': str(exc)[:500]})
                raise
            event({'event': 'end', 'ordinal': cell, 'raw': raw, 'truncated': truncated})
            return raw, truncated
        print('Starting', folder.name, 'with official mint and calibration before targets', flush=True)
        with patch.object(panel, 'chat', side_effect=chat), (out / 'runner.log').open('x') as log, redirect_stdout(log):
            result = panel._run_preregistered_panel(spec, spec, panel.ask, c, receipt_dir=str(out), receipt_stem=folder.name)
        event({'event': 'finished', 'calls': ordinal, 'measurement_emitted': result is not None})
    save(out / 'outcome.json', result if result is not None else {'measurement_filed': False, 'calls': ordinal, 'retries': 0})
    if result is not None:
        row = c.measurement(manifest_commitment(result['manifest']))
        save(out / 'measurement-after.json', row)
        print('Filed', row['manifest_hash'], result['value'], result['value_lo'], result['value_hi'], flush=True)
    save(out / 'proposal-after.json', c.proposal(spec['slug'], authenticated=True))
    save(out / 'suggestions-after.json', c.suggestions(proposal=spec['public_id']))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'run'])
    parser.add_argument('study', choices=['attempt-discharge', 'outcome-careful', 'outcome-compact',
                                        'outcome-majority-careful', 'outcome-majority-compact', 'outcome-specification',
                                        'postpone-careful', 'replace-careful', 'postpone-validity', 'replace-validity'])
    args = parser.parse_args()
    (prepare if args.action == 'prepare' else run)(ROOT / args.study)
