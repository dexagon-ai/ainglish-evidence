"""Execute the approved careful-English component after its actual prerequisites clear."""
import copy
import hashlib
import json
import subprocess
import sys
import urllib.request
from collections import Counter
from ainglish import panel
from local_colony_auth import ainglish_client, colony_client
from reader_campaign import ROOT, save, load, require_resources

OUT = ROOT / 'postpone-careful'
PRIOR = ROOT.parent / 'reader-and-web-followthrough-2026-09-08/postpone-careful-v2'
PID = 'a-ge8tz4ejhpknbghe'
SLUG = 'consider-now-matter-postpone-matter-never-use-procedural'
COST = '731894e988bbb6a473703d55ba259d137fe53ace009c7e792345edd2e036161a'
REVIEW = '6e99ebd9-60bf-48b0-bada-912cf25e2cb8'
ITEMS = 'd87694202eb5288cb4f3adb5fa4dc14fe018dfba59651ab58a9b047717a282f8'


def prerequisites():
    c = ainglish_client()
    suggestions = c.suggestions(proposal=PID)
    p = c.proposal(SLUG, authenticated=True)
    # Suggestions prioritise the existing small legacy original, whose opaque
    # remote source is not this cached reader population. The user separately
    # authorised this exact broader original; never attach replicates_hash or
    # represent a selected replication card as authorisation to change its source.
    assert any(x.get('metric') == 'comprehension_accuracy_delta' for x in suggestions['suggestions'])
    assert p['stage'] in ('seconded', 'measured')
    prior_lock = load(PRIOR / 'claim-lock.json')
    assert {k: hashlib.sha256(p[k.removesuffix('_sha256')].encode()).hexdigest()
            for k in prior_lock} == prior_lock
    cost = c.measurement(COST)
    assert cost['confirmed'] and cost['evidence_state'] == 'valid' and cost['value'] <= 0
    assert cost['manifest']['models'] == ['cl100k_base', 'o200k_base']
    assert len(cost['manifest']['test_set']) == 64
    co = colony_client()
    comments = co.get_all_comments(p['colony_thread_url'].rsplit('/', 1)[-1])
    review = next(x for x in comments if x['id'] == REVIEW)
    assert review['author']['username'] == 'saturnia' and ITEMS in review['body']
    assert 'accept the exact 192-target careful-English packet' in review['body']
    return c, p, cost, review


def prepare():
    c, p, cost, review = prerequisites()
    spec = copy.deepcopy(load(PRIOR / 'unbound-runspec.json'))
    assert hashlib.sha256(json.dumps(spec['items'], sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest() == ITEMS
    safe = load(ROOT / 'verifier-recovery-bare/runspec.json')
    selected = {'mistral-small3.2-24b-opaque-choice-q4_k_m', 'gemma3-12b-opaque-choice-q4_k_m'}
    spec['panel'] = [copy.deepcopy(x) for x in safe['panel'] if x['name'] in selected]
    assert len(spec['panel']) == 2
    spec['reader_qualifications'] = [copy.deepcopy(x) for x in safe['reader_qualifications'] if x['roster_id'].split('@')[0] in selected]
    assert len(spec['reader_qualifications']) == 2
    require_resources(spec['panel'])
    spec = panel.prepare_reader_instruments(spec)
    spec['attempt']['admissibility_gates'] = [
        x for x in spec['attempt']['admissibility_gates'] if 'Our isolated service is restricted to GPU 0' not in x]
    spec['attempt']['admissibility_gates'] += [
        'The shared existing Ollama endpoint uses the same already cached ctx4k models and unchanged generation settings, not the earlier stopped isolated endpoint. Its currently valid exact-setting qualification receipts must validate before mint.',
        'Run stateless requests serially, release only this study model between readers, start above 22 GiB Windows free and stop below 15 GiB. Do not download or substitute readers.',
        'The public semantic acceptance is comment ' + REVIEW + ' for digest ' + ITEMS + '; it excludes the separate validity and bare-table components.',
        'This is the user-approved broader original, not a replication of the small spark-zen-13-minimal original prioritised by discovery. No original is retired, hidden or declared superseded by this filing.',
    ]
    real = [x for x in spec['items'] if not x.get('calibration')]
    baseline = Counter(x['answer'] for x in real)
    save(OUT / 'unbound-runspec.json', spec)
    save(OUT / 'items.json', spec['items'])
    save(OUT / 'claim-lock.json', {k:p[k] for k in (
        'public_id', 'form', 'english_mapping', 'predicted_measurement', 'evidence_contract')})
    save(OUT / 'cost-confirmed.json', cost)
    save(OUT / 'semantic-review.json', review)
    save(OUT / 'execution-boundary.json', {
        'items_sha256': ITEMS, 'items_changed': False, 'target_calls_so_far': 0,
        'scope': 'Author-accepted 192-row careful-English component only. Not the bare-table hypothesis, validity block, robustness, or full claim completion.',
        'source_of_authority': 'User approved task 6 conditional full reader followthrough; current cost and explicit independent semantic review now pass.',
        'discovery_boundary': 'Current suggestion prioritises replication of small remote original 48eb9efde1b65dc3d0ecb7af5f5bf0ed6260659b0e323592bc2394d5b6b5cb37. This is a separately scoped new original, not an execution of that replication card.',
        'endpoint_change': 'Stopped isolated port 11435 replaced before any scientific call by shared localhost:11434 with currently qualified exact ctx4k artifacts/settings. No new model or scientific outcome exists for this packet.',
        'baseline': {'constant_complete_answer_accuracy': max(baseline.values()) / len(real),
                     'different_gold_vectors': len(baseline),
                     'limit': 'Only immediate-action bit varies in valid target directives. Neither-approval-nor-rejection and no guaranteed return are constant truths, not independent discriminating tasks.'},
        'limits': ['Authored template variants and speaker labels are not independent human or natural-use samples.',
                   'No inference that a cost-source correction for an unrelated original is still a prerequisite for this accepted study.']})
    print('PREPARED postpone: 192 targets, 48 calibration + 384 target calls; zero calls yet.', flush=True)


def bind():
    c, p, cost, review = prerequisites()
    spec = load(OUT / 'unbound-runspec.json')
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT.parent, text=True).strip()
    spec['items_url'] = f'https://raw.githubusercontent.com/dexagon-ai/ainglish-evidence/{commit}/{ROOT.name}/postpone-careful/items.json'
    with urllib.request.urlopen(spec['items_url'], timeout=30) as f:
        assert json.load(f) == spec['items']
    manifest = panel._planned_panel_manifest(spec)
    save(OUT / 'preflight.json', c.preflight_attempt(SLUG, manifest, **panel._attempt_settings(spec['attempt'], [panel.calibration_gate_statement(spec)])))
    save(OUT / 'runspec.json', spec)
    save(OUT / 'planned-manifest.json', manifest)
    print('BOUND postpone; no mint or inference yet.', flush=True)


if __name__ == '__main__':
    {'prepare': prepare, 'bind': bind}[sys.argv[1]]()
